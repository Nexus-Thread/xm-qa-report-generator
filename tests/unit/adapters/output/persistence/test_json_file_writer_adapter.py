"""Unit tests for the JSON file writer adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

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
