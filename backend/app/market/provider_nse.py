import requests
import pandas as pd
from datetime import datetime
from .provider_base import MarketDataProvider
import asyncio
from typing import Optional, Dict, Any

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
            # Handle index vs equity
            if symbol in ["NIFTY", "BANKNIFTY"]:
                url = f"{self.base_url}/api/allIndices"
                res = self.session.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    index_data = next((item for item in data['data'] if item["index"] == (symbol + " 50" if symbol == "NIFTY" else symbol)), {})
                    return {
                        "symbol": symbol,
                        "ltp": index_data.get("lastPrice", 0),
                        "change": index_data.get("pChange", 0),
                        "timestamp": datetime.utcnow().isoformat(),
                        "provider": "nse"
                    }
            else:
                url = f"{self.base_url}/api/quote-equity?symbol={symbol}"
                res = self.session.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "symbol": symbol,
                        "ltp": data.get("priceInfo", {}).get("lastPrice", 0),
                        "change": data.get("priceInfo", {}).get("pChange", 0),
                        "timestamp": datetime.utcnow().isoformat(),
                        "provider": "nse"
                    }
            return {}
        return await asyncio.to_thread(_fetch)

    async def get_ohlcv(self, symbol: str, interval: str, start: datetime, end: datetime) -> pd.DataFrame:
        raise NotImplementedError("Use YFinanceProvider for historical OHLCV data")

    async def get_options_chain(self, symbol: str, expiry: str = None) -> dict:
        def _fetch():
            type_str = "indices" if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY"] else "equities"
            url = f"{self.base_url}/api/option-chain-{type_str}?symbol={symbol}"
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"error": f"Failed to fetch options chain: {res.status_code}"}
        return await asyncio.to_thread(_fetch)

    async def get_futures_data(self, symbol: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        def _fetch():
            # Futures data usually comes from the derivative quote endpoint
            url = f"{self.base_url}/api/quote-derivative?symbol={symbol}"
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # Filter for futures
                futures = [item for item in data.get("stocks", []) if item.get("metadata", {}).get("instrumentType") == "Stock Futures" or "Index Futures" in item.get("metadata", {}).get("instrumentType", "")]
                return {"symbol": symbol, "futures": futures}
            return {"error": f"Failed to fetch futures data: {res.status_code}"}
        return await asyncio.to_thread(_fetch)

    async def get_equity_meta(self, symbol: str) -> Dict[str, Any]:
        def _fetch():
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}"
            res = self.session.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return data.get("metadata", {})
            return {}
        return await asyncio.to_thread(_fetch)
