from fastapi import APIRouter
from ..mcp.tool_fetch_market import fetch_market_data, FetchMarketInput

router = APIRouter()

@router.get("/market/{symbol}/quote")
async def get_quote(symbol: str):
    return fetch_market_data(FetchMarketInput(symbol=symbol, data_type="quote"))

@router.get("/market/{symbol}/ohlcv")
async def get_ohlcv(symbol: str):
    return fetch_market_data(FetchMarketInput(symbol=symbol, data_type="ohlcv"))

@router.get("/market/{symbol}/options")
async def get_options(symbol: str, expiry: str = None):
    return fetch_market_data(FetchMarketInput(symbol=symbol, data_type="options_chain", expiry=expiry))

@router.websocket("/ws/market")
async def websocket_market(websocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Market update for {data}")
