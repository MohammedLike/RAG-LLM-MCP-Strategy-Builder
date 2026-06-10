import requests
import pandas as pd
from datetime import datetime
from .provider_base import MarketDataProvider
import asyncio

class NSEProvider(MarketDataProvider):
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._init_session()

    def _init_session(self):
        # Visit home page to get cookies
        try:
            self.session.get(self.base_url, timeout=5)
        except Exception as e:
            print(f"Failed to initialize NSE session: {e}")

    async def get_quote(self, symbol: str) -> dict:
        def _fetch():
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}"
            # For indices: /api/allIndices
            res = self.session.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return {
                    "symbol": symbol,
                    "ltp": data.get("priceInfo", {}).get("lastPrice", 0),
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider": "nse"
                }
            return {}
        return await asyncio.to_thread(_fetch)

    async def get_ohlcv(self, symbol: str, interval: str, start: datetime, end: datetime) -> pd.DataFrame:
        # Implementing NSE historical data requires complex API endpoints or scraping.
        # Fallback to yfinance is recommended for historical.
        raise NotImplementedError("Use YFinanceProvider for historical OHLCV data")

    async def get_options_chain(self, symbol: str, expiry: str = None) -> dict:
        def _fetch():
            url = f"{self.base_url}/api/option-chain-indices?symbol={symbol}"
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"error": f"Failed to fetch options chain: {res.status_code}"}
        return await asyncio.to_thread(_fetch)
