"""Unit tests for the JSON file writer adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from pydantic import BaseModel

from qa_report_generator.adapters.output.persistence import JsonFileWriterAdapter

if TYPE_CHECKING:
    from pathlib import Path


def test_write_json_persists_payload_with_label_and_returns_path(tmp_path: Path) -> None:
    """Adapter writes payload to JSON file and returns created file path."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    written_path = adapter.write_json(label="Request Payload", payload={"ok": True, "num": 7})

    assert written_path.exists()
    assert written_path.parent == tmp_path
    assert written_path.name.endswith("_request_payload.json")
    stored_payload = json.loads(written_path.read_text(encoding="utf-8"))
    assert stored_payload == {"num": 7, "ok": True}


def test_write_json_uses_payload_label_when_label_is_blank(tmp_path: Path) -> None:
    """Adapter falls back to payload filename label when provided label is blank."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    written_path = adapter.write_json(label="   ", payload={"ok": True})

    assert written_path.name.endswith("_payload.json")


def test_write_json_sanitizes_label_into_safe_filename_component(tmp_path: Path) -> None:
    """Adapter normalizes labels into stable filename-safe suffixes."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    written_path = adapter.write_json(label="  Request / Payload v2!  ", payload={"ok": True})

    assert written_path.name.endswith("_request_payload_v2.json")


@dataclass(frozen=True)
class _ChildPayload:
    """Nested payload used to verify dataclass serialization."""

    value: int


@dataclass(frozen=True)
class _ParentPayload:
    """Top-level payload used to verify dataclass serialization."""

    name: str
    child: _ChildPayload


def test_write_json_serializes_dataclass_payloads(tmp_path: Path) -> None:
    """Adapter serializes dataclass payloads into JSON objects."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    written_path = adapter.write_json(
        label="model snapshot",
        payload=[_ParentPayload(name="run-1", child=_ChildPayload(value=7))],
    )

    stored_payload = json.loads(written_path.read_text(encoding="utf-8"))

    assert stored_payload == [{"child": {"value": 7}, "name": "run-1"}]


class _AliasedPayload(BaseModel):
    """Pydantic payload used to verify model_dump serialization."""

    report_file: str


def test_write_json_serializes_pydantic_payloads(tmp_path: Path) -> None:
    """Adapter serializes Pydantic payloads into JSON objects."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    written_path = adapter.write_json(
        label="pydantic snapshot",
        payload=_AliasedPayload(report_file="run-1.json"),
    )

    stored_payload = json.loads(written_path.read_text(encoding="utf-8"))

    assert stored_payload == {"report_file": "run-1.json"}


def test_write_json_serializes_pathlike_values(tmp_path: Path) -> None:
    """Adapter serializes path-like values as filesystem strings."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    written_path = adapter.write_json(
        label="paths",
        payload={"report_path": tmp_path / "nested" / "report.json"},
    )

    stored_payload = json.loads(written_path.read_text(encoding="utf-8"))

    assert stored_payload == {"report_path": str(tmp_path / "nested" / "report.json")}


def test_write_json_creates_missing_output_directories(tmp_path: Path) -> None:
    """Adapter creates missing parent directories before writing JSON output."""
    base_dir = tmp_path / "debug" / "json"
    adapter = JsonFileWriterAdapter(base_dir=base_dir)

    written_path = adapter.write_json(label="snapshot", payload={"ok": True})

    assert base_dir.is_dir()
    assert written_path.parent == base_dir


def test_write_json_rejects_unsupported_payload_types(tmp_path: Path) -> None:
    """Adapter raises a clear error for unsupported payload values."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    with pytest.raises(TypeError, match="Unsupported JSON payload type: object"):
        adapter.write_json(label="invalid", payload={"value": object()})


def test_write_json_serializes_sets_deterministically(tmp_path: Path) -> None:
    """Adapter writes unordered collections in a stable JSON order."""
    adapter = JsonFileWriterAdapter(base_dir=tmp_path)

    written_path = adapter.write_json(label="set payload", payload={"values": {3, 1, 2}})

    stored_payload = json.loads(written_path.read_text(encoding="utf-8"))

    assert stored_payload == {"values": [1, 2, 3]}
