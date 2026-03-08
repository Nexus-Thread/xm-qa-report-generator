"""JSON file loading utilities for the k6 parsed report parser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from qa_report_generator.domain.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path


def load_json_report(path: Path) -> dict[str, Any]:
    """Load and decode a k6 JSON report file."""
    try:
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as err:
        msg = f"Invalid k6 JSON report: {path}"
        raise ConfigurationError(msg, suggestion="Validate k6 artifact JSON format") from err
    except OSError as err:
        msg = f"Unable to read k6 JSON report: {path}"
        raise ConfigurationError(msg, suggestion="Ensure report file exists and is readable") from err

    if not isinstance(payload, dict):
        msg = f"Invalid k6 JSON report root object: {path}"
        raise ConfigurationError(msg, suggestion="Ensure k6 report JSON uses an object at the top level")

    return payload
