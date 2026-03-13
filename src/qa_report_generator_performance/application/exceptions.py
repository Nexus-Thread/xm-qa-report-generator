"""Application-layer exception types."""

from __future__ import annotations

from qa_report_generator_performance.domain.exceptions import ReportingError


class ApplicationError(ReportingError):
    """Base error for application-layer failures."""


class ConfigurationError(ApplicationError):
    """Raised when application configuration or report input is invalid."""


class ExtractionVerificationError(ApplicationError):
    """Raised when extraction or verification payloads are invalid."""


class ServiceDefinitionRegistryError(ApplicationError):
    """Base error for service definition registry failures."""


class InvalidServiceDefinitionError(ServiceDefinitionRegistryError):
    """Raised when a service definition has invalid metadata."""


class DuplicateServiceDefinitionError(ServiceDefinitionRegistryError):
    """Raised when a service definition name is already registered."""


class UnknownServiceDefinitionError(ServiceDefinitionRegistryError):
    """Raised when a service definition name is not registered."""
