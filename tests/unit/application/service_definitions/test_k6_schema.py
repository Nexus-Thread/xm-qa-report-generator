"""Unit tests for generic extracted k6 schema models."""

from qa_report_generator.application.service_definitions.schema import (
    Scenario,
    TrendValuesMs,
    metric_values_field,
)


def test_scenario_accepts_camel_case_alias_fields() -> None:
    """Scenario model accepts canonical k6 alias field names."""
    scenario = Scenario.model_validate(
        {
            "name": "orders-load",
            "env_name": "staging",
            "executor": "constant-arrival-rate",
            "rate": 10,
            "duration": "1m",
            "preAllocatedVUs": 5,
            "maxVUs": 10,
        }
    )

    assert scenario.pre_allocated_vus == 5
    assert scenario.max_vus == 10


def test_trend_values_accept_percentile_aliases() -> None:
    """Trend values model accepts percentile aliases from k6 payloads."""
    values = TrendValuesMs.model_validate(
        {
            "min": 100.0,
            "avg": 200.0,
            "med": 150.0,
            "max": 900.0,
            "p(95)": 400.0,
            "p(99)": 700.0,
        }
    )

    assert values.p95 == 400.0
    assert values.p99 == 700.0


def test_metric_values_field_supports_optional_metrics() -> None:
    """Metric field guidance can describe optional null fallback."""
    field = metric_values_field("dropped_iterations", optional=True)

    assert field.description == "Use $.metrics.dropped_iterations.values when present; otherwise use null"
