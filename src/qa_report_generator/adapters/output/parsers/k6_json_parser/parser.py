"""K6 JSON summary report parser."""

import json
import logging
import re
from pathlib import Path
from typing import Any

from qa_report_generator.application.dtos.parsed_report import ParsedReport
from qa_report_generator.application.ports.output import ReportParser
from qa_report_generator.domain.exceptions import (
    ParseError,
    ParseFileNotFoundError,
    ParseInvalidFormatError,
    ParseInvalidJsonError,
)
from qa_report_generator.domain.models import Failure, RunMetrics, TestCaseResult
from qa_report_generator.domain.models.performance import (
    K6Check,
    K6LoadStage,
    K6ReportContext,
    K6ScenarioContext,
    K6ScenarioLoadModel,
    K6Threshold,
)
from qa_report_generator.domain.value_objects import Duration, TestIdentifier, TestStatus

LOGGER = logging.getLogger(__name__)

_CHECK_FAILURE_TYPE = "CheckFailure"
_THRESHOLD_VIOLATION_TYPE = "ThresholdViolation"
_THRESHOLDS_SUITE_PREFIX = "thresholds"
_ROOT_SUITE = "root"
_SCENARIO_FALLBACK = "default"
_TEST_NAME_PATTERN = re.compile(r"test_name:([^,}]+)")


class K6JsonParser(ReportParser):
    """Adapter for parsing k6 summary JSON export files (`--summary-export`)."""

    def parse(self, filepath: Path) -> ParsedReport:
        """Parse k6 summary JSON file and extract test metrics.

        Args:
            filepath: Path to k6 summary JSON file produced by --summary-export

        Returns:
            ParsedReport containing RunMetrics and K6ReportContext breakdown

        Raises:
            ParseError: If file does not exist or JSON is malformed

        """
        LOGGER.info("Starting parse of k6 summary report: %s", filepath)

        try:
            file_size = filepath.stat().st_size
            LOGGER.debug("Report file size: %d bytes", file_size)
        except OSError:
            LOGGER.debug("Unable to read report file size for %s", filepath)

        try:
            with filepath.open(encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError as exc:
            msg = f"Report file not found: {filepath}"
            LOGGER.exception("Parse failed: %s", msg)
            raise ParseFileNotFoundError(
                msg,
                suggestion="Check the file path and ensure k6 was run with --summary-export to generate the JSON.",
            ) from exc
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSON in report file: {filepath} (line {exc.lineno}, column {exc.colno})"
            LOGGER.exception("Parse failed: %s", msg)
            raise ParseInvalidJsonError(
                msg,
                suggestion=f"The JSON file is malformed at line {exc.lineno}. Ensure k6 completed successfully.",
            ) from exc
        except Exception as exc:
            msg = f"Failed to read report file: {filepath} - {type(exc).__name__}: {exc}"
            LOGGER.exception("Parse failed: %s", msg)
            raise ParseError(
                msg,
                suggestion="Check file permissions and ensure the file is not corrupted.",
            ) from exc

        try:
            metrics, k6_context = self._build_metrics(data)
        except Exception as exc:
            msg = f"Failed to parse k6 report data: {exc}"
            LOGGER.exception("Parse failed during data extraction: %s", msg)
            raise ParseInvalidFormatError(
                msg,
                suggestion="Ensure the JSON file matches k6 --summary-export format with 'metrics' and 'root_group'.",
            ) from exc

        return ParsedReport(metrics=metrics, k6_context=k6_context)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_metrics(self, data: dict[str, Any]) -> tuple[RunMetrics, K6ReportContext]:
        """Build RunMetrics and K6ReportContext from parsed k6 summary data."""
        metrics_raw: dict[str, Any] = data.get("metrics", {})
        root_group: dict[str, Any] = data.get("root_group", {})
        primary_scenario = self._extract_primary_scenario(data)

        checks = self._collect_checks(root_group, parent_group=_ROOT_SUITE, scenario=primary_scenario)
        thresholds = self._collect_thresholds(metrics_raw, fallback_scenario=primary_scenario)

        test_results = self._build_test_results(checks, thresholds)
        failures = self._build_failures(checks, thresholds)
        duration = self._extract_duration(data)

        passing_checks = sum(1 for check in checks if not check.is_failed)
        failing_checks = sum(1 for check in checks if check.is_failed)
        passing_thresholds = sum(1 for t in thresholds if t.ok)
        failing_thresholds = sum(1 for t in thresholds if t.is_violated)

        total = len(checks) + len(thresholds)
        passed = passing_checks + passing_thresholds
        failed = failing_checks + failing_thresholds

        LOGGER.info(
            "Parse completed: %d checks (%d passed, %d failed), %d thresholds (%d passed, %d violated)",
            len(checks),
            passing_checks,
            failing_checks,
            len(thresholds),
            passing_thresholds,
            failing_thresholds,
        )

        by_scenario = self._build_scenario_context(checks, thresholds)
        scenario_load_models = self._build_scenario_load_models(data)

        k6_context = K6ReportContext(
            by_scenario=by_scenario,
            scenario_load_models=scenario_load_models,
        )

        run_metrics = RunMetrics(
            total=total,
            passed=passed,
            failed=failed,
            skipped=0,
            errors=0,
            duration=duration,
            failures=failures,
            test_results=test_results,
        )

        return run_metrics, k6_context

    def _collect_checks(
        self,
        group: dict[str, Any],
        parent_group: str,
        scenario: str,
    ) -> list[K6Check]:
        """Recursively collect all checks from a k6 group tree.

        Args:
            group: k6 group dict containing 'checks' and 'groups'
            parent_group: Dot-joined group path from ancestor groups
            scenario: Scenario name used to group k6 checks

        Returns:
            List of K6Check objects

        """
        group_name = group.get("name", "")
        group_path = (f"{parent_group}.{group_name}" if parent_group != _ROOT_SUITE else group_name) if group_name else parent_group

        result: list[K6Check] = []
        for check_data in group.get("checks", []):
            check = K6Check(
                name=check_data.get("name", "unknown check"),
                scenario=scenario,
                group_path=group_path,
                passes=check_data.get("passes", 0),
                fails=check_data.get("fails", 0),
            )
            result.append(check)

        for subgroup in group.get("groups", []):
            result.extend(self._collect_checks(subgroup, parent_group=group_path, scenario=scenario))

        return result

    def _collect_thresholds(self, metrics: dict[str, Any], fallback_scenario: str) -> list[K6Threshold]:
        """Extract threshold entries from the metrics section.

        Args:
            metrics: k6 metrics dict
            fallback_scenario: Fallback scenario when metric key has no test_name tag

        Returns:
            List of K6Threshold objects

        """
        thresholds: list[K6Threshold] = []
        for metric_name, metric_data in metrics.items():
            for expression, result in metric_data.get("thresholds", {}).items():
                threshold = K6Threshold(
                    scenario=self._scenario_from_metric_name(metric_name) or fallback_scenario,
                    metric_name=metric_name,
                    expression=expression,
                    ok=bool(result.get("ok", False)),
                )
                thresholds.append(threshold)
        return thresholds

    def _build_test_results(
        self,
        checks: list[K6Check],
        thresholds: list[K6Threshold],
    ) -> list[TestCaseResult]:
        """Build TestCaseResult list from checks and thresholds."""
        results: list[TestCaseResult] = []

        for check in checks:
            status = TestStatus.PASSED if not check.is_failed else TestStatus.FAILED
            results.append(
                TestCaseResult(
                    identifier=TestIdentifier(name=check.name, suite=check.group_path),
                    status=status,
                    duration=None,
                )
            )

        for threshold in thresholds:
            suite = threshold.scenario
            status = TestStatus.PASSED if threshold.ok else TestStatus.FAILED
            results.append(
                TestCaseResult(
                    identifier=TestIdentifier(name=threshold.expression, suite=suite),
                    status=status,
                    duration=None,
                )
            )

        return results

    def _build_failures(
        self,
        checks: list[K6Check],
        thresholds: list[K6Threshold],
    ) -> list[Failure]:
        """Build Failure list from failed checks and violated thresholds."""
        failures: list[Failure] = []

        for check in checks:
            if not check.is_failed:
                continue
            message = f"Check failed: {check.fails}/{check.total_iterations} iterations"
            failures.append(
                Failure(
                    identifier=TestIdentifier(name=check.name, suite=check.group_path),
                    message=message,
                    type=_CHECK_FAILURE_TYPE,
                )
            )

        for threshold in thresholds:
            if not threshold.is_violated:
                continue
            suite = threshold.scenario
            message = f"Threshold violated: {threshold.metric_name} {threshold.expression}"
            failures.append(
                Failure(
                    identifier=TestIdentifier(name=threshold.expression, suite=suite),
                    message=message,
                    type=_THRESHOLD_VIOLATION_TYPE,
                )
            )

        return failures

    def _extract_duration(self, data: dict[str, Any]) -> Duration | None:
        """Extract test run duration from k6 state or metrics.

        Args:
            data: Top-level k6 summary dict

        Returns:
            Duration if extractable, None otherwise

        """
        state = data.get("state", {})

        duration_ms = state.get("testRunDurationMs")
        if duration_ms is not None:
            return Duration(seconds=float(duration_ms) / 1000.0)

        total_duration = state.get("totalDuration")
        if total_duration is not None:
            return Duration(seconds=float(total_duration))

        # Fall back to iteration_duration avg * count from metrics
        metrics = data.get("metrics", {})
        iter_duration_values = metrics.get("iteration_duration", {}).get("values", {})
        iterations_values = metrics.get("iterations", {}).get("values", {})
        avg_ms = iter_duration_values.get("avg")
        count = iterations_values.get("count")
        if avg_ms is not None and count:
            return Duration(seconds=float(avg_ms) * float(count) / 1000.0)

        return None

    def _extract_primary_scenario(self, data: dict[str, Any]) -> str:
        """Extract primary scenario from execScenarios/test_name tags."""
        exec_scenarios = data.get("execScenarios")
        if not isinstance(exec_scenarios, dict) or not exec_scenarios:
            return _SCENARIO_FALLBACK

        scenario_name, scenario_config = next(iter(exec_scenarios.items()))
        if isinstance(scenario_name, str) and isinstance(scenario_config, dict):
            return self._resolve_scenario_name(scenario_name, scenario_config)
        return _SCENARIO_FALLBACK

    def _resolve_scenario_name(self, scenario_name: str, scenario_config: dict[str, Any]) -> str:
        """Resolve scenario display name using tags.test_name when present."""
        tags = scenario_config.get("tags")
        if isinstance(tags, dict):
            test_name = tags.get("test_name")
            if isinstance(test_name, str) and test_name.strip():
                return test_name.strip()

        normalized_scenario_name = scenario_name.strip()
        return normalized_scenario_name or _SCENARIO_FALLBACK

    def _scenario_from_metric_name(self, metric_name: str) -> str | None:
        """Extract scenario from metric label string."""
        match = _TEST_NAME_PATTERN.search(metric_name)
        if not match:
            return None
        scenario = match.group(1).strip()
        return scenario or None

    def _build_scenario_context(
        self,
        checks: list[K6Check],
        thresholds: list[K6Threshold],
    ) -> dict[str, K6ScenarioContext]:
        """Build per-scenario check and threshold totals."""
        scenarios = sorted({check.scenario for check in checks} | {threshold.scenario for threshold in thresholds})

        context: dict[str, K6ScenarioContext] = {}
        for scenario in scenarios:
            scenario_checks = [check for check in checks if check.scenario == scenario]
            scenario_thresholds = [threshold for threshold in thresholds if threshold.scenario == scenario]

            checks_passed = sum(1 for check in scenario_checks if not check.is_failed)
            checks_failed = sum(1 for check in scenario_checks if check.is_failed)
            thresholds_passed = sum(1 for threshold in scenario_thresholds if threshold.ok)
            thresholds_failed = sum(1 for threshold in scenario_thresholds if threshold.is_violated)

            context[scenario] = K6ScenarioContext(
                checks_total=len(scenario_checks),
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                thresholds_total=len(scenario_thresholds),
                thresholds_passed=thresholds_passed,
                thresholds_failed=thresholds_failed,
            )

        return context

    def _build_scenario_load_models(self, data: dict[str, Any]) -> dict[str, K6ScenarioLoadModel]:
        """Extract per-scenario load model information from execScenarios."""
        exec_scenarios = data.get("execScenarios")
        if not isinstance(exec_scenarios, dict):
            return {}

        models: dict[str, K6ScenarioLoadModel] = {}
        for scenario_name, scenario_config in exec_scenarios.items():
            if not isinstance(scenario_name, str) or not isinstance(scenario_config, dict):
                continue
            resolved_scenario_name = self._resolve_scenario_name(scenario_name, scenario_config)
            models[resolved_scenario_name] = self._parse_scenario_load_model(scenario_config)

        return models

    def _parse_scenario_load_model(self, scenario_config: dict[str, Any]) -> K6ScenarioLoadModel:
        """Parse normalized load-model configuration for one scenario."""
        executor = scenario_config.get("executor")
        if not isinstance(executor, str) or not executor.strip():
            executor = "unknown"

        return K6ScenarioLoadModel(
            executor=executor,
            rate=self._to_non_negative_int(scenario_config.get("rate")),
            time_unit=self._to_non_empty_string(scenario_config.get("timeUnit")),
            duration=self._to_non_empty_string(scenario_config.get("duration")),
            start_vus=self._to_non_negative_int(scenario_config.get("startVUs")),
            pre_allocated_vus=self._to_non_negative_int(scenario_config.get("preAllocatedVUs")),
            max_vus=self._to_non_negative_int(scenario_config.get("maxVUs")),
            stages=self._parse_load_stages(scenario_config.get("stages")),
        )

    def _parse_load_stages(self, raw_stages: Any) -> list[K6LoadStage]:
        """Parse and normalize k6 stage definitions."""
        if not isinstance(raw_stages, list):
            return []

        parsed_stages: list[K6LoadStage] = []
        for raw_stage in raw_stages:
            if not isinstance(raw_stage, dict):
                continue

            duration = self._to_non_empty_string(raw_stage.get("duration"))
            target = self._to_non_negative_int(raw_stage.get("target"))
            if duration is None or target is None:
                continue

            parsed_stages.append(K6LoadStage(duration=duration, target=target))

        return parsed_stages

    def _to_non_empty_string(self, value: Any) -> str | None:
        """Normalize string-like values to non-empty strings."""
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _to_non_negative_int(self, value: Any) -> int | None:
        """Normalize numeric-like values to non-negative integers."""
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None
