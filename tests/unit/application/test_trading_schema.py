"""Unit tests for trading extraction schema and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from qa_report_generator.application.service_definitions.trading.schema import TradingExtractedMetrics


def _trend_metric() -> dict[str, object]:
    return {
        "type": "trend",
        "contains": "time",
        "values": {
            "min": 10.0,
            "avg": 20.0,
            "med": 15.0,
            "max": 40.0,
            "p(95)": 30.0,
            "p(99)": 35.0,
        },
    }


def _counter_metric() -> dict[str, object]:
    return {
        "type": "counter",
        "contains": "default",
        "values": {"count": 100, "rate": 1.5},
    }


def _valid_payload() -> dict[str, object]:
    return {
        "service": "trading",
        "report_file": "trading-1.json",
        "test_run_duration_ms": 639126.469054,
        "scenario": {
            "name": "getOpenAndCloseOrder",
            "env_name": "staging",
            "executor": "constant-arrival-rate",
            "rate": 58,
            "duration": "10m0s",
            "pre_allocated_vus": 200,
            "max_vus": 1000,
        },
        "checks": {"rate": 0.999, "passes": 71114, "fails": 1},
        "http_req_failed": {"rate": 0.0000143, "passes": 1, "fails": 69800},
        "http_reqs": {"count": 71115, "rate": 111.26},
        "iterations": {"count": 34801, "rate": 54.45},
        "get_open_and_close_order_duration": {
            **_trend_metric(),
            "thresholds": {"p(95)<350": {"ok": True}, "p(99) < 500": {"ok": True}},
        },
        "get_open_and_close_order_counter": _counter_metric(),
        "post_open_order_duration": _trend_metric(),
        "post_open_order_counter": _counter_metric(),
        "post_close_trade_duration": _trend_metric(),
        "post_close_trade_counter": _counter_metric(),
        "deposit_balance_duration": _trend_metric(),
        "deposit_balance_counter": _counter_metric(),
        "login_email_duration": _trend_metric(),
        "login_email_fail_counter": _counter_metric(),
        "thresholds": {
            "K6_Metrics_getOpenAndCloseOrder_duration": ["p(95)<350", "p(99) < 500"],
            "http_req_failed{test_name:getOpenAndCloseOrder}": ["rate<0.01"],
        },
    }


def test_trading_schema_accepts_valid_payload() -> None:
    """Trading schema validates an expected extracted payload."""
    model = TradingExtractedMetrics.model_validate(_valid_payload())

    assert model.service == "trading"
    assert model.get_open_and_close_order_duration.values.p95 == 30.0
    assert model.get_open_and_close_order_counter.values.count == 100


def test_trading_schema_rejects_unknown_fields() -> None:
    """Trading schema forbids extra keys in strict extraction output."""
    payload = _valid_payload()
    payload["unexpected"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TradingExtractedMetrics.model_validate(payload)


def test_trading_schema_accepts_camel_case_scenario_aliases() -> None:
    """Trading schema accepts canonical k6 scenario alias field names."""
    payload = _valid_payload()
    payload["scenario"] = {
        "name": "getOpenAndCloseOrder",
        "env_name": "staging",
        "executor": "constant-arrival-rate",
        "rate": 58,
        "duration": "10m0s",
        "preAllocatedVUs": 200,
        "maxVUs": 1000,
    }

    model = TradingExtractedMetrics.model_validate(payload)

    assert model.scenario.pre_allocated_vus == 200
    assert model.scenario.max_vus == 1000


def test_trading_schema_exposes_shared_and_custom_ai_descriptions() -> None:
    """Trading schema includes reusable field descriptions for AI extraction."""
    schema = TradingExtractedMetrics.model_json_schema()
    properties = schema["properties"]

    assert properties["service"]["description"] == "Use literal service name 'trading'"
    assert properties["report_file"]["description"] == "Use verification_context.report_file, populated from the selected scenario source report filename"
    assert properties["checks"]["description"] == "Use $.metrics.checks.values"
    assert properties["http_req_failed"]["description"] == "Use $.metrics.http_req_failed{test_name:<scenario>}.values"
    assert properties["get_open_and_close_order_duration"]["description"] == "Use $.metrics.K6_Metrics_getOpenAndCloseOrder_duration"
    assert properties["login_email_fail_counter"]["description"] == "Use $.metrics.K6_Metrics_login_email_failCounter"
    assert properties["thresholds"]["description"] == "Use $.execThresholds"
