"""Schema validation helpers for k6 service extraction use case."""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from qa_report_generator.application.exceptions import ExtractionVerificationError


def validate_with_schema(schema_type: type[BaseModel], payload: dict[str, object]) -> BaseModel:
    """Validate extracted payload with service schema."""
    try:
        return schema_type.model_validate(payload)
    except ValidationError as err:
        msg = "Extracted payload failed schema validation"
        raise ExtractionVerificationError(msg, suggestion=str(err)) from err
