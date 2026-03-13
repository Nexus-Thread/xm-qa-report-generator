"""Parse k6 example reports and print manual validation summary."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from qa_report_generator_performance.domain.analytics import K6ParsedReport

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
LOGGER = logging.getLogger(__name__)


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
class ParseResultWithDumpEntry:
    """One file parse result with optional dump entry payload."""

    file_result: FileParseResult
    dump_entry: dict[str, Any] | None


@dataclass(frozen=True)
class ServiceParseResult:
    """One service parse result for manual review."""

    service: str
    files_total: int
    files_ok: int
    scenario_total: int
    scenario_names: tuple[str, ...]
    file_results: tuple[FileParseResult, ...]
    parsed_dump_file: str | None


class ParsedReportParser(Protocol):
    """Protocol for parser adapter used by this script."""

    def parse(self, *, service: str, report_files: list[Path]) -> K6ParsedReport:
        """Parse report files for one service."""


class DebugJsonWriter(Protocol):
    """Protocol for JSON debug dump writer used by this script."""

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Write one labeled JSON payload and return file path."""


def _build_arg_parser() -> argparse.ArgumentParser:
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
    parser.add_argument(
        "--dump-dir",
        default="out/parse_k6_example_20260228",
        help="Directory where parsed model JSON dumps are written",
    )
    return parser


def _load_parser_class() -> type[ParsedReportParser] | None:
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    try:
        from qa_report_generator_performance.adapters.output.parsers import K6ParsedReportParser
    except ImportError as err:
        _write_error(f"ERROR: unable to import parser adapter: {err}")
        _write_error("Hint: run from repository root or set PYTHONPATH=src")
        return None

    return K6ParsedReportParser


def _load_debug_writer(*, dump_dir: Path) -> DebugJsonWriter | None:
    try:
        from shared.adapters.output.persistence import JsonFileWriterAdapter
    except ImportError as err:
        _write_error(f"ERROR: unable to import JSON debug writer adapter: {err}")
        _write_error("Hint: run from repository root or set PYTHONPATH=src")
        return None

    return JsonFileWriterAdapter(base_dir=dump_dir)


def main() -> int:
    """Run manual parser validation across service fixture folders."""
    args = _build_arg_parser().parse_args()

    base_dir = Path(args.base_dir)
    if not base_dir.exists() or not base_dir.is_dir():
        _write_error(f"ERROR: base directory does not exist or is not a directory: {base_dir}")
        return 2

    dump_dir = Path(args.dump_dir)
    try:
        dump_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        _write_error(f"ERROR: cannot create dump directory {dump_dir}: {err}")
        return 2

    parser_class = _load_parser_class()
    debug_writer = _load_debug_writer(dump_dir=dump_dir)
    if parser_class is None or debug_writer is None:
        return 2

    requested_services = tuple(dict.fromkeys(args.service))
    service_dirs, missing_services = _resolve_service_dirs(base_dir=base_dir, requested_services=requested_services)
    if missing_services:
        _write_error(f"ERROR: unknown service(s): {', '.join(missing_services)}")
        available_services = ", ".join(_discover_service_names(base_dir)) or "-"
        _write_error(f"Available services: {available_services}")
        return 2

    if not service_dirs:
        _write_error(f"ERROR: no service directories found in {base_dir}")
        return 2

    results = _parse_services(
        service_dirs=service_dirs,
        parser_class=parser_class,
        dump_writer=debug_writer,
    )
    return _print_summary(base_dir=base_dir, results=results, dump_dir=dump_dir)


def _discover_service_names(base_dir: Path) -> tuple[str, ...]:
    return tuple(sorted(path.name for path in base_dir.iterdir() if path.is_dir()))


def _resolve_service_dirs(base_dir: Path, requested_services: tuple[str, ...]) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    available_dirs = tuple(sorted(path for path in base_dir.iterdir() if path.is_dir()))
    available_by_name = {path.name: path for path in available_dirs}

    if not requested_services:
        return available_dirs, ()

    selected_dirs: list[Path] = []
    missing_services: list[str] = []
    for service in requested_services:
        path = available_by_name.get(service)
        if path is None:
            missing_services.append(service)
            continue
        selected_dirs.append(path)

    return tuple(selected_dirs), tuple(missing_services)


def _parse_services(
    *,
    service_dirs: tuple[Path, ...],
    parser_class: type[ParsedReportParser],
    dump_writer: DebugJsonWriter,
) -> list[ServiceParseResult]:
    parser = parser_class()
    results: list[ServiceParseResult] = []

    for service_dir in service_dirs:
        service = service_dir.name

        report_files = sorted(service_dir.glob("*.json"))
        file_results: list[FileParseResult] = []
        dump_entries: list[dict[str, Any]] = []
        for report_file in report_files:
            parse_result = _parse_one_file(
                parser=parser,
                service=service,
                report_file=report_file,
            )
            file_results.append(parse_result.file_result)
            if parse_result.dump_entry is not None:
                dump_entries.append(parse_result.dump_entry)

        parsed_dump_file = _write_service_parsed_dump(
            dump_writer=dump_writer,
            service=service,
            dump_entries=dump_entries,
        )

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
                parsed_dump_file=parsed_dump_file,
            )
        )

    return results


def _parse_one_file(*, parser: ParsedReportParser, service: str, report_file: Path) -> ParseResultWithDumpEntry:
    from qa_report_generator_performance.application.exceptions import ConfigurationError

    try:
        source = _load_json(report_file)
    except OSError as err:
        LOGGER.exception("Failed reading report file", extra={"service": service, "file": report_file.name})
        return ParseResultWithDumpEntry(
            file_result=FileParseResult(
                file_name=report_file.name,
                ok=False,
                scenario_names=(),
                checks_ok=0,
                checks_failed=1,
                check_lines=("MISMATCH unable to read report file",),
                error=f"I/O error: {err}",
            ),
            dump_entry=None,
        )

    if source is None:
        return ParseResultWithDumpEntry(
            file_result=FileParseResult(
                file_name=report_file.name,
                ok=False,
                scenario_names=(),
                checks_ok=0,
                checks_failed=1,
                check_lines=("MISMATCH invalid JSON",),
                error="Invalid JSON",
            ),
            dump_entry=None,
        )

    try:
        parsed = parser.parse(service=service, report_files=[report_file])
    except ConfigurationError as err:
        return ParseResultWithDumpEntry(
            file_result=FileParseResult(
                file_name=report_file.name,
                ok=False,
                scenario_names=(),
                checks_ok=0,
                checks_failed=1,
                check_lines=("MISMATCH parser rejected file",),
                error=str(err),
            ),
            dump_entry=None,
        )
    except Exception as err:  # pragma: no cover - safety net for manual diagnostics
        LOGGER.exception("Unexpected parser failure", extra={"service": service, "file": report_file.name})
        return ParseResultWithDumpEntry(
            file_result=FileParseResult(
                file_name=report_file.name,
                ok=False,
                scenario_names=(),
                checks_ok=0,
                checks_failed=1,
                check_lines=("MISMATCH parser raised unexpected error",),
                error=f"Unexpected parser error: {err}",
            ),
            dump_entry=None,
        )

    scenario_names = tuple(sorted(scenario.name for scenario in parsed.scenarios))
    check_lines, checks_ok, checks_failed = _compare_parsed_to_source(source=source, parsed=parsed, report_file=report_file)

    is_ok = checks_failed == 0
    return ParseResultWithDumpEntry(
        file_result=FileParseResult(
            file_name=report_file.name,
            ok=is_ok,
            scenario_names=scenario_names,
            checks_ok=checks_ok,
            checks_failed=checks_failed,
            check_lines=tuple(check_lines),
            error=None,
        ),
        dump_entry={"report_file": report_file.name, "parsed": asdict(parsed)},
    )


def _write_service_parsed_dump(*, dump_writer: DebugJsonWriter, service: str, dump_entries: list[dict[str, Any]]) -> str | None:
    payload = {
        "service": service,
        "reports": dump_entries,
    }
    try:
        dump_path = dump_writer.write_json(label=f"{service}__parsed", payload=payload)
    except (OSError, TypeError, ValueError):
        LOGGER.exception(
            "Failed writing service parsed model dump",
            extra={"service": service},
        )
        return None
    return str(dump_path)


def _load_json(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        return payload
    return None


def _compare_parsed_to_source(*, source: dict[str, object], parsed: K6ParsedReport, report_file: Path) -> tuple[list[str], int, int]:
    from qa_report_generator_performance.domain.analytics.source_payload import extract_env_name, pick_test_run_duration_ms

    checks: list[tuple[str, bool]] = []

    raw_exec = _as_dict(source.get("execScenarios"))
    raw_thresholds = _as_dict(source.get("execThresholds"))
    raw_metrics = _as_dict(source.get("metrics"))

    raw_duration = 0.0
    raw_state = source.get("state")
    if isinstance(raw_state, dict):
        raw_duration = _as_float(raw_state.get("testRunDurationMs"))

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

        parsed_scenarios = _as_dict(scenario.source_payload.get("execScenarios"))
        parsed_config = _as_dict(parsed_scenarios.get(scenario_name))

        checks.extend(
            [
                (f"{scenario_name}: source_report_file", scenario.source_report_file == report_file.name),
                (
                    f"{scenario_name}: scenario payload preserves config",
                    _normalize_json_like(parsed_config) == _normalize_json_like(raw_config),
                ),
                (
                    f"{scenario_name}: env_name derivation",
                    extract_env_name(scenario_config=parsed_config) == extract_env_name(scenario_config=raw_config),
                ),
                (
                    f"{scenario_name}: testRunDurationMs derivation",
                    pick_test_run_duration_ms(source_payload=scenario.source_payload) == raw_duration,
                ),
                (
                    f"{scenario_name}: thresholds deep equality",
                    _normalize_json_like(_as_dict(scenario.source_payload.get("execThresholds"))) == _normalize_json_like(raw_thresholds),
                ),
                (
                    f"{scenario_name}: metrics deep equality",
                    _normalize_json_like(_as_dict(scenario.source_payload.get("metrics"))) == _normalize_json_like(raw_metrics),
                ),
            ]
        )

    check_lines = [f"{'OK' if is_ok else 'MISMATCH'} {name}" for name, is_ok in checks]
    checks_ok = sum(1 for _, is_ok in checks if is_ok)
    checks_failed = sum(1 for _, is_ok in checks if not is_ok)
    return check_lines, checks_ok, checks_failed


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _as_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _normalize_json_like(value: object) -> object:
    if isinstance(value, dict):
        normalized_items = ((str(key), _normalize_json_like(item)) for key, item in value.items())
        return dict(sorted(normalized_items, key=lambda pair: pair[0]))
    if isinstance(value, list):
        return [_normalize_json_like(item) for item in value]
    return value


def _print_summary(*, base_dir: Path, results: list[ServiceParseResult], dump_dir: Path) -> int:
    _write_line(f"k6 parse coverage summary for: {base_dir}")
    _write_line("=" * 88)

    files_total = 0
    files_failed = 0
    services_failed = 0
    dumps_written = 0

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
                    f"   - OK   {file_result.file_name} scenarios=[{names}] checks={file_result.checks_ok}/{file_result.checks_ok + file_result.checks_failed}"
                )
            else:
                _write_line(f"   - FAIL {file_result.file_name} error={file_result.error} checks_failed={file_result.checks_failed}")

            for check_line in file_result.check_lines:
                _write_line(f"      · {check_line}")

        if result.parsed_dump_file:
            dumps_written += 1
            _write_line(f"   · DUMP {result.parsed_dump_file}")

    _write_line("=" * 88)
    _write_line(f"Totals: services={len(results)} services_failed={services_failed} files={files_total} files_failed={files_failed}")
    _write_line(f"Parsed model dumps: {dumps_written} service file(s) in {dump_dir}")

    if services_failed or files_failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
