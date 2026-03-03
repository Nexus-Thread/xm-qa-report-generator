"""Parse k6 example reports and print manual validation summary."""

from __future__ import annotations

import argparse
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

    def parse(self, *, service: str, report_files: list[Path]) -> "K6ParsedReport":
        """Parse report files for one service"""


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
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    if not base_dir.exists() or not base_dir.is_dir():
        _write_error(f"ERROR: base directory does not exist or is not a directory: {base_dir}")
        return 2

    results = _parse_services(base_dir, parser_class=K6ParsedReportParser)
    return _print_summary(base_dir=base_dir, results=results)


def _parse_services(base_dir: Path, *, parser_class: type[ParsedReportParser]) -> list[ServiceParseResult]:
    parser = parser_class()
    results: list[ServiceParseResult] = []

    for service_dir in sorted(path for path in base_dir.iterdir() if path.is_dir()):
        service = service_dir.name
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

    try:
        parsed = parser.parse(service=service, report_files=[report_file])
    except ConfigurationError as err:
        return FileParseResult(
            file_name=report_file.name,
            ok=False,
            scenario_names=(),
            error=str(err),
        )

    scenario_names = tuple(sorted(scenario.name for scenario in parsed.scenarios))
    return FileParseResult(
        file_name=report_file.name,
        ok=True,
        scenario_names=scenario_names,
        error=None,
    )


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
                _write_line(f"   - OK   {file_result.file_name} scenarios=[{names}]")
            else:
                _write_line(f"   - FAIL {file_result.file_name} error={file_result.error}")

    _write_line("=" * 88)
    _write_line(f"Totals: services={len(results)} services_failed={services_failed} files={files_total} files_failed={files_failed}")

    if services_failed or files_failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
