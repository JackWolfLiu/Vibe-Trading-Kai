"""Tests for Task 5 Taiwan stock CompositeEngine routing."""

from __future__ import annotations

from backtest.engines.composite import CompositeEngine
from backtest.engines.taiwan_stock import TaiwanStockEngine
from backtest.runner import _create_market_engine


def test_composite_engine_builds_taiwan_stock_rules() -> None:
    engine = _create_market_engine("auto", {"initial_cash": 100_000}, ["000001.SZ", "2330.TW"])

    assert isinstance(engine, CompositeEngine)
    assert isinstance(engine._rule_engines["tw_stock"], TaiwanStockEngine)
