"""Registry for service-specific extraction definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.service_definitions.megatron import SERVICE_DEFINITION as MEGATRON_DEFINITION

if TYPE_CHECKING:
    from qa_report_generator.application.service_definitions.base import ServiceDefinition

SERVICE_DEFINITIONS: dict[str, ServiceDefinition] = {
    MEGATRON_DEFINITION.name: MEGATRON_DEFINITION,
}


def get_service_definition(service: str) -> ServiceDefinition:
    """Return service definition by name or raise ValueError."""
    if service in SERVICE_DEFINITIONS:
        return SERVICE_DEFINITIONS[service]
    msg = f"Unsupported service: {service}"
    raise ValueError(msg)


__all__ = [
    "SERVICE_DEFINITIONS",
    "get_service_definition",
]
