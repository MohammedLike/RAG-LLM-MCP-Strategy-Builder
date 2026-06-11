import os
import csv
from fastapi import APIRouter
from ..mcp.tool_fetch_market import fetch_market_data, FetchMarketInput

router = APIRouter()

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../company_profiles.csv"))

@router.get("/market/companies")
async def get_companies():
    """Returns all available companies and indices from company_profiles.csv."""
    companies = []
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    companies.append({
                        "symbol": row.get("ticker"),
                        "name": row.get("name"),
                        "sector": row.get("sector") or "Index/General",
                        "industry": row.get("industry") or "General"
                    })
        except Exception as e:
            print(f"Error loading companies CSV: {e}")
            
    # Default fallback list if CSV has issues
    if not companies:
        companies = [
            {"symbol": "NIFTY", "name": "Nifty 50 Index", "sector": "Index", "industry": "Index"},
            {"symbol": "BANKNIFTY", "name": "Nifty Bank Index", "sector": "Index", "industry": "Banking"},
            {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "sector": "Energy", "industry": "Oil & Gas"},
            {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "sector": "Technology", "industry": "IT Services"},
            {"symbol": "INFY", "name": "Infosys Ltd", "sector": "Technology", "industry": "IT Services"},
            {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "sector": "Financial Services", "industry": "Banking"},
        ]
    return companies


@router.get("/market/{symbol}/quote")
async def get_quote(symbol: str):
    return await fetch_market_data(FetchMarketInput(symbol=symbol, data_type="quote"))

@router.get("/market/{symbol}/ohlcv")
async def get_ohlcv(symbol: str):
    return await fetch_market_data(FetchMarketInput(symbol=symbol, data_type="ohlcv"))

@router.get("/market/{symbol}/options")
async def get_options(symbol: str, expiry: str = None):
    return await fetch_market_data(FetchMarketInput(symbol=symbol, data_type="options_chain", expiry=expiry))

@router.websocket("/ws/market")
async def websocket_market(websocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Market update for {data}")
