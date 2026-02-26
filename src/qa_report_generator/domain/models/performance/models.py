"""K6-specific domain models organized by scenario."""

from pydantic import BaseModel, Field, model_validator


class K6Check(BaseModel):
    """Represents a single k6 check grouped under a scenario."""

    name: str = Field(description="Check name")
    scenario: str = Field(min_length=1, description="k6 scenario name (test_name tag)")
    group_path: str = Field(description="Hierarchical k6 group path")
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
    """Represents a single k6 threshold evaluation for a scenario."""

    scenario: str = Field(min_length=1, description="k6 scenario name (test_name tag)")
    metric_name: str = Field(description="Name of the metric being thresholded")
    expression: str = Field(description="Threshold expression (e.g., 'p(95)<500')")
    ok: bool = Field(description="Whether the threshold was met")

    @property
    def is_violated(self) -> bool:
        """Whether this threshold was violated."""
        return not self.ok


class K6ScenarioContext(BaseModel):
    """Per-scenario summary of k6 checks and thresholds."""

    checks_total: int = Field(ge=0, description="Total number of checks executed")
    checks_passed: int = Field(ge=0, description="Number of checks that passed")
    checks_failed: int = Field(ge=0, description="Number of checks that failed")
    thresholds_total: int = Field(ge=0, description="Total number of thresholds evaluated")
    thresholds_passed: int = Field(ge=0, description="Number of thresholds that passed")
    thresholds_failed: int = Field(ge=0, description="Number of thresholds that were violated")

    @model_validator(mode="after")
    def validate_totals(self) -> "K6ScenarioContext":
        """Validate scenario check and threshold counters are internally consistent."""
        if self.checks_passed + self.checks_failed != self.checks_total:
            msg = "Invalid k6 scenario check counters: checks_total must equal checks_passed + checks_failed"
            raise ValueError(msg)
        if self.thresholds_passed + self.thresholds_failed != self.thresholds_total:
            msg = "Invalid k6 scenario threshold counters: thresholds_total must equal thresholds_passed + thresholds_failed"
            raise ValueError(msg)
        return self


class K6ReportContext(BaseModel):
    """Per-scenario k6 check and threshold breakdown."""

    by_scenario: dict[str, K6ScenarioContext] = Field(
        default_factory=dict,
        description="Per-scenario check/threshold breakdown keyed by scenario name",
    )


class K6SummaryRow(BaseModel):
    """Consolidated summary row for a single k6 scenario report."""

    service: str = Field(description="Service code derived from scenario name")
    scenario: str = Field(description="Scenario identifier")
    target_load_rps: int = Field(ge=0, description="Configured target load in requests per second")
    duration_seconds: int = Field(ge=0, description="Configured scenario duration in seconds")
    thresholds: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Configured threshold expressions keyed by metric name",
    )
    iterations: int = Field(ge=0, description="Executed iterations count")
    achieved_rps: float = Field(ge=0.0, description="Observed steady-state iterations per second")
    latency_metrics_ms: dict[str, float] = Field(
        default_factory=dict,
        description="Latency metrics in milliseconds keyed by statistic name",
    )
    error_rate_percent: float = Field(ge=0.0, description="HTTP error rate percentage")
    outcome_passed: bool = Field(description="Whether all relevant thresholds passed")

    @model_validator(mode="after")
    def validate_dynamic_metrics(self) -> "K6SummaryRow":
        """Validate dynamic threshold and latency metric values."""
        invalid_thresholds = [metric_name for metric_name, expressions in self.thresholds.items() if not metric_name or not isinstance(expressions, list)]
        if invalid_thresholds:
            msg = "Invalid threshold metrics: metric names must be non-empty and map to expression lists"
            raise ValueError(msg)

        invalid_latency_metrics = [metric_name for metric_name, value in self.latency_metrics_ms.items() if value < 0.0]
        if invalid_latency_metrics:
            msg = "Invalid latency metrics: all latency values must be non-negative"
            raise ValueError(msg)

        return self
