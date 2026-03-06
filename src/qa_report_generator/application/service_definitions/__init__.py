"""Service definition registry entrypoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import ServiceDefinitionRegistry

if TYPE_CHECKING:
    from .base import ServiceDefinition

REGISTRY = ServiceDefinitionRegistry(
    package_name=__name__,
    package_paths=list(globals().get("__path__", [])),
)


def register_service_definition(definition: ServiceDefinition) -> None:
    """Register one service definition for runtime use."""
    REGISTRY.register(definition)


def list_service_definitions() -> tuple[str, ...]:
    """Return sorted names of registered service definitions."""
    return REGISTRY.list_names()


def get_service_definition(service: str) -> ServiceDefinition:
    """Return service definition by name or raise an application error."""
    return REGISTRY.get(service)


def get_optional_service_definition(service: str) -> ServiceDefinition | None:
    """Return service definition by name or None when unsupported."""
    return REGISTRY.get_optional(service)


SERVICE_DEFINITIONS = REGISTRY.definitions


__all__ = [
    "REGISTRY",
    "SERVICE_DEFINITIONS",
    "get_optional_service_definition",
    "get_service_definition",
    "list_service_definitions",
    "register_service_definition",
]
