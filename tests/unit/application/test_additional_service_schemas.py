"""Unit tests for additional service extraction schemas."""

from qa_report_generator.application.service_definitions import list_service_definitions
from qa_report_generator.application.service_definitions.symbolsservice.schema import SymbolsserviceExtractedMetrics
from qa_report_generator.application.service_definitions.symbolstreeservice.schema import SymbolstreeserviceExtractedMetrics
from qa_report_generator.application.service_definitions.tradinghistoricaldata.schema import TradinghistoricaldataExtractedMetrics
from qa_report_generator.application.service_definitions.vps.schema import VpsExtractedMetrics
from qa_report_generator.application.service_definitions.watchlists.schema import WatchlistsExtractedMetrics


def _scenario_payload(name: str) -> dict[str, object]:
    return {
        "name": name,
        "env_name": "staging",
        "executor": "constant-arrival-rate",
        "rate": 10,
        "duration": "1m",
        "preAllocatedVUs": 5,
        "maxVUs": 10,
    }


def _trend_metric() -> dict[str, object]:
    return {
        "type": "trend",
        "contains": "time",
        "values": {
            "min": 1.0,
            "avg": 2.0,
            "med": 2.0,
            "max": 4.0,
            "p(95)": 3.0,
            "p(99)": 3.5,
        },
    }


def _counter_metric() -> dict[str, object]:
    return {
        "type": "counter",
        "contains": "default",
        "values": {"count": 10, "rate": 1.0},
    }


def test_symbolsservice_schema_accepts_variant_payload() -> None:
    """Symbolsservice schema accepts one operation-specific metric pair."""
    model = SymbolsserviceExtractedMetrics.model_validate(
        {
            "service": "symbolsservice",
            "report_file": "symbolsservice-1.json",
            "test_run_duration_ms": 900011.1,
            "scenario": _scenario_payload("postVisibleSymbolsState"),
            "checks": {"rate": 1.0, "passes": 10, "fails": 0},
            "http_req_failed": {"rate": 0.0, "passes": 10, "fails": 0},
            "http_reqs": {"count": 10, "rate": 1.0},
            "iterations": {"count": 10, "rate": 1.0},
            "post_visible_symbols_state_duration": _trend_metric(),
            "post_visible_symbols_state_counter": _counter_metric(),
            "thresholds": {"http_req_failed{test_name:postVisibleSymbolsState}": ["rate<0.01"]},
        }
    )

    assert model.post_visible_symbols_state_duration is not None
    assert model.post_last_tick_duration is None


def test_symbolstreeservice_schema_accepts_variant_payload() -> None:
    """Symbolstreeservice schema accepts one operation-specific metric trio."""
    model = SymbolstreeserviceExtractedMetrics.model_validate(
        {
            "service": "symbolstreeservice",
            "report_file": "symbolstreeservice-1.json",
            "test_run_duration_ms": 900011.1,
            "scenario": _scenario_payload("getSymbolsTreeInfo7"),
            "checks": {"rate": 1.0, "passes": 10, "fails": 0},
            "http_req_failed": {"rate": 0.0, "passes": 10, "fails": 0},
            "http_reqs": {"count": 10, "rate": 1.0},
            "iterations": {"count": 10, "rate": 1.0},
            "get_symbols_tree_info7_duration": _trend_metric(),
            "get_symbols_tree_info7_counter": _counter_metric(),
            "get_symbols_tree_info7_fail_counter": _counter_metric(),
            "thresholds": {"http_req_failed{test_name:getSymbolsTreeInfo7}": ["rate<0.01"]},
        }
    )

    assert model.get_symbols_tree_info7_fail_counter is not None
    assert model.get_symbols_tree_info0_duration is None


def test_tradinghistoricaldata_schema_accepts_variant_payload() -> None:
    """Tradinghistoricaldata schema accepts shared and operation-specific metrics."""
    model = TradinghistoricaldataExtractedMetrics.model_validate(
        {
            "service": "tradinghistoricaldata",
            "report_file": "tradinghistoricaldata-1.json",
            "test_run_duration_ms": 60000,
            "scenario": _scenario_payload("thdGetCandles"),
            "checks": {"rate": 1.0, "passes": 10, "fails": 0},
            "http_req_failed": {"rate": 0.0, "passes": 10, "fails": 0},
            "http_reqs": {"count": 10, "rate": 1.0},
            "iterations": {"count": 10, "rate": 1.0},
            "dropped_iterations": None,
            "login_email_duration": _trend_metric(),
            "login_email_counter": _counter_metric(),
            "thd_candles_duration": _trend_metric(),
            "thd_candles_counter": _counter_metric(),
            "thd_candles_fail_counter": _counter_metric(),
            "thresholds": {"http_req_failed{test_name:thdGetCandles}": ["rate<0.01"]},
        }
    )

    assert model.login_email_duration is not None
    assert model.thd_trading_history_duration is None


def test_vps_schema_accepts_payload() -> None:
    """Vps schema accepts its supported custom metrics."""
    model = VpsExtractedMetrics.model_validate(
        {
            "service": "vps",
            "report_file": "vps-1.json",
            "test_run_duration_ms": 60000,
            "scenario": _scenario_payload("getVpsEligible"),
            "checks": {"rate": 1.0, "passes": 10, "fails": 0},
            "http_req_failed": {"rate": 0.0, "passes": 10, "fails": 0},
            "http_reqs": {"count": 10, "rate": 1.0},
            "iterations": {"count": 10, "rate": 1.0},
            "dropped_iterations": None,
            "get_vps_eligible_duration": _trend_metric(),
            "get_vps_eligible_counter": _counter_metric(),
            "get_vps_eligible_fail_counter": _counter_metric(),
            "thresholds": {"http_req_failed{test_name:getVpsEligible}": ["rate<0.01"]},
        }
    )

    assert model.get_vps_eligible_duration is not None


def test_watchlists_schema_accepts_variant_payload() -> None:
    """Watchlists schema accepts one watchlist operation metric pair."""
    model = WatchlistsExtractedMetrics.model_validate(
        {
            "service": "watchlists",
            "report_file": "watchlists-1.json",
            "test_run_duration_ms": 60000,
            "scenario": _scenario_payload("getV4Watchlists1"),
            "checks": {"rate": 1.0, "passes": 10, "fails": 0},
            "http_req_failed": {"rate": 0.0, "passes": 10, "fails": 0},
            "http_reqs": {"count": 10, "rate": 1.0},
            "iterations": {"count": 10, "rate": 1.0},
            "get_v4_watchlists1_duration": _trend_metric(),
            "get_v4_watchlists1_counter": _counter_metric(),
            "thresholds": {"http_req_failed{test_name:getV4Watchlists1}": ["rate<0.01"]},
        }
    )

    assert model.get_v4_watchlists1_duration is not None
    assert model.get_v1_watchlists_duration is None


def test_registry_lists_all_fixture_backed_service_definitions() -> None:
    """Registry discovers all fixture-backed built-in service definitions."""
    names = set(list_service_definitions())

    assert {
        "megatron",
        "symbolsservice",
        "symbolstreeservice",
        "trading",
        "tradinghistoricaldata",
        "vps",
        "watchlists",
    }.issubset(names)
