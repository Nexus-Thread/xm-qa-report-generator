"""Retry logic and error handling for LLM requests."""

import logging
import secrets
import time

from openai import APIConnectionError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from qa_report_generator.adapters.output.narrative.llm_adapter.types import ChatMessage
from qa_report_generator.adapters.output.narrative.llm_adapter.validators import validate_messages
from qa_report_generator.domain.exceptions import GenerationError, LLMConnectionError, LLMTimeoutError

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles retry logic and error handling for LLM API requests."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        base_url: str,
        max_retries: int,
        retry_backoff_factor: float,
    ) -> None:
        """Initialize retry handler.

        Args:
            client: OpenAI client instance
            model: Model name for logging
            base_url: Base URL for error messages
            max_retries: Maximum retry attempts
            retry_backoff_factor: Exponential backoff multiplier

        """
        self.client = client
        self.model = model
        self.base_url = base_url
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor

    def chat_completion(
        self,
        messages: list[ChatMessage],
        temperature: float | None = None,
        reasoning_effort: str | None = None,
    ) -> str:
        """Make a chat completion request with retry logic.

        Args:
            messages: List of typed ChatMessage dicts with role and content
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            reasoning_effort: Optional reasoning effort for compatible models

        Returns:
            Generated text content

        Raises:
            LLMConnectionError: If connection to LLM service fails after retries
            LLMTimeoutError: If request times out after retries
            GenerationError: For other LLM-related errors

        """
        validate_messages(messages)
        params = self._build_params(messages, temperature, reasoning_effort)

        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._attempt_request(params, attempt)
            except (APITimeoutError, APIConnectionError, RateLimitError) as e:
                last_exception = e
                if attempt >= self.max_retries:
                    break
                self._sleep_for_retry(attempt, e)
            except AuthenticationError as e:
                raise self._handle_authentication_error() from e
            except Exception as e:
                raise self._handle_generation_error(e) from e

        self._raise_retry_exhausted(last_exception)
        msg = "LLM request failed after retries"
        raise GenerationError(msg)

    def _build_params(
        self,
        messages: list[ChatMessage],
        temperature: float | None,
        reasoning_effort: str | None,
    ) -> dict[str, object]:
        """Build request parameters for chat completion."""
        params: dict[str, object] = {
            "model": self.model,
            "messages": messages,
        }
        if temperature is not None:
            params["temperature"] = temperature
        if reasoning_effort is not None:
            params["reasoning_effort"] = reasoning_effort

        logger.debug(
            "Request params: %s",
            {key: value for key, value in params.items() if key != "messages"},
        )
        return params

    def _handle_authentication_error(self) -> GenerationError:
        """Translate authentication errors into domain errors."""
        msg = f"Authentication failed for LLM service (model: {self.model})"
        logger.exception("LLM authentication error: %s", msg)
        return GenerationError(
            msg,
            suggestion="Check your LLM_API_KEY in .env file. For local services, use 'not-needed'.",
        )

    def _handle_generation_error(self, error: Exception) -> GenerationError:
        """Translate unexpected LLM errors into domain errors."""
        msg = f"LLM generation failed: {type(error).__name__}: {error}"
        logger.exception("LLM error: %s", msg)
        return GenerationError(
            msg,
            suggestion=f"Check that model '{self.model}' is available and the service is properly configured.",
        )

    def _attempt_request(self, params: dict, attempt: int) -> str:
        """Execute a single request attempt.

        Args:
            params: Request parameters
            attempt: Attempt number (0-indexed)

        Returns:
            Generated text content

        """
        if attempt > 0:
            logger.info(
                "Retry attempt %d/%d for LLM request (model=%s)",
                attempt,
                self.max_retries,
                self.model,
            )

        response = self.client.chat.completions.create(**params)

        if attempt > 0:
            logger.info(
                "LLM request succeeded on retry attempt %d (model=%s)",
                attempt,
                self.model,
            )

        return response.choices[0].message.content or ""

    def _sleep_for_retry(self, attempt: int, error: Exception) -> None:
        """Sleep with exponential backoff and jitter before retry.

        Args:
            attempt: Current attempt number (0-indexed)
            error: The exception that triggered the retry

        """
        base_wait = self.retry_backoff_factor**attempt
        jitter = secrets.SystemRandom().uniform(0, base_wait / 2)
        wait_time = base_wait + jitter

        error_type = type(error).__name__
        logger.warning(
            "LLM request failed with %s (attempt %d/%d, model=%s): %s. Retrying in %.2fs...",
            error_type,
            attempt + 1,
            self.max_retries + 1,
            self.model,
            str(error),
            wait_time,
        )

        time.sleep(wait_time)

    def _raise_retry_exhausted(self, last_exception: Exception | None) -> None:
        """Raise appropriate exception when retries are exhausted.

        Args:
            last_exception: The last exception encountered

        Raises:
            LLMTimeoutError: If last exception was a timeout
            LLMConnectionError: If last exception was a connection error
            GenerationError: For rate limit errors or unknown failures

        """
        if isinstance(last_exception, APITimeoutError):
            msg = f"LLM request timed out after {self.max_retries + 1} attempts (model: {self.model})"
            logger.error("LLM timeout after retries: %s", msg)
            raise LLMTimeoutError(
                msg,
                suggestion=f"Increase LLM_TIMEOUT or LLM_MAX_RETRIES in .env, or try a faster model. "
                f"Current timeout: {self.client.timeout}s, retries: {self.max_retries}",
            ) from last_exception
        if isinstance(last_exception, APIConnectionError):
            msg = f"Cannot connect to LLM service at {self.base_url} after {self.max_retries + 1} attempts"
            logger.error("LLM connection error after retries: %s", msg)
            raise LLMConnectionError(
                msg,
                suggestion=f"Check that the LLM service is running and accessible. For local servers: verify the endpoint is accessible at {self.base_url}",
            ) from last_exception
        if isinstance(last_exception, RateLimitError):
            msg = f"Rate limit exceeded for LLM service after {self.max_retries + 1} attempts"
            logger.error("LLM rate limit error after retries: %s", msg)
            raise GenerationError(
                msg,
                suggestion="Wait a moment and try again, or increase LLM_RETRY_BACKOFF_FACTOR for longer waits between retries.",
            ) from last_exception
