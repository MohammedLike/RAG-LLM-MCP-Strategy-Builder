from fastapi import APIRouter
from .routes_chat import router as chat_router
from .routes_market import router as market_router
from .routes_strategy import router as strategy_router
from .routes_backtest import router as backtest_router
from .routes_mcp import router as mcp_router
from .routes_independent_strategy import router as independent_strategy_router
from .routes_pipeline import router as pipeline_router
from .routes_options_backtest import router as options_backtest_router

api_router = APIRouter()
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(market_router, tags=["market"])
api_router.include_router(strategy_router, tags=["strategy"])
api_router.include_router(backtest_router, tags=["backtest"])
api_router.include_router(pipeline_router, tags=["pipeline"])
api_router.include_router(options_backtest_router)
api_router.include_router(mcp_router, tags=["mcp"])
api_router.include_router(independent_strategy_router, tags=["independent-strategy"])
