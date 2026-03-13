"""JSON file writer adapter."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from os import PathLike, fspath
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from pathlib import Path

LOGGER = logging.getLogger(__name__)
_LABEL_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")
JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class JsonFileWriterAdapter:
    """Persist labeled JSON payloads as files."""

    def __init__(self, *, base_dir: Path) -> None:
        """Store target directory for JSON payload files."""
        self._base_dir = base_dir

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Write one labeled JSON payload and return file path."""
        safe_label = self._sanitize_label(label)
        file_path = self._build_file_path(safe_label=safe_label)
        normalized_payload = _normalize_json_value(payload)
        self._write_payload(file_path=file_path, payload=normalized_payload)
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

    def _build_file_path(self, *, safe_label: str) -> Path:
        """Build an output path for one labeled JSON payload."""
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
        return self._base_dir / f"{timestamp}_{safe_label}.json"

    @staticmethod
    def _write_payload(*, file_path: Path, payload: JsonValue) -> None:
        """Write one normalized JSON payload to disk."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, ensure_ascii=False, indent=2, sort_keys=True)
            file_handle.write("\n")


def _normalize_json_value(value: object) -> JsonValue:
    """Normalize common model objects into JSON-serializable values."""
    if value is None or isinstance(value, str | int | float | bool):
        normalized_value: JsonValue = value
    elif is_dataclass(value) and not isinstance(value, type):
        normalized_value = _normalize_json_value(asdict(value))
    else:
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            normalized_value = _normalize_json_value(model_dump(by_alias=True))
        elif isinstance(value, Mapping):
            normalized_value = {str(key): _normalize_json_value(item) for key, item in value.items()}
        elif isinstance(value, list | tuple):
            normalized_value = [_normalize_json_value(item) for item in value]
        elif isinstance(value, set | frozenset):
            normalized_items = [_normalize_json_value(item) for item in value]
            normalized_value = sorted(normalized_items, key=_json_sort_key)
        elif isinstance(value, PathLike):
            normalized_value = fspath(value)
        else:
            msg = f"Unsupported JSON payload type: {type(value).__name__}"
            raise TypeError(msg)

    return normalized_value


def _json_sort_key(value: JsonValue) -> str:
    """Build a deterministic JSON sort key for unordered collections."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
