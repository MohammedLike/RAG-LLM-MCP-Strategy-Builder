"""
Quant AI Agent — yfinance Market Data Provider

Reliable fallback provider for historical OHLCV data.
Maps NSE symbols to yfinance tickers.
Note: Indian market data on yfinance may be 15-min delayed.
"""

import asyncio
from datetime import date, datetime
from functools import partial

import pandas as pd
import yfinance as yf

from app.market.provider_base import (
    MarketDataProvider,
    OptionContract,
    OptionsChainData,
    Quote,
)

# ── Symbol mapping: NSE common names → yfinance tickers ──
SYMBOL_MAP: dict[str, str] = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "BANK NIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "SENSEX": "^BSESN",
    "MIDCPNIFTY": "^NSEMDCP50",
    # Individual stocks — add as needed
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "LT": "LT.NS",
}


def _resolve_ticker(symbol: str) -> str:
    """Resolve an NSE symbol to a yfinance ticker."""
    symbol_upper = symbol.upper().strip()
    if symbol_upper in SYMBOL_MAP:
        return SYMBOL_MAP[symbol_upper]
    # If not in map, assume it's an NSE stock
    if not symbol_upper.endswith(".NS") and not symbol_upper.startswith("^"):
        return f"{symbol_upper}.NS"
    return symbol_upper


class YFinanceProvider(MarketDataProvider):
    """
    Market data provider using yfinance.

    Pros: Reliable, free, good historical data
    Cons: 15-min delayed for Indian markets, no real-time options chain
    """

    async def get_quote(self, symbol: str) -> Quote:
        """Get the latest quote from yfinance."""
        ticker_str = _resolve_ticker(symbol)

        # yfinance is synchronous — run in executor
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, ticker_str)
        info = await loop.run_in_executor(None, lambda: ticker.fast_info)

        # Get today's OHLCV for intraday data
        hist = await loop.run_in_executor(
            None, partial(ticker.history, period="1d")
        )

        ltp = float(info.get("lastPrice", 0) or info.get("previousClose", 0))
        prev_close = float(info.get("previousClose", 0))

        if not hist.empty:
            latest = hist.iloc[-1]
            return Quote(
                symbol=symbol.upper(),
                ltp=float(latest["Close"]),
                open=float(latest["Open"]),
                high=float(latest["High"]),
                low=float(latest["Low"]),
                close=prev_close,
                change=float(latest["Close"]) - prev_close,
                change_pct=(
                    ((float(latest["Close"]) - prev_close) / prev_close * 100)
                    if prev_close
                    else 0
                ),
                volume=int(latest.get("Volume", 0)),
                timestamp=datetime.now(),
            )

        return Quote(
            symbol=symbol.upper(),
            ltp=ltp,
            close=prev_close,
            change=ltp - prev_close,
            change_pct=(
                ((ltp - prev_close) / prev_close * 100) if prev_close else 0
            ),
            timestamp=datetime.now(),
        )

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        start: date | None = None,
        end: date | None = None,
        period: str = "1y",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data from yfinance.

        Returns DataFrame with columns: [open, high, low, close, volume]
        """
        ticker_str = _resolve_ticker(symbol)

        # Map interval formats
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "1d": "1d",
            "1wk": "1wk", "1mo": "1mo",
        }
        yf_interval = interval_map.get(interval, interval)

        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, ticker_str)

        if start and end:
            hist = await loop.run_in_executor(
                None,
                partial(
                    ticker.history,
                    start=start.isoformat(),
                    end=end.isoformat(),
                    interval=yf_interval,
                ),
            )
        else:
            hist = await loop.run_in_executor(
                None,
                partial(ticker.history, period=period, interval=yf_interval),
            )

        if hist.empty:
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"]
            )

        # Normalize column names to lowercase
        hist.columns = [c.lower() for c in hist.columns]

        # Keep only OHLCV columns
        ohlcv_cols = ["open", "high", "low", "close", "volume"]
        available_cols = [c for c in ohlcv_cols if c in hist.columns]
        return hist[available_cols]

    async def get_options_chain(
        self,
        symbol: str,
        expiry: date | None = None,
    ) -> OptionsChainData:
        """
        Get options chain from yfinance.

        Note: yfinance options data is primarily for US markets.
        For NSE options, this will have limited data. Use NSE provider instead.
        """
        ticker_str = _resolve_ticker(symbol)

        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, ticker_str)

        # Get available expiries
        try:
            expiry_dates = await loop.run_in_executor(
                None, lambda: ticker.options
            )
        except Exception:
            return OptionsChainData(
                symbol=symbol.upper(),
                expiry=expiry or date.today(),
                underlying_ltp=0,
                contracts=[],
            )

        if not expiry_dates:
            return OptionsChainData(
                symbol=symbol.upper(),
                expiry=expiry or date.today(),
                underlying_ltp=0,
                contracts=[],
            )

        # Select expiry
        if expiry:
            target_expiry = expiry.isoformat()
        else:
            target_expiry = expiry_dates[0]  # Nearest expiry

        # Get chain
        try:
            chain = await loop.run_in_executor(
                None, partial(ticker.option_chain, target_expiry)
            )
        except Exception:
            return OptionsChainData(
                symbol=symbol.upper(),
                expiry=date.fromisoformat(target_expiry),
                underlying_ltp=0,
                contracts=[],
            )

        # Get current price for the underlying
        quote = await self.get_quote(symbol)
        contracts: list[OptionContract] = []

        # Parse calls
        if chain.calls is not None and not chain.calls.empty:
            for _, row in chain.calls.iterrows():
                contracts.append(
                    OptionContract(
                        strike=float(row.get("strike", 0)),
                        option_type="CE",
                        ltp=float(row.get("lastPrice", 0)),
                        bid=float(row.get("bid", 0)),
                        ask=float(row.get("ask", 0)),
                        open_interest=int(row.get("openInterest", 0)),
                        volume=int(row.get("volume", 0) or 0),
                        iv=float(row.get("impliedVolatility", 0)) * 100,
                    )
                )

        # Parse puts
        if chain.puts is not None and not chain.puts.empty:
            for _, row in chain.puts.iterrows():
                contracts.append(
                    OptionContract(
                        strike=float(row.get("strike", 0)),
                        option_type="PE",
                        ltp=float(row.get("lastPrice", 0)),
                        bid=float(row.get("bid", 0)),
                        ask=float(row.get("ask", 0)),
                        open_interest=int(row.get("openInterest", 0)),
                        volume=int(row.get("volume", 0) or 0),
                        iv=float(row.get("impliedVolatility", 0)) * 100,
                    )
                )

        result = OptionsChainData(
            symbol=symbol.upper(),
            expiry=date.fromisoformat(target_expiry),
            underlying_ltp=quote.ltp,
            contracts=contracts,
        )
        result.compute_derived()
        return result

    async def get_expiry_dates(self, symbol: str) -> list[date]:
        """Get available expiry dates for options."""
        ticker_str = _resolve_ticker(symbol)

        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, ticker_str)

        try:
            expiry_dates = await loop.run_in_executor(
                None, lambda: ticker.options
            )
            return [date.fromisoformat(d) for d in expiry_dates]
        except Exception:
            return []
