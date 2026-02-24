"""Domain-specific exceptions for the report generation pipeline."""


class ReportingError(Exception):
    """Base exception for reporting domain errors."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        """Initialize with error message and optional suggestion."""
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        """Return the error message."""
        return super().__str__()


class ParseError(ReportingError):
    """Base error for test report parsing failures."""


class ParseFileNotFoundError(ParseError):
    """Test report file not found at specified path."""


class ParseInvalidJsonError(ParseError):
    """Test report contains malformed JSON."""


class ParseInvalidFormatError(ParseError):
    """Test report structure doesn't match expected format."""


class GenerationError(ReportingError):
    """Base error for report generation failures."""


class ConfigurationError(ReportingError):
    """Application configuration is invalid or incomplete."""


class PersistenceError(ReportingError):
    """Failed to save report to file system."""
