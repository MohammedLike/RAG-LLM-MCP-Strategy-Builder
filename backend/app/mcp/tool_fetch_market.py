from typing import Optional
from pydantic import BaseModel, Field
import asyncio
from ..market.provider_nse import NSEProvider

nse_provider = NSEProvider()

class FetchMarketInput(BaseModel):
    symbol: str = Field(description="The symbol to fetch data for, e.g., 'NIFTY', 'RELIANCE', or 'BANKNIFTY'")
    data_type: str = Field(description="The type of data to fetch: 'quote', 'ohlcv', 'options_chain', 'futures', 'equity_meta'")
    expiry: Optional[str] = Field(None, description="The expiry date for options/futures, format YYYY-MM-DD")

async def fetch_market_data(input_data: FetchMarketInput) -> dict:
    """
    Fetches real-time or historical market data for Equity, Futures, and Options.
    """
    try:
        if input_data.data_type == "quote":
            return await nse_provider.get_quote(input_data.symbol)
        
        elif input_data.data_type == "options_chain":
            return await nse_provider.get_options_chain(input_data.symbol, input_data.expiry)
            
        elif input_data.data_type == "futures":
            return await nse_provider.get_futures_data(input_data.symbol, input_data.expiry)
            
        elif input_data.data_type == "equity_meta":
            return await nse_provider.get_equity_meta(input_data.symbol)
            
        elif input_data.data_type == "ohlcv":
            # For now returning mock or calling yfinance if implemented
            return {
                "symbol": input_data.symbol,
                "note": "Historical data currently available via historical provider.",
                "data": []
            }
            
        return {"error": "Invalid data_type"}
    except Exception as e:
        return {"error": str(e)}

# Wrapper for synchronous execution if needed by the tool caller
def fetch_market_data_sync(input_data: FetchMarketInput) -> dict:
    return asyncio.run(fetch_market_data(input_data))
