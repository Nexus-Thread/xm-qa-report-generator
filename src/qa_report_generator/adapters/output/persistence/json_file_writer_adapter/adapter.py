"""JSON file writer adapter."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

LOGGER = logging.getLogger(__name__)
_LABEL_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


class JsonFileWriterAdapter:
    """Persist labeled JSON payloads as files."""

    def __init__(self, *, base_dir: Path) -> None:
        """Store target directory for JSON payload files."""
        self._base_dir = base_dir

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Write one labeled JSON payload and return file path."""
        safe_label = self._sanitize_label(label)
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
        file_path = self._base_dir / f"{timestamp}_{safe_label}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        normalized_payload = _to_json_compatible(payload)
        serialized_payload = json.dumps(normalized_payload, ensure_ascii=False, indent=2, sort_keys=True)
        file_path.write_text(f"{serialized_payload}\n", encoding="utf-8")
        LOGGER.debug(
            "Wrote JSON payload to file: %s",
            file_path,
            extra={
                "component": self.__class__.__name__,
                "payload_label": safe_label,
            },
        )
        return file_path

    @staticmethod
    def _sanitize_label(label: str) -> str:
        """Normalize label into a safe filename component."""
        sanitized = _LABEL_PATTERN.sub("_", label.strip()).strip("_").lower()
        return sanitized or "payload"


def _to_json_compatible(value: Any) -> Any:
    """Normalize common model objects into JSON-serializable values."""
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if is_dataclass(value) and not isinstance(value, type):
        return _to_json_compatible(asdict(value))

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _to_json_compatible(model_dump(by_alias=True))

    if isinstance(value, dict):
        return {str(key): _to_json_compatible(item) for key, item in value.items()}

    if isinstance(value, list | tuple | set | frozenset):
        return [_to_json_compatible(item) for item in value]

    path_str = getattr(value, "as_posix", None)
    if callable(path_str):
        value = path_str()

    return value
