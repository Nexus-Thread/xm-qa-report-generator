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


class K6LoadStage(BaseModel):
    """Single k6 load stage configuration."""

    duration: str = Field(min_length=1, description="Stage duration as defined in k6 scenario config")
    target: int = Field(ge=0, description="Target VUs or iteration rate for this stage")


class K6ScenarioLoadModel(BaseModel):
    """Normalized k6 scenario load-model configuration."""

    executor: str = Field(min_length=1, description="k6 executor type for the scenario")
    rate: int | None = Field(default=None, ge=0, description="Target arrival rate when configured")
    time_unit: str | None = Field(default=None, description="k6 time unit used with rate-based executors")
    duration: str | None = Field(default=None, description="Configured scenario duration")
    start_vus: int | None = Field(default=None, ge=0, description="Initial VUs when configured")
    pre_allocated_vus: int | None = Field(default=None, ge=0, description="Pre-allocated VUs for arrival-rate executors")
    max_vus: int | None = Field(default=None, ge=0, description="Maximum VUs for the scenario")
    stages: list[K6LoadStage] = Field(default_factory=list, description="Optional ramping stages")


class K6ReportContext(BaseModel):
    """Per-scenario k6 check, threshold, and load-model breakdown."""

    by_scenario: dict[str, K6ScenarioContext] = Field(
        default_factory=dict,
        description="Per-scenario check/threshold breakdown keyed by scenario name",
    )
    scenario_load_models: dict[str, K6ScenarioLoadModel] = Field(
        default_factory=dict,
        description="Per-scenario load-model configuration keyed by scenario name",
    )

    @property
    def checks_total(self) -> int:
        """Total checks across all scenarios."""
        return sum(context.checks_total for context in self.by_scenario.values())

    @property
    def checks_passed(self) -> int:
        """Total passing checks across all scenarios."""
        return sum(context.checks_passed for context in self.by_scenario.values())

    @property
    def checks_failed(self) -> int:
        """Total failed checks across all scenarios."""
        return sum(context.checks_failed for context in self.by_scenario.values())

    @property
    def thresholds_total(self) -> int:
        """Total thresholds across all scenarios."""
        return sum(context.thresholds_total for context in self.by_scenario.values())

    @property
    def thresholds_passed(self) -> int:
        """Total passing thresholds across all scenarios."""
        return sum(context.thresholds_passed for context in self.by_scenario.values())

    @property
    def thresholds_failed(self) -> int:
        """Total failed thresholds across all scenarios."""
        return sum(context.thresholds_failed for context in self.by_scenario.values())


class K6SummaryRow(BaseModel):
    """Consolidated summary row for a single k6 scenario report."""

    service: str = Field(description="Service code derived from scenario name")
    scenario: str = Field(description="Scenario identifier")
    executor: str = Field(default="unknown", min_length=1, description="k6 executor type")
    time_unit: str | None = Field(default=None, description="k6 time unit for rate-based executors")
    pre_allocated_vus: int | None = Field(default=None, ge=0, description="Pre-allocated VUs from scenario config")
    max_vus: int | None = Field(default=None, ge=0, description="Maximum VUs from scenario config")
    observed_vus_current: int | None = Field(default=None, ge=0, description="Observed current VUs from k6 runtime metrics")
    observed_vus_peak: int | None = Field(default=None, ge=0, description="Observed peak VUs from k6 runtime metrics")
    total_requests: int | None = Field(default=None, ge=0, description="Total HTTP requests executed")
    dropped_iterations: int | None = Field(default=None, ge=0, description="Dropped iterations reported by k6")
    checks_passes: int | None = Field(default=None, ge=0, description="Passing checks count")
    checks_fails: int | None = Field(default=None, ge=0, description="Failing checks count")
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
    waiting_metrics_ms: dict[str, float] = Field(
        default_factory=dict,
        description="HTTP waiting-time metrics in milliseconds keyed by statistic name",
    )
    connecting_metrics_ms: dict[str, float] = Field(
        default_factory=dict,
        description="HTTP connecting-time metrics in milliseconds keyed by statistic name",
    )
    tls_handshaking_metrics_ms: dict[str, float] = Field(
        default_factory=dict,
        description="HTTP TLS handshaking metrics in milliseconds keyed by statistic name",
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
