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
        "SENSEX": "^BSESN"
    }

    def _get_ticker(self, symbol: str) -> str:
        return self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}.NS")

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
        
        # Format columns properly (yf.download returns MultiIndex columns sometimes)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df.reset_index()
        # Ensure column names match our schema lowercase
        df.columns = [c.lower() if c != 'Date' and c != 'Datetime' else 'time' for c in df.columns]
        df['symbol'] = symbol
        return df

    async def get_options_chain(self, symbol: str, expiry: str) -> dict:
        # yfinance doesn't natively support NSE options chain easily,
        # but this provides a placeholder/fallback interface
        return {"error": "Options chain not fully supported via yfinance for NSE"}
