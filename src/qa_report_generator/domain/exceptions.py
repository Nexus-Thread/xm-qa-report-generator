"""Domain exceptions with error codes and suggestions."""


class ReportingError(Exception):
    """Base exception for reporting domain errors."""

    error_code: str = "ERR_UNKNOWN"

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        """Initialize with error message and optional suggestion."""
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        """Format error message with suggestion if available."""
        base_msg = super().__str__()
        if self.suggestion:
            return f"{base_msg}\n💡 Suggestion: {self.suggestion}"
        return base_msg


class ParseError(ReportingError):
    """Base error for test report parsing failures."""

    error_code: str = "ERR_PARSE"


class ParseFileNotFoundError(ParseError):
    """Test report file not found at specified path."""

    error_code: str = "ERR_PARSE_FILE_NOT_FOUND"


class ParseInvalidJsonError(ParseError):
    """Test report contains malformed JSON."""

    error_code: str = "ERR_PARSE_INVALID_JSON"


class ParseInvalidFormatError(ParseError):
    """Test report structure doesn't match expected format."""

    error_code: str = "ERR_PARSE_INVALID_FORMAT"


class GenerationError(ReportingError):
    """Base error for report generation failures."""

    error_code: str = "ERR_GENERATION"


class ConfigurationError(ReportingError):
    """Application configuration is invalid or incomplete."""

    error_code: str = "ERR_CONFIG"


class ConfigInvalidUrlError(ConfigurationError):
    """URL in configuration has invalid format."""

    error_code: str = "ERR_CONFIG_INVALID_URL"


class LLMConnectionError(GenerationError):
    """Failed to connect to LLM service."""

    error_code: str = "ERR_LLM_CONNECTION"


class LLMTimeoutError(GenerationError):
    """LLM request timed out."""

    error_code: str = "ERR_LLM_TIMEOUT"


class LLMInitializationError(GenerationError):
    """Failed to initialize LLM client."""

    error_code: str = "ERR_LLM_INIT"


class PersistenceError(ReportingError):
    """Failed to save report to file system."""

    error_code: str = "ERR_PERSISTENCE"
