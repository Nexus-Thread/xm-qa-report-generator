"""Shared types for service-specific extraction definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import BaseModel


@dataclass(frozen=True)
class ServiceDefinition:
    """Configuration bundle describing one service extraction contract."""

    name: str
    schema_model: type[BaseModel]
    remove_keys: frozenset[str]
    extraction_system_prompt: str
    verification_system_prompt: str
    build_extraction_user_prompt: Callable[[str, dict[str, Any], str], str]
    build_verification_user_prompt: Callable[[str, str], str]
    validate_extracted: Callable[[BaseModel], None] | None = None

    @property
    def schema_type(self) -> type[BaseModel]:
        """Backward-compatible alias for schema model type."""
        return self.schema_model

    def dump_schema(self) -> dict[str, Any]:
        """Return JSON schema for the service extraction model."""
        return self.schema_model.model_json_schema()
