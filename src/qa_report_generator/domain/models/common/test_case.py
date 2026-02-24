"""Test case result model."""

from pydantic import BaseModel, Field

from qa_report_generator.domain.value_objects import Duration, TestIdentifier, TestStatus


class TestCaseResult(BaseModel):
    """Result of a single test execution."""

    identifier: TestIdentifier = Field(description="Unique test identifier")
    status: TestStatus = Field(description="Outcome status of the test")
    duration: Duration | None = Field(None, description="Test execution time")
    __test__ = False

    @property
    def test_name(self) -> str:
        """Get test name from identifier."""
        return self.identifier.name

    @property
    def suite(self) -> str:
        """Get suite name from identifier."""
        return self.identifier.suite
