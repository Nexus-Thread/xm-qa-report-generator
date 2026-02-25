"""Pytest JSON report parser for extracting test metrics and failure details."""

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
from qa_report_generator.domain.models.common import Failure, RunMetrics, TestCaseResult, TestOutput
from qa_report_generator.domain.value_objects import Duration, TestIdentifier, TestStatus

logger = logging.getLogger(__name__)


class PytestJsonParser(ReportParser):
    """Adapter for parsing pytest-json-report JSON files."""

    def parse(self, filepath: Path) -> ParsedReport:
        """Parse pytest-json-report JSON file and extract test metrics.

        Args:
            filepath: Path to .pytest-report.json file

        Returns:
            ParsedReport with extracted metrics (k6_context is always None for pytest)

        Raises:
            ParseError: If file doesn't exist or JSON is malformed

        """
        logger.info("Starting parse of pytest JSON report: %s", filepath)

        # Log file size for debugging
        try:
            file_size = filepath.stat().st_size
            logger.debug("Report file size: %d bytes", file_size)
        except OSError:
            logger.debug("Unable to read report file size for %s", filepath)

        try:
            with filepath.open(encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            msg = f"Report file not found: {filepath}"
            logger.exception("Parse failed: %s", msg)
            raise ParseFileNotFoundError(
                msg,
                suggestion="Check the file path and ensure pytest-json-report plugin generated the report. "
                "Run pytest with --json-report flag to generate the JSON report.",
            ) from e
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in report file: {filepath} (line {e.lineno}, column {e.colno})"
            logger.exception("Parse failed: %s", msg)
            raise ParseInvalidJsonError(
                msg,
                suggestion=f"The JSON file is malformed at line {e.lineno}. Ensure pytest-json-report completed successfully and the file wasn't truncated.",
            ) from e
        except Exception as e:
            msg = f"Failed to read report file: {filepath} - {type(e).__name__}: {e}"
            logger.exception("Parse failed: %s", msg)
            raise ParseError(
                msg,
                suggestion="Check file permissions and ensure the file is not corrupted.",
            ) from e

        try:
            # Extract summary
            summary = data.get("summary", {})
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            skipped = summary.get("skipped", 0)
            errors = summary.get("error", 0)  # pytest-json-report uses 'error' (singular)

            logger.debug(
                "Extracted test summary: total=%d, passed=%d, failed=%d, skipped=%d, errors=%d",
                total,
                passed,
                failed,
                skipped,
                errors,
            )

            # Extract duration
            duration_seconds = data.get("duration")
            duration = Duration(seconds=duration_seconds) if duration_seconds is not None else None

            # Extract failures with full context
            tests_data = data.get("tests", [])
            failures = self._extract_failures_from_tests(tests_data)
            test_results = self._extract_test_results(tests_data)

            logger.info(
                "Parse completed: %d total tests, %d failures extracted",
                total,
                len(failures),
            )

            return ParsedReport(
                metrics=RunMetrics(
                    total=total,
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    errors=errors,
                    duration=duration,
                    failures=failures,
                    test_results=test_results,
                )
            )
        except Exception as e:
            msg = f"Failed to parse report data: {e}"
            logger.exception("Parse failed during data extraction: %s", msg)
            raise ParseInvalidFormatError(
                msg,
                suggestion="Ensure the JSON file matches pytest-json-report structure with 'summary' and 'tests'.",
            ) from e

    def _extract_failures_from_tests(self, tests: list[dict[str, Any]]) -> list[Failure]:
        """Extract failure details from test cases.

        Args:
            tests: List of test case dictionaries from pytest-json-report

        Returns:
            List of Failure objects with detailed information

        """
        failures: list[Failure] = []

        for test in tests:
            # Only process failed or error tests
            outcome = test.get("outcome")
            if outcome not in ["failed", "error"]:
                continue

            # Extract basic info
            nodeid = test.get("nodeid", "unknown")
            # Parse nodeid like "tests/test_file.py::TestClass::test_method"
            test_name = self._extract_test_name(nodeid)
            suite = self._extract_suite(nodeid)

            # Create test identifier
            identifier = TestIdentifier(name=test_name, suite=suite)

            # Extract duration
            duration_seconds = test.get("duration")
            duration = Duration(seconds=duration_seconds) if duration_seconds is not None else None

            # Extract failure/error info from call phase
            call_info = test.get("call", {})

            exc_type, exc_message = self._extract_exception_info(call_info)

            # Extract captured output
            output = self._extract_output(test)

            failures.append(
                Failure(
                    identifier=identifier,
                    message=exc_message or "Test failed",
                    type=exc_type,
                    duration=duration,
                    output=output,
                ),
            )

        return failures

    def _extract_test_name(self, nodeid: str) -> str:
        """Extract test name from pytest nodeid.

        Args:
            nodeid: Pytest node ID (e.g., "tests/test_file.py::TestClass::test_method")

        Returns:
            Test method/function name (the last component of the nodeid)

        """
        parts = nodeid.split("::")
        return parts[-1] if parts else nodeid

    def _extract_suite(self, nodeid: str) -> str:
        """Extract suite/module path from pytest nodeid.

        Args:
            nodeid: Pytest node ID (e.g., "tests/test_file.py::TestClass::test_method")

        Returns:
            Module path with optional class (e.g., "tests.test_file.TestClass")

        """
        parts = nodeid.split("::")
        if len(parts) >= 2:
            # Convert file path to module notation (remove .py extension)
            module_path = parts[0].replace("/", ".").replace(".py", "")
            if len(parts) == 3:
                # Include class name if present
                return f"{module_path}.{parts[1]}"
            return module_path
        return nodeid

    def _extract_exception_info(self, call_info: dict[str, Any]) -> tuple[str | None, str]:
        """Extract exception type and message from call info."""
        exc_type: str | None = None
        exc_message = ""

        longrepr = call_info.get("longrepr")
        if isinstance(longrepr, str):
            exc_message = longrepr
        elif isinstance(longrepr, dict):
            reprcrash = longrepr.get("reprcrash", {})
            exc_message = reprcrash.get("message", "")
            exc_type = reprcrash.get("path", "")

        if not exc_message:
            crash = call_info.get("crash")
            if isinstance(crash, dict):
                exc_message = crash.get("message", "")
                exc_type = crash.get("path", "")

        return exc_type, exc_message

    def _extract_output(self, test: dict[str, Any]) -> TestOutput | None:
        """Extract captured output from all test phases.

        Args:
            test: Test case dictionary from pytest-json-report

        Returns:
            TestOutput object if any output was captured, None otherwise

        """
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        log_lines: list[str] = []

        # Check all test phases: setup, call, teardown
        for phase in ("setup", "call", "teardown"):
            phase_data = test.get(phase, {})
            self._append_phase_output(stdout_lines, phase, phase_data.get("stdout"))
            self._append_phase_output(stderr_lines, phase, phase_data.get("stderr"))
            self._append_phase_output(log_lines, phase, phase_data.get("log"))

        # Only create TestOutput if we captured any output
        if not (stdout_lines or stderr_lines or log_lines):
            return None

        return TestOutput(
            stdout="\n".join(stdout_lines) if stdout_lines else None,
            stderr="\n".join(stderr_lines) if stderr_lines else None,
            log="\n".join(log_lines) if log_lines else None,
        )

    def _append_phase_output(self, lines: list[str], phase: str, content: str | None) -> None:
        if content:
            lines.append(f"[{phase}]\n{content}")

    def _extract_test_results(self, tests: list[dict[str, Any]]) -> list[TestCaseResult]:
        results: list[TestCaseResult] = []
        for test in tests:
            nodeid = test.get("nodeid", "unknown")
            test_name = self._extract_test_name(nodeid)
            suite = self._extract_suite(nodeid)
            identifier = TestIdentifier(name=test_name, suite=suite)
            outcome = test.get("outcome", "unknown")
            status = TestStatus(outcome) if outcome in TestStatus._value2member_map_ else TestStatus.ERROR
            duration_seconds = test.get("duration")
            duration = Duration(seconds=duration_seconds) if duration_seconds is not None else None
            results.append(
                TestCaseResult(
                    identifier=identifier,
                    status=status,
                    duration=duration,
                ),
            )
        return results
