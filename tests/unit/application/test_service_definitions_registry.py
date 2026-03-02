"""Unit tests for service definition registry behavior."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from qa_report_generator.application.service_definitions import (
    get_service_definition,
    list_service_definitions,
    register_service_definition,
)

if TYPE_CHECKING:
    from qa_report_generator.application.service_definitions.base import ServiceDefinition


def test_list_service_definitions_contains_builtin_megatron() -> None:
    """Built-in definitions are discovered without manual registry edits."""
    assert "megatron" in list_service_definitions()


def test_register_service_definition_rejects_duplicate_name() -> None:
    """Registry rejects duplicate runtime registration for existing names."""
    existing_definition = get_service_definition("megatron")
    duplicate_definition = replace(existing_definition)

    with pytest.raises(ValueError, match="already registered"):
        register_service_definition(duplicate_definition)


def test_get_service_definition_returns_builtin_definition() -> None:
    """Lookup returns the builtin megatron service definition."""
    definition: ServiceDefinition = get_service_definition("megatron")

    assert definition.name == "megatron"
