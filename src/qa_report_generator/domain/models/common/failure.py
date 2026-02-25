"""Test failure model."""

from pydantic import BaseModel, Field

# TestOutput is populated by the pytest parser. k6 failures have output=None.
from qa_report_generator.domain.models.common.test_output import TestOutput
from qa_report_generator.domain.value_objects import Duration, TestIdentifier


class Failure(BaseModel):
    """A single test failure with diagnostic information."""

    identifier: TestIdentifier = Field(description="Unique test identifier")
    message: str = Field(min_length=1, description="Error or failure message")
    type: str | None = Field(None, description="Exception type (e.g., AssertionError)")
    duration: Duration | None = Field(None, description="Test execution time")
    output: TestOutput | None = Field(
        None,
        description="Captured output streams — populated by the pytest parser only; None for k6 results",
    )

    @property
    def test_name(self) -> str:
        """Get test name from identifier."""
        return self.identifier.name

    @property
    def suite(self) -> str:
        """Get suite name from identifier."""
        return self.identifier.suite
