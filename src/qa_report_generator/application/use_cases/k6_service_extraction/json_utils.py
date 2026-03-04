"""JSON helpers for k6 service extraction use case."""

from __future__ import annotations

import json
from typing import Any


def to_canonical_json(payload: dict[str, Any]) -> str:
    """Serialize payload to deterministic compact JSON."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
