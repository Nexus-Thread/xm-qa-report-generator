"""K6 JSON summary report parser."""

import json
import logging
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
from qa_report_generator.domain.models.k6.context import K6ReportContext
from qa_report_generator.domain.models.k6.models import K6Check, K6Threshold
from qa_report_generator.domain.value_objects import Duration, TestIdentifier, TestStatus

LOGGER = logging.getLogger(__name__)

_CHECK_FAILURE_TYPE = "CheckFailure"
_THRESHOLD_VIOLATION_TYPE = "ThresholdViolation"
_THRESHOLDS_SUITE_PREFIX = "thresholds"
_ROOT_SUITE = "root"


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

        checks = self._collect_checks(root_group, parent_suite=_ROOT_SUITE)
        thresholds = self._collect_thresholds(metrics_raw)

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

        k6_context = K6ReportContext(
            checks_total=len(checks),
            checks_passed=passing_checks,
            checks_failed=failing_checks,
            thresholds_total=len(thresholds),
            thresholds_passed=passing_thresholds,
            thresholds_failed=failing_thresholds,
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
        parent_suite: str,
    ) -> list[K6Check]:
        """Recursively collect all checks from a k6 group tree.

        Args:
            group: k6 group dict containing 'checks' and 'groups'
            parent_suite: Dot-joined suite path from ancestor groups

        Returns:
            List of K6Check objects

        """
        group_name = group.get("name", "")
        suite = (f"{parent_suite}.{group_name}" if parent_suite != _ROOT_SUITE else group_name) if group_name else parent_suite

        result: list[K6Check] = []
        for check_data in group.get("checks", []):
            check = K6Check(
                name=check_data.get("name", "unknown check"),
                suite=suite,
                passes=check_data.get("passes", 0),
                fails=check_data.get("fails", 0),
            )
            result.append(check)

        for subgroup in group.get("groups", []):
            result.extend(self._collect_checks(subgroup, parent_suite=suite))

        return result

    def _collect_thresholds(self, metrics: dict[str, Any]) -> list[K6Threshold]:
        """Extract threshold entries from the metrics section.

        Args:
            metrics: k6 metrics dict

        Returns:
            List of K6Threshold objects

        """
        thresholds: list[K6Threshold] = []
        for metric_name, metric_data in metrics.items():
            for expression, result in metric_data.get("thresholds", {}).items():
                threshold = K6Threshold(
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
                    identifier=TestIdentifier(name=check.name, suite=check.suite),
                    status=status,
                    duration=None,
                )
            )

        for threshold in thresholds:
            suite = f"{_THRESHOLDS_SUITE_PREFIX}/{threshold.metric_name}"
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
                    identifier=TestIdentifier(name=check.name, suite=check.suite),
                    message=message,
                    type=_CHECK_FAILURE_TYPE,
                )
            )

        for threshold in thresholds:
            if not threshold.is_violated:
                continue
            suite = f"{_THRESHOLDS_SUITE_PREFIX}/{threshold.metric_name}"
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
