"""Logging helpers for the structured LLM adapter."""

from __future__ import annotations

import json
from typing import Any


def build_json_payload_log_extra(*, payload: Any) -> dict[str, object]:
    """Return metadata-only logging fields for a JSON-serializable payload."""
    serialized_payload = json.dumps(payload, ensure_ascii=False, default=str)
    log_extra: dict[str, object] = {
        "payload_length": len(serialized_payload),
        "payload_kind": type(payload).__name__,
        "payload_preview_omitted": True,
    }
    if isinstance(payload, dict):
        log_extra["payload_keys"] = sorted(str(key) for key in payload)
    return log_extra


def build_text_payload_log_extra(*, content: str) -> dict[str, object]:
    """Return metadata-only logging fields for a text payload."""
    return {
        "payload_length": len(content),
        "payload_kind": "text",
        "payload_preview_omitted": True,
    }
