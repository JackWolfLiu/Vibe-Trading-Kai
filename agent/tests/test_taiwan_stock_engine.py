"""Tests for TaiwanStockEngine market rules."""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.engines.taiwan_stock import TaiwanStockEngine
from backtest.runner import _create_market_engine


def _make_bar(close: float = 100.0, pre_close: float | None = None) -> pd.Series:
    """Build a minimal Taiwan stock OHLC bar."""
    data: dict[str, float] = {"close": close, "open": close}
    if pre_close is not None:
        data["pre_close"] = pre_close
    return pd.Series(data)


def _make_engine(**overrides) -> TaiwanStockEngine:
    config = {"initial_cash": 1_000_000}
    config.update(overrides)
    return TaiwanStockEngine(config)


class TestTaiwanStockExecutionRules:
    def test_same_day_sell_has_no_t_plus_one_block(self) -> None:
        engine = _make_engine()

        assert engine.can_execute("2330.TW", 0, _make_bar()) is True

    def test_limit_up_blocks_buy(self) -> None:
        engine = _make_engine()

        assert engine.can_execute("2330.TW", 1, _make_bar(close=110.0, pre_close=100.0)) is False

    def test_limit_down_blocks_sell(self) -> None:
        engine = _make_engine()

        assert engine.can_execute("2330.TW", 0, _make_bar(close=90.0, pre_close=100.0)) is False


class TestTaiwanStockRoundSize:
    def test_rounds_down_to_board_lots(self) -> None:
        engine = _make_engine()

        assert engine.round_size(2500.0, 100.0) == 2000
        assert engine.round_size(999.0, 100.0) == 0

    def test_negative_size_clamps_to_zero(self) -> None:
        engine = _make_engine()

        assert engine.round_size(-1000.0, 100.0) == 0


class TestTaiwanStockCommission:
    def test_buy_uses_minimum_broker_commission(self) -> None:
        engine = _make_engine()

        assert engine.calc_commission(1000.0, 10.0, 1, is_open=True) == pytest.approx(20.0)

    def test_sell_adds_transaction_tax(self) -> None:
        engine = _make_engine()
        notional = 1000.0 * 100.0

        buy_fee = engine.calc_commission(1000.0, 100.0, 1, is_open=True)
        sell_fee = engine.calc_commission(1000.0, 100.0, 1, is_open=False)

        assert sell_fee - buy_fee == pytest.approx(notional * 0.003)

    def test_leverage_is_forced_to_one(self) -> None:
        engine = _make_engine(leverage=3.0)

        assert engine.default_leverage == 1.0


class TestTaiwanStockSlippage:
    def test_buy_slippage_increases_price(self) -> None:
        engine = _make_engine(slippage=0.001)

        assert engine.apply_slippage(100.0, 1) == pytest.approx(100.1)

    def test_sell_slippage_decreases_price(self) -> None:
        engine = _make_engine(slippage=0.001)

        assert engine.apply_slippage(100.0, -1) == pytest.approx(99.9)


class TestTaiwanStockRunnerInstantiation:
    def test_runner_creates_taiwan_stock_engine(self) -> None:
        engine = _create_market_engine("shioaji", {"initial_cash": 100_000}, ["2330.TW"])

        assert isinstance(engine, TaiwanStockEngine)
