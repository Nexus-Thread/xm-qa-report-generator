"""JSON file writer adapter for debug payload persistence."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

LOGGER = logging.getLogger(__name__)
_LABEL_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


class JsonFileDebugWriterAdapter:
    """Persist labeled debug payloads as JSON files."""

    def __init__(self, *, base_dir: Path) -> None:
        """Store target directory for debug payload files."""
        self._base_dir = base_dir

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Write one labeled JSON payload and return file path."""
        safe_label = self._sanitize_label(label)
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
        file_path = self._base_dir / f"{timestamp}_{safe_label}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        serialized_payload = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        file_path.write_text(f"{serialized_payload}\n", encoding="utf-8")
        LOGGER.debug(
            "Wrote debug JSON payload to file: %s",
            file_path,
            extra={
                "component": self.__class__.__name__,
                "debug_label": safe_label,
            },
        )
        return file_path

    def _sanitize_label(self, label: str) -> str:
        """Normalize label into a safe filename component."""
        sanitized = _LABEL_PATTERN.sub("_", label.strip()).strip("_").lower()
        return sanitized or "payload"
