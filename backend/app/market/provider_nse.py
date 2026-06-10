"""
Quant AI Agent — NSE Market Data Provider

Fetches live data from NSE India website.
Uses browser-like headers and session management to handle NSE's anti-bot measures.

WARNING: NSE does not provide an official REST API. This scrapes the website's
internal endpoints. It may break if NSE changes their frontend. Use yfinance
as the primary fallback.
"""

import asyncio
from datetime import date, datetime
from functools import partial

import pandas as pd
import requests

from app.market.provider_base import (
    MarketDataProvider,
    OptionContract,
    OptionsChainData,
    Quote,
)

# NSE website endpoints
NSE_BASE = "https://www.nseindia.com"
NSE_QUOTE_API = "https://www.nseindia.com/api/quote-equity"
NSE_INDEX_API = "https://www.nseindia.com/api/allIndices"
NSE_OPTIONS_API = "https://www.nseindia.com/api/option-chain-indices"
NSE_EQUITY_OPTIONS_API = "https://www.nseindia.com/api/option-chain-equities"

# Browser-like headers to bypass anti-bot
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

# Index symbols that use the index API
INDEX_SYMBOLS = {"NIFTY", "NIFTY50", "NIFTY 50", "BANKNIFTY", "BANK NIFTY", "FINNIFTY"}


class NSESession:
    """
    Manages a persistent HTTP session with NSE.
    Handles cookie acquisition and rotation.
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._cookie_initialized = False

    def _ensure_cookies(self) -> None:
        """Visit NSE homepage to acquire session cookies."""
        if not self._cookie_initialized:
            try:
                self._session.get(NSE_BASE, timeout=10)
                self._cookie_initialized = True
            except requests.RequestException:
                pass

    def get(self, url: str, params: dict | None = None) -> dict:
        """Make a GET request to NSE API with retry."""
        self._ensure_cookies()

        for attempt in range(3):
            try:
                resp = self._session.get(url, params=params, timeout=15)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 401:
                    # Cookie expired — refresh
                    self._cookie_initialized = False
                    self._ensure_cookies()
            except (requests.RequestException, ValueError):
                if attempt < 2:
                    import time
                    time.sleep(1 * (attempt + 1))

        return {}


# Global session instance
_nse_session = NSESession()


class NSEProvider(MarketDataProvider):
    """
    Market data provider using NSE India website.

    Pros: Real-time data, options chain with OI, no cost
    Cons: Rate limited, may break if NSE changes frontend, requires cookie management
    """

    def __init__(self) -> None:
        self._session = _nse_session

    async def get_quote(self, symbol: str) -> Quote:
        """Get live quote from NSE."""
        symbol_upper = symbol.upper().strip()
        loop = asyncio.get_event_loop()

        if symbol_upper in INDEX_SYMBOLS:
            return await self._get_index_quote(symbol_upper, loop)
        else:
            return await self._get_equity_quote(symbol_upper, loop)

    async def _get_index_quote(
        self, symbol: str, loop: asyncio.AbstractEventLoop
    ) -> Quote:
        """Get index quote (Nifty, BankNifty)."""
        data = await loop.run_in_executor(
            None, partial(self._session.get, NSE_INDEX_API)
        )

        # Map symbol to NSE index name
        index_name_map = {
            "NIFTY": "NIFTY 50",
            "NIFTY50": "NIFTY 50",
            "NIFTY 50": "NIFTY 50",
            "BANKNIFTY": "NIFTY BANK",
            "BANK NIFTY": "NIFTY BANK",
            "FINNIFTY": "NIFTY FINANCIAL SERVICES",
        }
        target_name = index_name_map.get(symbol, symbol)

        for idx in data.get("data", []):
            if idx.get("index") == target_name:
                ltp = float(idx.get("last", 0))
                prev = float(idx.get("previousClose", 0))
                return Quote(
                    symbol=symbol,
                    ltp=ltp,
                    open=float(idx.get("open", 0)),
                    high=float(idx.get("high", 0)),
                    low=float(idx.get("low", 0)),
                    close=prev,
                    change=ltp - prev,
                    change_pct=float(idx.get("percentChange", 0)),
                    timestamp=datetime.now(),
                )

        return Quote(symbol=symbol, ltp=0)

    async def _get_equity_quote(
        self, symbol: str, loop: asyncio.AbstractEventLoop
    ) -> Quote:
        """Get equity quote for individual stocks."""
        data = await loop.run_in_executor(
            None,
            partial(self._session.get, NSE_QUOTE_API, {"symbol": symbol}),
        )

        price_info = data.get("priceInfo", {})
        ltp = float(price_info.get("lastPrice", 0))
        prev = float(price_info.get("previousClose", 0))

        return Quote(
            symbol=symbol,
            ltp=ltp,
            open=float(price_info.get("open", 0)),
            high=float(price_info.get("intraDayHighLow", {}).get("max", 0)),
            low=float(price_info.get("intraDayHighLow", {}).get("min", 0)),
            close=prev,
            change=float(price_info.get("change", 0)),
            change_pct=float(price_info.get("pChange", 0)),
            volume=int(
                data.get("securityWiseDP", {}).get("quantityTraded", 0) or 0
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
        NSE doesn't provide historical OHLCV via API.
        Falls back to yfinance for historical data.
        """
        from app.market.provider_yfinance import YFinanceProvider

        fallback = YFinanceProvider()
        return await fallback.get_ohlcv(symbol, interval, start, end, period)

    async def get_options_chain(
        self,
        symbol: str,
        expiry: date | None = None,
    ) -> OptionsChainData:
        """Get full options chain from NSE."""
        symbol_upper = symbol.upper().strip()
        loop = asyncio.get_event_loop()

        # Choose endpoint based on index vs equity
        if symbol_upper in INDEX_SYMBOLS:
            url = NSE_OPTIONS_API
            api_symbol_map = {
                "NIFTY": "NIFTY",
                "NIFTY50": "NIFTY",
                "NIFTY 50": "NIFTY",
                "BANKNIFTY": "BANKNIFTY",
                "BANK NIFTY": "BANKNIFTY",
                "FINNIFTY": "FINNIFTY",
            }
            api_symbol = api_symbol_map.get(symbol_upper, symbol_upper)
        else:
            url = NSE_EQUITY_OPTIONS_API
            api_symbol = symbol_upper

        data = await loop.run_in_executor(
            None,
            partial(self._session.get, url, {"symbol": api_symbol}),
        )

        if not data:
            return OptionsChainData(
                symbol=symbol_upper,
                expiry=expiry or date.today(),
                underlying_ltp=0,
                contracts=[],
            )

        # Parse response
        records = data.get("records", {})
        underlying_ltp = float(records.get("underlyingValue", 0))
        expiry_dates_raw = records.get("expiryDates", [])

        # Filter by requested expiry
        target_expiry = None
        if expiry:
            target_expiry = expiry.strftime("%d-%b-%Y")
        elif expiry_dates_raw:
            target_expiry = expiry_dates_raw[0]  # Nearest

        contracts: list[OptionContract] = []
        for row in records.get("data", []):
            row_expiry = row.get("expiryDate", "")
            if target_expiry and row_expiry != target_expiry:
                continue

            # Parse CE
            ce = row.get("CE")
            if ce:
                contracts.append(
                    OptionContract(
                        strike=float(ce.get("strikePrice", 0)),
                        option_type="CE",
                        ltp=float(ce.get("lastPrice", 0)),
                        bid=float(ce.get("bidprice", 0)),
                        ask=float(ce.get("askPrice", 0)),
                        open_interest=int(ce.get("openInterest", 0)),
                        oi_change=int(ce.get("changeinOpenInterest", 0)),
                        volume=int(ce.get("totalTradedVolume", 0)),
                        iv=float(ce.get("impliedVolatility", 0)),
                    )
                )

            # Parse PE
            pe = row.get("PE")
            if pe:
                contracts.append(
                    OptionContract(
                        strike=float(pe.get("strikePrice", 0)),
                        option_type="PE",
                        ltp=float(pe.get("lastPrice", 0)),
                        bid=float(pe.get("bidprice", 0)),
                        ask=float(pe.get("askPrice", 0)),
                        open_interest=int(pe.get("openInterest", 0)),
                        oi_change=int(pe.get("changeinOpenInterest", 0)),
                        volume=int(pe.get("totalTradedVolume", 0)),
                        iv=float(pe.get("impliedVolatility", 0)),
                    )
                )

        # Parse expiry date
        parsed_expiry = expiry or date.today()
        if target_expiry:
            try:
                parsed_expiry = datetime.strptime(
                    target_expiry, "%d-%b-%Y"
                ).date()
            except ValueError:
                pass

        result = OptionsChainData(
            symbol=symbol_upper,
            expiry=parsed_expiry,
            underlying_ltp=underlying_ltp,
            contracts=contracts,
        )
        result.compute_derived()
        return result

    async def get_expiry_dates(self, symbol: str) -> list[date]:
        """Get available option expiry dates from NSE."""
        symbol_upper = symbol.upper().strip()
        loop = asyncio.get_event_loop()

        if symbol_upper in INDEX_SYMBOLS:
            url = NSE_OPTIONS_API
            api_symbol = {
                "NIFTY": "NIFTY", "NIFTY50": "NIFTY", "NIFTY 50": "NIFTY",
                "BANKNIFTY": "BANKNIFTY", "BANK NIFTY": "BANKNIFTY",
            }.get(symbol_upper, symbol_upper)
        else:
            url = NSE_EQUITY_OPTIONS_API
            api_symbol = symbol_upper

        data = await loop.run_in_executor(
            None,
            partial(self._session.get, url, {"symbol": api_symbol}),
        )

        expiry_dates_raw = data.get("records", {}).get("expiryDates", [])
        result = []
        for d in expiry_dates_raw:
            try:
                result.append(datetime.strptime(d, "%d-%b-%Y").date())
            except ValueError:
                continue
        return result
