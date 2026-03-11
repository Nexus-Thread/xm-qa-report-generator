"""JSON file writer adapter."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeAlias

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
        file_path.parent.mkdir(parents=True, exist_ok=True)

        serialized_payload = self._serialize_payload(payload)
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

    def _build_file_path(self, *, safe_label: str) -> Path:
        """Build an output path for one labeled JSON payload."""
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
        return self._base_dir / f"{timestamp}_{safe_label}.json"

    @staticmethod
    def _serialize_payload(payload: Any) -> str:
        """Serialize payload into formatted JSON text."""
        normalized_payload = _to_json_compatible(payload)
        return json.dumps(normalized_payload, ensure_ascii=False, indent=2, sort_keys=True)


def _to_json_compatible(value: Any) -> JsonValue:
    """Normalize common model objects into JSON-serializable values."""
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    else:
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            value = model_dump(by_alias=True)

    if isinstance(value, Mapping):
        return _normalize_mapping(value)

    if isinstance(value, list | tuple):
        return _normalize_sequence(value)

    if isinstance(value, set | frozenset):
        return _normalize_unordered_collection(value)

    if isinstance(value, Path):
        return str(value)

    msg = f"Unsupported JSON payload type: {type(value).__name__}"
    raise TypeError(msg)


def _normalize_mapping(value: Mapping[Any, Any]) -> dict[str, JsonValue]:
    """Normalize a mapping into JSON-compatible key/value pairs."""
    return {str(key): _to_json_compatible(item) for key, item in value.items()}


def _normalize_sequence(value: list[Any] | tuple[Any, ...]) -> list[JsonValue]:
    """Normalize an ordered collection into JSON-compatible items."""
    return [_to_json_compatible(item) for item in value]


def _normalize_unordered_collection(value: set[Any] | frozenset[Any]) -> list[JsonValue]:
    """Normalize an unordered collection into a stable JSON array."""
    normalized_items = [_to_json_compatible(item) for item in value]
    return sorted(normalized_items, key=_json_sort_key)


def _json_sort_key(value: JsonValue) -> str:
    """Build a deterministic JSON sort key for unordered collections."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
