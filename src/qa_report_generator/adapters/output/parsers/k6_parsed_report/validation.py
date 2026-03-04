"""Schema validation utilities for k6 parsed report input."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from qa_report_generator.domain.exceptions import ConfigurationError

from .raw_schema import K6RawSummary


def validate_report(source: dict[str, Any]) -> K6RawSummary:
    """Validate raw report payload against the internal schema."""
    try:
        return K6RawSummary.model_validate(source)
    except ValidationError as err:
        msg = "Invalid k6 report schema"
        raise ConfigurationError(msg, suggestion=str(err)) from err
