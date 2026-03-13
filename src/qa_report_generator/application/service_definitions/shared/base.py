"""Shared types for service-specific extraction definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class PreparedExtractionRun:
    """Prepared typed extraction result before output DTO conversion."""

    source_report_files: tuple[str, ...]
    extracted: BaseModel

    def __post_init__(self) -> None:
        """Normalize provenance into an immutable tuple."""
        object.__setattr__(self, "source_report_files", tuple(self.source_report_files))


@dataclass(frozen=True)
class ServiceDefinition:
    """Configuration bundle describing one service extraction contract."""

    name: str
    schema_model: type[BaseModel]
    remove_keys: frozenset[str]
    extraction_system_prompt: str
    verification_system_prompt: str
    build_extraction_user_prompt: Callable[[str, dict[str, Any], str, str], str]
    build_verification_user_prompt: Callable[[str, str, dict[str, Any], dict[str, Any]], str]
    validate_extracted: Callable[[BaseModel], None] | None = None
    post_process_extracted: Callable[[list[PreparedExtractionRun]], list[PreparedExtractionRun]] | None = None

    @property
    def schema_type(self) -> type[BaseModel]:
        """Backward-compatible alias for schema model type."""
        return self.schema_model

    def dump_schema(self) -> dict[str, Any]:
        """Return JSON schema for the service extraction model."""
        return _strip_internal_fields(self.schema_model.model_json_schema())


def _strip_internal_fields(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove internal-only top-level schema fields from exported JSON schema."""
    normalized_schema = dict(schema)
    properties = normalized_schema.get("properties")
    if not isinstance(properties, dict):
        return normalized_schema

    filtered_properties = {
        field_name: field_schema
        for field_name, field_schema in properties.items()
        if not (isinstance(field_schema, dict) and field_schema.get("internal") is True)
    }
    normalized_schema["properties"] = filtered_properties

    required_fields = normalized_schema.get("required")
    if isinstance(required_fields, list):
        normalized_schema["required"] = [field_name for field_name in required_fields if field_name in filtered_properties]

    return normalized_schema
