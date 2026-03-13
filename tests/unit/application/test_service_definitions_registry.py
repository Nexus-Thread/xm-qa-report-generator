"""Unit tests for service definition registry behavior."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from qa_report_generator_performance.application.exceptions import (
    DuplicateServiceDefinitionError,
    UnknownServiceDefinitionError,
)
from qa_report_generator_performance.application.service_definitions import (
    get_optional_service_definition,
    get_service_definition,
    list_service_definitions,
    register_service_definition,
)
from qa_report_generator_performance.application.service_definitions.shared.schema import K6HttpExtractedMetrics

if TYPE_CHECKING:
    from qa_report_generator_performance.application.service_definitions.shared.base import ServiceDefinition


def test_list_service_definitions_contains_builtin_megatron() -> None:
    """Built-in definitions are discovered without manual registry edits."""
    assert "megatron" in list_service_definitions()
    assert "trading" in list_service_definitions()


def test_register_service_definition_rejects_duplicate_name() -> None:
    """Registry rejects duplicate runtime registration for existing names."""
    existing_definition = get_service_definition("megatron")
    duplicate_definition = replace(existing_definition)

    with pytest.raises(DuplicateServiceDefinitionError, match="already registered"):
        register_service_definition(duplicate_definition)


def test_get_service_definition_returns_builtin_definition() -> None:
    """Lookup returns the builtin megatron service definition."""
    definition: ServiceDefinition = get_service_definition("megatron")

    assert definition.name == "megatron"
    assert issubclass(definition.schema_type, K6HttpExtractedMetrics)


def test_get_optional_service_definition_returns_none_for_unknown_service() -> None:
    """Optional lookup returns None for unsupported services."""
    assert get_optional_service_definition("unknown-service") is None


def test_get_service_definition_rejects_unknown_service() -> None:
    """Lookup raises application-specific error for unsupported services."""
    with pytest.raises(UnknownServiceDefinitionError, match="Unsupported service"):
        get_service_definition("unknown-service")
