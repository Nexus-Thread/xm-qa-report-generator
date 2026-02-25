"""K6-specific domain models for checks and thresholds."""

from pydantic import BaseModel, Field


class K6Check(BaseModel):
    """Represents a single k6 check with pass/fail counts and suite context."""

    name: str = Field(description="Check name")
    suite: str = Field(description="Hierarchical suite path (dot-separated)")
    passes: int = Field(ge=0, description="Number of passing iterations")
    fails: int = Field(ge=0, description="Number of failing iterations")

    @property
    def total_iterations(self) -> int:
        """Total iterations for this check."""
        return self.passes + self.fails

    @property
    def is_failed(self) -> bool:
        """Whether this check has any failures."""
        return self.fails > 0


class K6Threshold(BaseModel):
    """Represents a single k6 threshold evaluation."""

    metric_name: str = Field(description="Name of the metric being thresholded")
    expression: str = Field(description="Threshold expression (e.g., 'p(95)<500')")
    ok: bool = Field(description="Whether the threshold was met")

    @property
    def is_violated(self) -> bool:
        """Whether this threshold was violated."""
        return not self.ok
