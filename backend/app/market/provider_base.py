from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime

class MarketDataProvider(ABC):
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> dict:
        """Fetch current live price quote for symbol."""
        pass
        
    @abstractmethod
    async def get_ohlcv(self, symbol: str, interval: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        pass
        
    @abstractmethod
    async def get_options_chain(self, symbol: str, expiry: str) -> dict:
        """Fetch options chain for a given symbol and expiry."""
        pass
