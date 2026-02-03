"""Filesystem-backed cache for parsed report facts."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from qa_report_generator.application.ports.output import ReportCache
from qa_report_generator.domain.exceptions import PersistenceError
from qa_report_generator.domain.models import EnvironmentMeta, RunMetrics

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pathlib import Path


class FileReportCache(ReportCache):
    """Cache parsed report facts to disk for regeneration workflows."""

    def __init__(self, cache_dir: Path) -> None:
        """Initialize the cache directory."""
        self._cache_dir = cache_dir

    def load_cached_facts(
        self,
        report_path: Path,
    ) -> tuple[RunMetrics, EnvironmentMeta, list[str]] | None:
        """Load cached facts for a report path."""
        cache_path = self._cache_path(report_path)
        if not cache_path.exists():
            logger.info("Cache miss for report: %s", report_path)
            return None

        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            metrics = RunMetrics.model_validate(payload["metrics"])
            environment = EnvironmentMeta.model_validate(payload["environment"])
            input_files = list(payload.get("input_files", []))
        except Exception as exc:
            msg = f"Failed to load cached facts from {cache_path}: {exc}"
            logger.exception("Cache load failed: %s", msg)
            raise PersistenceError(msg) from exc
        else:
            logger.info("Cache hit for report: %s", report_path)
            return metrics, environment, input_files

    def save_cached_facts(
        self,
        report_path: Path,
        metrics: RunMetrics,
        environment: EnvironmentMeta,
        input_files: list[str],
    ) -> None:
        """Persist parsed facts for later regeneration."""
        cache_path = self._cache_path(report_path)
        payload = {
            "metrics": metrics.model_dump(),
            "environment": environment.model_dump(),
            "input_files": input_files,
        }

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            logger.info("Cached facts written: %s", cache_path)
        except Exception as exc:
            msg = f"Failed to save cached facts to {cache_path}: {exc}"
            logger.exception("Cache save failed: %s", msg)
            raise PersistenceError(msg) from exc

    def _cache_path(self, report_path: Path) -> Path:
        """Generate cache file path with path traversal protection.

        Args:
            report_path: Original report file path

        Returns:
            Safe cache file path within cache directory

        Raises:
            PersistenceError: If path traversal is detected

        """
        sanitized_name = report_path.resolve().as_posix().replace("/", "_")
        cache_path = self._cache_dir / f"{sanitized_name}.json"

        # Validate cache path stays within cache directory (prevent traversal)
        try:
            cache_path.resolve().relative_to(self._cache_dir.resolve())
        except ValueError as exc:
            msg = f"Cache path traversal detected: {cache_path}"
            logger.error("Security: %s", msg)  # noqa: TRY400
            raise PersistenceError(
                msg,
                suggestion="Report path may contain malicious components. Use trusted input only.",
            ) from exc

        return cache_path
