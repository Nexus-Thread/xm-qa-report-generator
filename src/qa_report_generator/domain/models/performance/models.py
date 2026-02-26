"""K6-specific domain models for checks, thresholds, and report context."""

from pydantic import BaseModel, Field, model_validator


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


class K6ReportContext(BaseModel):
    """Breakdown of k6 check and threshold results."""

    checks_total: int = Field(ge=0, description="Total number of checks executed")
    checks_passed: int = Field(ge=0, description="Number of checks that passed")
    checks_failed: int = Field(ge=0, description="Number of checks that failed")
    thresholds_total: int = Field(ge=0, description="Total number of thresholds evaluated")
    thresholds_passed: int = Field(ge=0, description="Number of thresholds that passed")
    thresholds_failed: int = Field(ge=0, description="Number of thresholds that were violated")

    @model_validator(mode="after")
    def validate_totals(self) -> "K6ReportContext":
        """Validate check and threshold counters are internally consistent."""
        if self.checks_passed + self.checks_failed != self.checks_total:
            msg = (
                "Invalid k6 check counters: checks_total must equal "
                "checks_passed + checks_failed"
            )
            raise ValueError(msg)
        if self.thresholds_passed + self.thresholds_failed != self.thresholds_total:
            msg = (
                "Invalid k6 threshold counters: thresholds_total must equal "
                "thresholds_passed + thresholds_failed"
            )
            raise ValueError(msg)
        return self


class K6SummaryRow(BaseModel):
    """Consolidated summary row for a single k6 scenario report."""

    service: str = Field(description="Service code derived from scenario name")
    scenario: str = Field(description="Scenario identifier")
    target_load_rps: int = Field(ge=0, description="Configured target load in requests per second")
    duration_seconds: int = Field(ge=0, description="Configured scenario duration in seconds")
    thresholds: list[str] = Field(default_factory=list, description="Configured threshold expressions")
    iterations: int = Field(ge=0, description="Executed iterations count")
    achieved_rps: float = Field(ge=0.0, description="Observed steady-state iterations per second")
    latency_med_ms: float = Field(ge=0.0, description="Median latency in milliseconds")
    latency_p95_ms: float = Field(ge=0.0, description="P95 latency in milliseconds")
    latency_p99_ms: float = Field(ge=0.0, description="P99 latency in milliseconds")
    latency_max_ms: float = Field(ge=0.0, description="Maximum latency in milliseconds")
    error_rate_percent: float = Field(ge=0.0, description="HTTP error rate percentage")
    outcome_passed: bool = Field(description="Whether all relevant thresholds passed")
