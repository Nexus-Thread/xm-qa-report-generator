"""Service definition resolution helpers for k6 extraction use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.service_definitions import get_service_definition

if TYPE_CHECKING:
    from qa_report_generator.application.service_definitions.base import ServiceDefinition


def resolve_service_definition(service: str) -> ServiceDefinition | None:
    """Resolve optional service definition for extraction flow."""
    try:
        return get_service_definition(service)
    except ValueError:
        return None
