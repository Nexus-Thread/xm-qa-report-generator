"""Generic k6 metric schema models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CounterValues(BaseModel):
    """k6 counter values."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0, description="Use $.metrics.<metric_key>.values.count")
    rate: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.rate")


class RateValues(BaseModel):
    """k6 rate values."""

    model_config = ConfigDict(extra="forbid")

    rate: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.rate")
    passes: int = Field(ge=0, description="Use $.metrics.<metric_key>.values.passes")
    fails: int = Field(ge=0, description="Use $.metrics.<metric_key>.values.fails")


class GaugeValues(BaseModel):
    """k6 gauge values."""

    model_config = ConfigDict(extra="forbid")

    value: float = Field(description="Use $.metrics.<metric_key>.values.value")
    min: float = Field(description="Use $.metrics.<metric_key>.values.min")
    max: float = Field(description="Use $.metrics.<metric_key>.values.max")


class TrendValuesMs(BaseModel):
    """k6 trend values in ms."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    min: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.min")
    avg: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.avg")
    med: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.med")
    max: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.max")
    p95: float = Field(ge=0, description='Use $.metrics.<metric_key>.values["p(95)"]')
    p99: float = Field(ge=0, description='Use $.metrics.<metric_key>.values["p(99)"]')


class ThresholdResult(BaseModel):
    """Threshold evaluation result."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = Field(description='Use $.metrics.<metric_key>.thresholds["<expr>"].ok')


class MetricBase(BaseModel):
    """Shared fields for typed k6 metrics."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["counter", "gauge", "rate", "trend"]
    contains: Literal["default", "time", "data"]


class CounterMetric(MetricBase):
    """Counter metric wrapper."""

    type: Literal["counter"]
    values: CounterValues


class GaugeMetric(MetricBase):
    """Gauge metric wrapper."""

    type: Literal["gauge"]
    values: GaugeValues


class RateMetric(MetricBase):
    """Rate metric wrapper."""

    type: Literal["rate"]
    values: RateValues
    thresholds: dict[str, ThresholdResult] | None = None


class TrendMetric(MetricBase):
    """Trend metric wrapper."""

    type: Literal["trend"]
    values: TrendValuesMs
    thresholds: dict[str, ThresholdResult] | None = None


K6Metric = CounterMetric | GaugeMetric | RateMetric | TrendMetric


class K6StandardMetrics(BaseModel):
    """Standard built-in metrics (appear in most runs)."""

    model_config = ConfigDict(extra="forbid")

    checks: RateMetric | None = None
    data_received: CounterMetric | None = None
    data_sent: CounterMetric | None = None
    dropped_iterations: CounterMetric | None = None
    iteration_duration: TrendMetric | None = None
    iterations: CounterMetric | None = None
    vus: GaugeMetric | None = None
    vus_max: GaugeMetric | None = None


class K6HttpMetrics(BaseModel):
    """HTTP built-in metrics (only if HTTP requests are made)."""

    model_config = ConfigDict(extra="forbid")

    http_req_blocked: TrendMetric | None = None
    http_req_connecting: TrendMetric | None = None
    http_req_duration: TrendMetric | None = None
    http_req_failed: RateMetric | None = None
    http_req_receiving: TrendMetric | None = None
    http_req_sending: TrendMetric | None = None
    http_req_tls_handshaking: TrendMetric | None = None
    http_req_waiting: TrendMetric | None = None
    http_reqs: CounterMetric | None = None


class K6WebSocketMetrics(BaseModel):
    """WebSocket metrics (only if ws is used)."""

    model_config = ConfigDict(extra="forbid")

    ws_connecting: TrendMetric | None = None
    ws_msgs_received: CounterMetric | None = None
    ws_msgs_sent: CounterMetric | None = None
    ws_ping: TrendMetric | None = None
    ws_session_duration: TrendMetric | None = None
    ws_sessions: CounterMetric | None = None


class K6GrpcMetrics(BaseModel):
    """gRPC metrics (only if grpc is used)."""

    model_config = ConfigDict(extra="forbid")

    grpc_req_duration: TrendMetric | None = None
    grpc_streams: CounterMetric | None = None
    grpc_streams_msgs_received: CounterMetric | None = None
    grpc_streams_msgs_sent: CounterMetric | None = None


class K6Metrics(BaseModel):
    """Parsed metrics."""

    model_config = ConfigDict(extra="forbid")

    standard: K6StandardMetrics = Field(default_factory=K6StandardMetrics)
    http: K6HttpMetrics = Field(default_factory=K6HttpMetrics)
    ws: K6WebSocketMetrics = Field(default_factory=K6WebSocketMetrics)
    grpc: K6GrpcMetrics = Field(default_factory=K6GrpcMetrics)

    tagged: dict[str, K6Metric] = Field(default_factory=dict)
    custom: dict[str, K6Metric] = Field(default_factory=dict)
