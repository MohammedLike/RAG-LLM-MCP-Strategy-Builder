from fastapi import APIRouter
from .routes_chat import router as chat_router
from .routes_market import router as market_router
from .routes_strategy import router as strategy_router
from .routes_backtest import router as backtest_router

api_router = APIRouter()
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(market_router, tags=["market"])
api_router.include_router(strategy_router, tags=["strategy"])
api_router.include_router(backtest_router, tags=["backtest"])
