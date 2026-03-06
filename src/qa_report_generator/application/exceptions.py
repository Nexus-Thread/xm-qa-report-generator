"""Application-layer exception types."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base error for application-layer failures."""


class ServiceDefinitionRegistryError(ApplicationError):
    """Base error for service definition registry failures."""


class InvalidServiceDefinitionError(ServiceDefinitionRegistryError):
    """Raised when a service definition has invalid metadata."""


class DuplicateServiceDefinitionError(ServiceDefinitionRegistryError):
    """Raised when a service definition name is already registered."""


class UnknownServiceDefinitionError(ServiceDefinitionRegistryError):
    """Raised when a service definition name is not registered."""
