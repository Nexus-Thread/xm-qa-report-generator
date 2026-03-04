"""Registry for service-specific extraction definitions."""

from __future__ import annotations

import importlib
import pkgutil
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.application.service_definitions.base import ServiceDefinition


_SERVICE_DEFINITIONS: dict[str, ServiceDefinition] = {}
_SERVICE_SOURCES: dict[str, str] = {}
_DISCOVERY_STATE = {"builtins_discovered": False}

SERVICE_DEFINITIONS = MappingProxyType(_SERVICE_DEFINITIONS)


def _store_definition(*, definition: ServiceDefinition, source: str) -> None:
    """Store one definition and reject conflicting registrations."""
    name = definition.name.strip()
    if not name:
        msg = "Service definition name must not be empty"
        raise ValueError(msg)

    existing = _SERVICE_DEFINITIONS.get(name)
    if existing is not None and existing is not definition:
        existing_source = _SERVICE_SOURCES.get(name, "unknown")
        msg = f"Service definition '{name}' already registered by {existing_source}"
        raise ValueError(msg)

    _SERVICE_DEFINITIONS[name] = definition
    _SERVICE_SOURCES[name] = source


def _discover_builtin_definitions() -> None:
    """Discover built-in service definitions from subpackages."""
    if _DISCOVERY_STATE["builtins_discovered"]:
        return

    package_paths = list(globals().get("__path__", []))
    for module_info in pkgutil.iter_modules(package_paths):
        if not module_info.ispkg or module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{__name__}.{module_info.name}")
        definition = getattr(module, "SERVICE_DEFINITION", None)
        if definition is None:
            continue
        _store_definition(definition=definition, source=f"builtin:{module_info.name}")

    _DISCOVERY_STATE["builtins_discovered"] = True


def register_service_definition(definition: ServiceDefinition) -> None:
    """Register one service definition for runtime use."""
    _discover_builtin_definitions()
    _store_definition(definition=definition, source="runtime")


def list_service_definitions() -> tuple[str, ...]:
    """Return sorted names of registered service definitions."""
    _discover_builtin_definitions()
    return tuple(sorted(_SERVICE_DEFINITIONS))


def get_service_definition(service: str) -> ServiceDefinition:
    """Return service definition by name or raise ValueError."""
    _discover_builtin_definitions()
    if service in _SERVICE_DEFINITIONS:
        return _SERVICE_DEFINITIONS[service]
    msg = f"Unsupported service: {service}"
    raise ValueError(msg)


__all__ = [
    "SERVICE_DEFINITIONS",
    "get_service_definition",
    "list_service_definitions",
    "register_service_definition",
]
