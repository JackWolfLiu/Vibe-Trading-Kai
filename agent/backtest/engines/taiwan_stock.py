"""Taiwan stock backtest engine.

Market rules:
  - T+0: same-day sell is allowed
  - Price limits: ±10%
  - Minimum lot: 1,000 shares (one board lot)
  - Commission: 0.1425% bilateral, NT$20 minimum
  - Transaction tax: 0.3% sell-side only
"""

from __future__ import annotations

from typing import Final

import pandas as pd

from backtest.engines.base import BaseEngine


COMMISSION_RATE: Final[float] = 0.001425
COMMISSION_MIN: Final[float] = 20.0
TRANSACTION_TAX: Final[float] = 0.003
LOT_SIZE: Final[int] = 1000
PRICE_LIMIT: Final[float] = 0.10


class TaiwanStockEngine(BaseEngine):
    """Taiwan stock market engine for TWSE/TPEX symbols."""

    def __init__(self, config: dict):
        config = {**config, "leverage": 1.0}
        super().__init__(config)
        self.commission_rate: float = config.get("commission_rate", COMMISSION_RATE)
        self.commission_min: float = config.get("commission_min", COMMISSION_MIN)
        self.transaction_tax: float = config.get("transaction_tax", TRANSACTION_TAX)
        self.lot_size: int = config.get("lot_size", LOT_SIZE)
        self.price_limit: float = config.get("price_limit", PRICE_LIMIT)
        self.slippage_rate: float = config.get("slippage", 0.001)

    def can_execute(self, symbol: str, direction: int, bar: pd.Series) -> bool:
        """Allow T+0 Taiwan stock trades unless price limits block them."""
        pct_chg = _calc_pct_change(bar)
        if pct_chg is None:
            return True
        if direction == 1 and pct_chg >= self.price_limit:
            return False
        if direction == 0 and pct_chg <= -self.price_limit:
            return False
        return True

    def round_size(self, raw_size: float, price: float) -> float:
        """Round down to Taiwan board lots."""
        return max(int(raw_size / self.lot_size) * self.lot_size, 0)

    def calc_commission(self, size: float, price: float, _direction: int, is_open: bool) -> float:
        """Calculate broker commission plus sell-side transaction tax."""
        notional = size * price
        fee = max(notional * self.commission_rate, self.commission_min)
        if not is_open:
            fee += notional * self.transaction_tax
        return fee

    def apply_slippage(self, price: float, direction: int) -> float:
        """Apply proportional Taiwan stock slippage."""
        return price * (1 + direction * self.slippage_rate)


def _calc_pct_change(bar: pd.Series) -> float | None:
    """Calculate fractional price change from a Taiwan stock OHLC bar."""
    if "pct_chg" in bar.index:
        pct_chg = bar["pct_chg"]
        if pd.notna(pct_chg):
            return float(pct_chg) / 100.0

    close = bar.get("close")
    pre_close = bar.get("pre_close")
    if close is not None and pre_close is not None and pre_close > 0:
        return (float(close) - float(pre_close)) / float(pre_close)
    return None
