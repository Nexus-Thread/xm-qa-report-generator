"""Unit tests for generic extracted k6 schema models."""

from qa_report_generator.application.service_definitions.shared.schema import (
    K6HttpExtractedMetrics,
    Scenario,
    TrendValuesMs,
    counter_metric_field,
    metric_values_field,
    threshold_statuses_field,
    trend_metric_field,
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


def test_metric_values_field_disambiguates_exact_tagged_metrics() -> None:
    """Metric field guidance requires the exact tagged metric entry."""
    field = metric_values_field("http_req_failed{test_name:<scenario>}")

    assert field.description == (
        "Use the exact tagged metric entry $.metrics.http_req_failed{test_name:<scenario>}.values; do not use a generic sibling metric with the same base name"
    )


def test_full_metric_fields_describe_whole_metric_objects() -> None:
    """Full metric helpers point to whole custom metric objects."""
    counter_field = counter_metric_field("custom_counter")
    trend_field = trend_metric_field("custom_trend")

    assert counter_field.description == "Use $.metrics.custom_counter"
    assert trend_field.description == "Use $.metrics.custom_trend"


def test_threshold_statuses_field_is_marked_internal() -> None:
    """Threshold status lookup is an internal schema field, not an LLM extraction input."""
    field = threshold_statuses_field()

    assert field.json_schema_extra == {"internal": True}


def test_k6_http_extracted_metrics_supports_threshold_status_lookup() -> None:
    """Shared HTTP extraction schema includes normalized threshold status lookup."""
    annotation = K6HttpExtractedMetrics.model_fields["threshold_statuses"].annotation

    assert annotation == dict[str, dict[str, bool]]
