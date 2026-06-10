"""
Quant AI Agent — Market Data Provider Base Class

Abstract interface for market data providers.
All providers (yfinance, NSE, broker) implement this contract.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd


@dataclass
class Quote:
    """Real-time or near-real-time price quote."""

    symbol: str
    ltp: float                      # Last traded price
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0             # Previous close
    change: float = 0.0
    change_pct: float = 0.0
    volume: int = 0
    timestamp: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "ltp": self.ltp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "change": self.change,
            "change_pct": self.change_pct,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class OptionContract:
    """Single option contract data."""

    strike: float
    option_type: str               # CE or PE
    ltp: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    open_interest: int = 0
    oi_change: int = 0
    volume: int = 0
    iv: float = 0.0

    # Greeks (may be computed locally)
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0

    def to_dict(self) -> dict:
        return {
            "strike": self.strike,
            "option_type": self.option_type,
            "ltp": self.ltp,
            "bid": self.bid,
            "ask": self.ask,
            "open_interest": self.open_interest,
            "oi_change": self.oi_change,
            "volume": self.volume,
            "iv": self.iv,
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
        }


@dataclass
class OptionsChainData:
    """Full options chain for a symbol + expiry."""

    symbol: str
    expiry: date
    underlying_ltp: float
    contracts: list[OptionContract] = field(default_factory=list)

    # Derived metrics (computed after loading)
    total_ce_oi: int = 0
    total_pe_oi: int = 0
    pcr: float = 0.0              # Put-Call Ratio
    max_pain: float = 0.0

    def compute_derived(self) -> None:
        """Compute PCR, max pain, and OI totals from contracts."""
        self.total_ce_oi = sum(
            c.open_interest for c in self.contracts if c.option_type == "CE"
        )
        self.total_pe_oi = sum(
            c.open_interest for c in self.contracts if c.option_type == "PE"
        )
        self.pcr = (
            self.total_pe_oi / self.total_ce_oi
            if self.total_ce_oi > 0
            else 0.0
        )

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "expiry": self.expiry.isoformat(),
            "underlying_ltp": self.underlying_ltp,
            "contracts": [c.to_dict() for c in self.contracts],
            "total_ce_oi": self.total_ce_oi,
            "total_pe_oi": self.total_pe_oi,
            "pcr": round(self.pcr, 3),
            "max_pain": self.max_pain,
        }


class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    Implementations: yfinance, NSE scraper, broker API.
    """

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """Get the current/latest quote for a symbol."""
        ...

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        start: date | None = None,
        end: date | None = None,
        period: str = "1y",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data.

        Returns DataFrame with columns: [open, high, low, close, volume]
        and a DatetimeIndex.
        """
        ...

    @abstractmethod
    async def get_options_chain(
        self,
        symbol: str,
        expiry: date | None = None,
    ) -> OptionsChainData:
        """
        Get the options chain for a symbol.
        If expiry is None, returns the nearest expiry.
        """
        ...

    @abstractmethod
    async def get_expiry_dates(self, symbol: str) -> list[date]:
        """Get available expiry dates for options."""
        ...
