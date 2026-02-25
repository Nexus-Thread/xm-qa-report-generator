"""Domain preprocessing utilities."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from qa_report_generator.domain.models.common import Failure, TestOutput

if TYPE_CHECKING:
    from collections.abc import Iterable


class FailureGroup(BaseModel):
    """Grouped failures sharing a common signature."""

    signature: str = Field(description="Normalized signature for the grouped failures")
    count: int = Field(ge=1, description="Number of failures in the group")
    representative: Failure = Field(description="Representative failure example")
    test_names: list[str] = Field(description="Test names contained in the group")


class OutputTruncator:
    """Truncate verbose output while preserving useful context."""

    def __init__(self, max_head_lines: int = 10, max_tail_lines: int = 10) -> None:
        """Initialize truncation settings for output streams."""
        self.max_head_lines = max_head_lines
        self.max_tail_lines = max_tail_lines

    def truncate_output(self, output: TestOutput | None) -> TestOutput | None:
        """Return a truncated copy of captured output streams."""
        if output is None:
            return None

        stdout = self._truncate_text(output.stdout)
        stderr = self._truncate_text(output.stderr)
        log = self._truncate_text(output.log)

        if stdout is None and stderr is None and log is None:
            return None

        return TestOutput(stdout=stdout, stderr=stderr, log=log)

    def _truncate_text(self, text: str | None) -> str | None:
        if text is None:
            return None

        lines = text.splitlines()
        max_lines = self.max_head_lines + self.max_tail_lines
        if len(lines) <= max_lines:
            return text

        head = lines[: self.max_head_lines] if self.max_head_lines > 0 else []
        tail = lines[-self.max_tail_lines :] if self.max_tail_lines > 0 else []
        truncated_count = len(lines) - len(head) - len(tail)

        ellipsis = f"... (truncated {truncated_count} lines) ..."
        truncated_lines = [*head, ellipsis, *tail]
        return "\n".join(truncated_lines)


class FailurePatternExtractor:
    """Extract normalized signatures from failures for grouping."""

    _url_re = re.compile(r"https?://\S+")
    _path_re = re.compile(r"(?:[A-Za-z]:)?[/\\][\w\-./\\]+")
    _hex_re = re.compile(r"0x[0-9a-fA-F]+")
    _number_re = re.compile(r"\b\d+\b")
    _whitespace_re = re.compile(r"\s+")

    def __init__(self, signature_max_length: int = 200) -> None:
        """Initialize signature length configuration."""
        self.signature_max_length = signature_max_length

    def signature_for_failure(self, failure: Failure) -> str:
        """Compute a normalized signature for a failure."""
        error_type = failure.type or "unknown"
        normalized_message = self._normalize_message(failure.message)
        signature = f"{error_type}:{normalized_message}"
        if len(signature) > self.signature_max_length:
            return signature[: self.signature_max_length] + "..."
        return signature

    def _normalize_message(self, message: str) -> str:
        normalized = message.lower().strip()
        if not normalized:
            return "unknown"

        normalized = self._url_re.sub("<url>", normalized)
        normalized = self._path_re.sub("<path>", normalized)
        normalized = self._hex_re.sub("<hex>", normalized)
        normalized = self._number_re.sub("<num>", normalized)
        return self._whitespace_re.sub(" ", normalized)


class FailureGrouper:
    """Group failures by extracted signature."""

    def __init__(self, pattern_extractor: FailurePatternExtractor | None = None) -> None:
        """Initialize grouper with a pattern extractor."""
        self.pattern_extractor = pattern_extractor or FailurePatternExtractor()

    def group_failures_by_pattern(
        self,
        failures: Iterable[Failure],
    ) -> list[FailureGroup]:
        """Group failures by error signature."""
        groups: dict[str, list[Failure]] = defaultdict(list)
        for failure in failures:
            signature = self.pattern_extractor.signature_for_failure(failure)
            groups[signature].append(failure)

        return [
            FailureGroup(
                signature=signature,
                count=len(group),
                representative=group[0],
                test_names=[failure.test_name for failure in group],
            )
            for signature, group in groups.items()
        ]
