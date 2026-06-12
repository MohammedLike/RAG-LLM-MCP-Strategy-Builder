import yfinance as yf
import pandas as pd
from datetime import datetime
from .provider_base import MarketDataProvider
import asyncio

class YFinanceProvider(MarketDataProvider):
    
    # Mapping for common Indian indices
    SYMBOL_MAP = {
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "FINNIFTY": "CNXFIN.NS",
        "SENSEX": "^BSESN",
        "NIFTY100": "^CNX100",
        "NIFTY500": "^CRSLDX"
    }

    def _get_ticker(self, symbol: str) -> str:
        symbol = symbol.upper()
        if symbol in self.SYMBOL_MAP:
            return self.SYMBOL_MAP[symbol]
        
        # If user explicitly provided suffix
        if symbol.endswith(".NS") or symbol.endswith(".BO") or symbol.startswith("^"):
            return symbol
            
        # Default to NSE
        return f"{symbol}.NS"

    async def get_quote(self, symbol: str) -> dict:
        ticker = self._get_ticker(symbol)
        def _fetch():
            t = yf.Ticker(ticker)
            info = t.fast_info
            return {
                "symbol": symbol,
                "ltp": info.last_price,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "yfinance"
            }
        return await asyncio.to_thread(_fetch)

    async def get_ohlcv(self, symbol: str, interval: str, start: datetime, end: datetime) -> pd.DataFrame:
        ticker = self._get_ticker(symbol)
        def _fetch():
            return yf.download(ticker, start=start, end=end, interval=interval)
        
        df = await asyncio.to_thread(_fetch)
        
        # Format columns properly
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df.reset_index()
        # The index column is typically 'Date' or 'Datetime', but let's be explicit
        df = df.rename(columns={df.columns[0]: 'time'})
        
        # Ensure remaining column names match our schema lowercase
        df.columns = [c.lower() for c in df.columns]
        df['symbol'] = symbol
        return df

    async def get_options_chain(self, symbol: str, expiry: str) -> dict:
        return {"error": "Options chain not fully supported via yfinance for NSE"}

    async def get_futures_data(self, symbol: str, expiry: str | None = None) -> dict:
        ticker = self._get_ticker(symbol)
        def _fetch():
            t = yf.Ticker(ticker)
            info = t.fast_info
            return {
                "symbol": symbol,
                "ltp": info.last_price,
                "expiry": expiry,
                "provider": "yfinance",
            }
        return await asyncio.to_thread(_fetch)

    async def get_equity_meta(self, symbol: str) -> dict:
        ticker = self._get_ticker(symbol)
        def _fetch():
            t = yf.Ticker(ticker)
            info = t.info
            return {
                "symbol": symbol,
                "name": info.get("shortName") or info.get("longName"),
                "exchange": info.get("exchange"),
                "currency": info.get("currency"),
                "provider": "yfinance",
            }
        return await asyncio.to_thread(_fetch)
