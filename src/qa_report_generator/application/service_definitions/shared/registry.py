"""Registry for builtin and runtime service definitions."""

from __future__ import annotations

import importlib
import pkgutil
from types import MappingProxyType
from typing import TYPE_CHECKING

from qa_report_generator.application.exceptions import (
    DuplicateServiceDefinitionError,
    InvalidServiceDefinitionError,
    UnknownServiceDefinitionError,
)

if TYPE_CHECKING:
    from .base import ServiceDefinition


class ServiceDefinitionRegistry:
    """Manage discovery, registration, and lookup of service definitions."""

    def __init__(self, *, package_name: str, package_paths: list[str]) -> None:
        """Store package discovery context for builtin definitions.

        Args:
            package_name: Package used as discovery root
            package_paths: Filesystem paths searched for builtin service packages

        """
        self._package_name = package_name
        self._package_paths = package_paths
        self._definitions: dict[str, ServiceDefinition] = {}
        self._sources: dict[str, str] = {}
        self._builtins_discovered = False

    @property
    def definitions(self) -> MappingProxyType[str, ServiceDefinition]:
        """Return a read-only registered definitions mapping."""
        self._discover_builtin_definitions()
        return MappingProxyType(self._definitions)

    def register(self, definition: ServiceDefinition) -> None:
        """Register one service definition for runtime use."""
        self._discover_builtin_definitions()
        self._store_definition(definition=definition, source="runtime")

    def list_names(self) -> tuple[str, ...]:
        """Return sorted names of registered service definitions."""
        self._discover_builtin_definitions()
        return tuple(sorted(self._definitions))

    def get(self, service: str) -> ServiceDefinition:
        """Return a service definition or raise an application error."""
        self._discover_builtin_definitions()
        if service in self._definitions:
            return self._definitions[service]
        msg = f"Unsupported service: {service}"
        raise UnknownServiceDefinitionError(msg)

    def get_optional(self, service: str) -> ServiceDefinition | None:
        """Return a service definition or None when not registered."""
        self._discover_builtin_definitions()
        return self._definitions.get(service)

    def _store_definition(self, *, definition: ServiceDefinition, source: str) -> None:
        """Store one definition and reject conflicting registrations."""
        name = definition.name.strip()
        if not name:
            msg = "Service definition name must not be empty"
            raise InvalidServiceDefinitionError(msg)

        existing = self._definitions.get(name)
        if existing is not None and existing is not definition:
            existing_source = self._sources.get(name, "unknown")
            msg = f"Service definition '{name}' already registered by {existing_source}"
            raise DuplicateServiceDefinitionError(msg)

        self._definitions[name] = definition
        self._sources[name] = source

    def _discover_builtin_definitions(self) -> None:
        """Discover built-in service definitions from subpackages."""
        if self._builtins_discovered:
            return

        for module_info in pkgutil.iter_modules(self._package_paths):
            if not module_info.ispkg or module_info.name.startswith("_"):
                continue

            module = importlib.import_module(f"{self._package_name}.{module_info.name}")
            definition = getattr(module, "SERVICE_DEFINITION", None)
            if definition is None:
                continue
            self._store_definition(definition=definition, source=f"builtin:{module_info.name}")

        self._builtins_discovered = True
