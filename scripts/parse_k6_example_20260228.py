"""Parse k6 example reports and print manual validation summary."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_report_generator.domain.analytics import K6ParsedReport

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def _write_line(text: str) -> None:
    sys.stdout.write(f"{text}\n")


def _write_error(text: str) -> None:
    sys.stderr.write(f"{text}\n")


@dataclass(frozen=True)
class FileParseResult:
    """One file parse result for manual review."""

    file_name: str
    ok: bool
    scenario_names: tuple[str, ...]
    checks_ok: int
    checks_failed: int
    check_lines: tuple[str, ...]
    error: str | None


@dataclass(frozen=True)
class ServiceParseResult:
    """One service parse result for manual review."""

    service: str
    files_total: int
    files_ok: int
    scenario_total: int
    scenario_names: tuple[str, ...]
    file_results: tuple[FileParseResult, ...]


class ParsedReportParser(Protocol):
    """Protocol for parser adapter used by this script."""

    def parse(self, *, service: str, report_files: list[Path]) -> K6ParsedReport:
        """Parse report files for one service."""


def main() -> int:
    """Run manual parser validation across service fixture folders."""
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    from qa_report_generator.adapters.output.parsers import K6ParsedReportParser

    parser = argparse.ArgumentParser(description="Parse k6 fixtures and print service coverage summary")
    parser.add_argument(
        "--base-dir",
        default="k6_example/20260228",
        help="Base directory with one subdirectory per service",
    )
    parser.add_argument(
        "--service",
        action="append",
        default=[],
        help="Service folder name to validate (repeatable). Defaults to all services.",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    if not base_dir.exists() or not base_dir.is_dir():
        _write_error(f"ERROR: base directory does not exist or is not a directory: {base_dir}")
        return 2

    requested_services = tuple(args.service)
    results = _parse_services(
        base_dir,
        parser_class=K6ParsedReportParser,
        requested_services=requested_services,
    )
    return _print_summary(base_dir=base_dir, results=results)


def _parse_services(
    base_dir: Path,
    *,
    parser_class: type[ParsedReportParser],
    requested_services: tuple[str, ...],
) -> list[ServiceParseResult]:
    parser = parser_class()
    results: list[ServiceParseResult] = []
    requested_set = set(requested_services)

    for service_dir in sorted(path for path in base_dir.iterdir() if path.is_dir()):
        service = service_dir.name
        if requested_set and service not in requested_set:
            continue

        report_files = sorted(service_dir.glob("*.json"))
        file_results = [
            _parse_one_file(parser=parser, service=service, report_file=report_file)
            for report_file in report_files
        ]

        scenario_names: set[str] = set()
        scenario_total = 0
        files_ok = 0
        for file_result in file_results:
            if file_result.ok:
                files_ok += 1
                scenario_total += len(file_result.scenario_names)
                scenario_names.update(file_result.scenario_names)

        results.append(
            ServiceParseResult(
                service=service,
                files_total=len(report_files),
                files_ok=files_ok,
                scenario_total=scenario_total,
                scenario_names=tuple(sorted(scenario_names)),
                file_results=tuple(file_results),
            )
        )

    return results


def _parse_one_file(*, parser: ParsedReportParser, service: str, report_file: Path) -> FileParseResult:
    from qa_report_generator.domain.exceptions import ConfigurationError

    source = _load_json(report_file)
    if source is None:
        return FileParseResult(
            file_name=report_file.name,
            ok=False,
            scenario_names=(),
            checks_ok=0,
            checks_failed=1,
            check_lines=("MISMATCH invalid JSON",),
            error="Invalid JSON",
        )

    try:
        parsed = parser.parse(service=service, report_files=[report_file])
    except ConfigurationError as err:
        return FileParseResult(
            file_name=report_file.name,
            ok=False,
            scenario_names=(),
            checks_ok=0,
            checks_failed=1,
            check_lines=("MISMATCH parser rejected file",),
            error=str(err),
        )

    scenario_names = tuple(sorted(scenario.name for scenario in parsed.scenarios))
    check_lines, checks_ok, checks_failed = _compare_parsed_to_source(source=source, parsed=parsed, report_file=report_file)

    is_ok = checks_failed == 0
    return FileParseResult(
        file_name=report_file.name,
        ok=is_ok,
        scenario_names=scenario_names,
        checks_ok=checks_ok,
        checks_failed=checks_failed,
        check_lines=tuple(check_lines),
        error=None,
    )


def _load_json(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        return payload
    return None


def _compare_parsed_to_source(*, source: dict[str, object], parsed: K6ParsedReport, report_file: Path) -> tuple[list[str], int, int]:
    checks: list[tuple[str, bool]] = []

    raw_exec = source.get("execScenarios")
    raw_exec = raw_exec if isinstance(raw_exec, dict) else {}
    raw_thresholds = source.get("execThresholds")
    raw_thresholds = raw_thresholds if isinstance(raw_thresholds, dict) else {}
    raw_metrics = source.get("metrics")
    raw_metrics = raw_metrics if isinstance(raw_metrics, dict) else {}

    raw_duration = 0.0
    raw_state = source.get("state")
    if isinstance(raw_state, dict):
        duration_value = raw_state.get("testRunDurationMs")
        if isinstance(duration_value, (int, float)):
            raw_duration = float(duration_value)

    checks.append(("scenario count", len(parsed.scenarios) == len(raw_exec)))

    parsed_by_name = {scenario.name: scenario for scenario in parsed.scenarios}
    checks.append(("scenario names", set(parsed_by_name) == set(raw_exec)))

    for scenario_name, raw_config in raw_exec.items():
        if not isinstance(scenario_name, str):
            continue
        if not isinstance(raw_config, dict):
            checks.append((f"{scenario_name}: raw config shape", False))
            continue

        scenario = parsed_by_name.get(scenario_name)
        checks.append((f"{scenario_name}: parsed scenario exists", scenario is not None))
        if scenario is None:
            continue

        tags = raw_config.get("tags")
        tags = tags if isinstance(tags, dict) else {}
        raw_env = tags.get("env_name")
        raw_env_name = raw_env if isinstance(raw_env, str) and raw_env else None

        checks.extend(
            [
                (f"{scenario_name}: source_report_file", scenario.source_report_file == report_file.name),
                (f"{scenario_name}: env_name", scenario.env_name == raw_env_name),
                (f"{scenario_name}: executor", scenario.executor == raw_config.get("executor")),
                (f"{scenario_name}: rate", scenario.rate == float(raw_config.get("rate", 0.0))),
                (f"{scenario_name}: duration", scenario.duration == raw_config.get("duration")),
                (f"{scenario_name}: preAllocatedVUs", scenario.pre_allocated_vus == int(raw_config.get("preAllocatedVUs", 0))),
                (f"{scenario_name}: maxVUs", scenario.max_vus == int(raw_config.get("maxVUs", 0))),
                (f"{scenario_name}: testRunDurationMs", scenario.test_run_duration_ms == raw_duration),
                (
                    f"{scenario_name}: thresholds deep equality",
                    _normalize_json_like(scenario.thresholds) == _normalize_json_like(raw_thresholds),
                ),
                (
                    f"{scenario_name}: metrics deep equality",
                    _normalize_json_like(scenario.metrics) == _normalize_json_like(raw_metrics),
                ),
            ]
        )

    check_lines = [f"{'OK' if is_ok else 'MISMATCH'} {name}" for name, is_ok in checks]
    checks_ok = sum(1 for _, is_ok in checks if is_ok)
    checks_failed = sum(1 for _, is_ok in checks if not is_ok)
    return check_lines, checks_ok, checks_failed


def _normalize_json_like(value: object) -> object:
    if isinstance(value, dict):
        normalized_items = ((str(key), _normalize_json_like(item)) for key, item in value.items())
        return dict(sorted(normalized_items, key=lambda pair: pair[0]))
    if isinstance(value, list):
        return [_normalize_json_like(item) for item in value]
    return value


def _print_summary(*, base_dir: Path, results: list[ServiceParseResult]) -> int:
    _write_line(f"k6 parse coverage summary for: {base_dir}")
    _write_line("=" * 88)

    files_total = 0
    files_failed = 0
    services_failed = 0

    for result in results:
        service_failed = result.files_ok != result.files_total
        if service_failed:
            services_failed += 1

        files_total += result.files_total
        files_failed += result.files_total - result.files_ok

        status = "FAIL" if service_failed else "OK"
        scenario_names = ", ".join(result.scenario_names) if result.scenario_names else "-"
        _write_line(
            f"[{status}] service={result.service} "
            f"files={result.files_ok}/{result.files_total} "
            f"scenarios={result.scenario_total} "
            f"unique_scenarios=[{scenario_names}]"
        )

        for file_result in result.file_results:
            if file_result.ok:
                names = ", ".join(file_result.scenario_names) if file_result.scenario_names else "-"
                _write_line(
                    f"   - OK   {file_result.file_name} scenarios=[{names}] "
                    f"checks={file_result.checks_ok}/{file_result.checks_ok + file_result.checks_failed}"
                )
            else:
                _write_line(
                    f"   - FAIL {file_result.file_name} error={file_result.error} "
                    f"checks_failed={file_result.checks_failed}"
                )

            for check_line in file_result.check_lines:
                _write_line(f"      · {check_line}")

    _write_line("=" * 88)
    _write_line(f"Totals: services={len(results)} services_failed={services_failed} files={files_total} files_failed={files_failed}")

    if services_failed or files_failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
