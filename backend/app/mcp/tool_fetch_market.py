from typing import Optional
from pydantic import BaseModel, Field

class FetchMarketInput(BaseModel):
    symbol: str = Field(description="The symbol to fetch data for, e.g., 'NIFTY' or 'BANKNIFTY'")
    data_type: str = Field(description="The type of data to fetch: 'quote', 'ohlcv', or 'options_chain'")
    expiry: Optional[str] = Field(None, description="The expiry date for options chain, format YYYY-MM-DD")

def fetch_market_data(input_data: FetchMarketInput) -> dict:
    """
    Simulates fetching market data to return quote, ohlcv, or options_chain.
    In a complete implementation, this would call provider_base implementations.
    """
    if input_data.data_type == "quote":
        return {
            "symbol": input_data.symbol,
            "ltp": 22000.50 if input_data.symbol == "NIFTY" else 46000.00,
            "change": 0.5,
            "iv": 14.2
        }
    elif input_data.data_type == "ohlcv":
        return {
            "symbol": input_data.symbol,
            "data": [
                {"date": "2026-06-09", "close": 21900},
                {"date": "2026-06-10", "close": 22000.50}
            ]
        }
    elif input_data.data_type == "options_chain":
        return {
            "symbol": input_data.symbol,
            "expiry": input_data.expiry,
            "chain": []
        }
    return {"error": "Invalid data_type"}
