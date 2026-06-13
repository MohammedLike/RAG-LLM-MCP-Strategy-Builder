import json
import glob
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from app.db.session import async_session, is_db_available
from app.strategies.compiler import compile_db_strategy
from app.strategies.suggestions import build_prebuilt_catalog, filter_catalog
from app.backtest.engine import BacktestEngine
from app.backtest.metrics import compute_monthly_returns_by_year
from app.market.provider_yfinance import YFinanceProvider

router = APIRouter()

STRATEGIES_DIR = os.environ.get(
    "STRATEGIES_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../training/data/strategies")),
)

EXCLUDED_CATEGORIES = {"Options", "Indicator Based", "Fundamental"}

engine = BacktestEngine()
provider = YFinanceProvider()


class StrategyCreate(BaseModel):
    name: str
    category: str
    rules: dict


class StrategyBacktestRequest(BaseModel):
    symbol: str = "NIFTY"
    period: str = "2y"


def _parse_backtest_results(raw) -> dict:
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return raw if isinstance(raw, dict) else {}


def _is_equity_strategy(category: str, backtest_spec: dict) -> bool:
    if category in EXCLUDED_CATEGORIES:
        return False
    instrument = (backtest_spec or {}).get("instrument_type", "EQUITY").upper()
    return instrument != "OPTION"


def _serialize_strategy_row(row, include_full_results: bool = False) -> dict:
    db_strat = {
        "name": row[0],
        "slug": row[1],
        "category": row[2],
        "hypothesis": row[3],
        "entry_rules": row[4],
        "exit_rules": row[5],
        "risk_params": row[6],
    }
    backtest_spec = compile_db_strategy(db_strat)
    if not _is_equity_strategy(row[2], backtest_spec):
        return None

    stored_results = _parse_backtest_results(row[7] if len(row) > 7 else None)
    description = row[3] or f"Equity strategy using {row[2]} rules on NSE index/stock data."

    payload = {
        "name": row[0],
        "slug": row[1],
        "category": row[2],
        "description": description,
        "hypothesis": row[3],
        "tags": [row[2], "Equity"],
        "backtest_spec": backtest_spec,
        "entry_rules": db_strat["entry_rules"],
        "exit_rules": db_strat["exit_rules"],
        "risk_params": db_strat["risk_params"],
        "backtest_results": stored_results,
    }

    if include_full_results and stored_results:
        payload["backtest_results"] = stored_results
    elif stored_results:
        summary_keys = (
            "total_return",
            "win_rate",
            "sharpe",
            "sortino",
            "max_drawdown",
            "cagr",
            "profit_factor",
            "total_trades",
            "symbol",
            "period",
            "source",
            "backtested_at",
            "monthly_returns",
        )
        payload["backtest_results"] = {
            k: stored_results[k] for k in summary_keys if k in stored_results
        }
        monthly = stored_results.get("monthly_returns")
        if not monthly and stored_results.get("equity_curve"):
            monthly = compute_monthly_returns_by_year(stored_results["equity_curve"])
            if monthly:
                payload["backtest_results"]["monthly_returns"] = monthly
        if stored_results.get("equity_curve") and include_full_results:
            payload["backtest_results"]["equity_curve"] = stored_results["equity_curve"]

    return payload


def _load_strategies():
    strategies = []
    for path in glob.glob(f"{STRATEGIES_DIR}/**/*.json", recursive=True):
        if "_schema" in path:
            continue
        try:
            with open(path, "r") as f:
                data = json.load(f)

            file_slug = os.path.basename(path).replace(".json", "")
            slug = data.get("slug") or file_slug
            category = data.get("category", "General")
            if category in EXCLUDED_CATEGORIES:
                continue

            logic = data.get("logic", {})
            entry_rules = data.get("entry_rules") or logic.get("entry", {})
            exit_rules = data.get("exit_rules") or logic.get("exit", {})

            backtest_spec = data.get("backtest_spec") or {
                "entry": entry_rules,
                "exit": exit_rules,
                "stop_loss": exit_rules.get("stop_loss"),
                "take_profit": exit_rules.get("target") or exit_rules.get("take_profit"),
                "instrument_type": "EQUITY",
            }

            if not _is_equity_strategy(category, backtest_spec):
                continue

            strategies.append({
                "name": data.get("name") or file_slug.replace("_", " ").title(),
                "slug": slug,
                "category": category,
                "description": data.get("description") or data.get("hypothesis", ""),
                "hypothesis": data.get("hypothesis") or data.get("description", ""),
                "tags": data.get("tags") or [category, "Equity"],
                "backtest_results": data.get("backtest_results", {}),
                "backtest_spec": backtest_spec,
                "entry_rules": entry_rules,
                "exit_rules": exit_rules,
            })
        except Exception as e:
            print(f"Error loading strategy file {path}: {e}")
    return strategies


async def _run_and_store_backtest(slug: str, symbol: str, period: str) -> dict:
    if not is_db_available():
        raise HTTPException(status_code=503, detail="Database unavailable")

    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, backtest_results "
                "FROM strategies WHERE slug = :slug"
            ),
            {"slug": slug},
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Strategy not found")

        strategy = _serialize_strategy_row(row, include_full_results=True)
        if not strategy:
            raise HTTPException(status_code=400, detail="Strategy is not an equity strategy")

        days_map = {"1y": 365, "2y": 730, "5y": 1825, "8y": 2920, "6m": 180, "3y": 1095}
        days = days_map.get(period, 730)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        spec = {**strategy["backtest_spec"], "symbol": symbol, "instrument_type": "EQUITY"}
        df = await provider.get_ohlcv(symbol, "1d", start_date, end_date)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No OHLCV data in database for {symbol}")

        bt_result = engine.run(df, spec)
        equity_curve = bt_result.get("equity_curve", [])
        monthly_returns = compute_monthly_returns_by_year(equity_curve)
        stored = {
            "source": "live_backtest",
            "backtested_at": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "period": period,
            "total_return": bt_result.get("total_return"),
            "win_rate": bt_result.get("win_rate"),
            "sharpe": bt_result.get("sharpe"),
            "sortino": bt_result.get("sortino"),
            "max_drawdown": bt_result.get("max_drawdown"),
            "cagr": bt_result.get("cagr"),
            "profit_factor": bt_result.get("profit_factor"),
            "expectancy": bt_result.get("expectancy"),
            "total_trades": len(bt_result.get("trades", [])),
            "equity_curve": equity_curve,
            "monthly_returns": monthly_returns,
            "drawdown": bt_result.get("drawdown", []),
        }

        await session.execute(
            text("UPDATE strategies SET backtest_results = :results WHERE slug = :slug"),
            {"results": json.dumps(stored), "slug": slug},
        )
        await session.commit()

        return {**strategy, "backtest_results": stored, "live_result": bt_result}


@router.get("/strategies")
async def list_strategies(
    category: str = None,
    equity_only: bool = Query(default=True),
    q: str = Query(default=None, description="Search name or description"),
):
    db_strategies = []

    if is_db_available():
        try:
            async with async_session() as session:
                query = (
                    "SELECT name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, backtest_results "
                    "FROM strategies"
                )
                params = {}
                conditions = []

                if category:
                    conditions.append("category = :category")
                    params["category"] = category

                if equity_only:
                    conditions.append("category NOT IN ('Options', 'Indicator Based', 'Fundamental')")

                if q:
                    conditions.append("(LOWER(name) LIKE :q OR LOWER(hypothesis) LIKE :q OR LOWER(category) LIKE :q)")
                    params["q"] = f"%{q.lower()}%"

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY name ASC"

                result = await session.execute(text(query), params)
                rows = result.fetchall()
                for row in rows:
                    try:
                        item = _serialize_strategy_row(row)
                        if item:
                            db_strategies.append(item)
                    except Exception as e:
                        print(f"Error compiling DB strategy {row[1]}: {e}")
        except Exception as e:
            print(f"Error loading strategies from database: {e}")

    if not db_strategies:
        file_strategies = _load_strategies()
        if category:
            file_strategies = [s for s in file_strategies if s.get("category", "").lower() == category.lower()]
        if q:
            q_lower = q.lower()
            file_strategies = [
                s for s in file_strategies
                if q_lower in s.get("name", "").lower()
                or q_lower in (s.get("description") or "").lower()
                or q_lower in s.get("category", "").lower()
            ]
        return file_strategies

    return db_strategies


@router.get("/strategies/prebuilt/catalog")
async def get_prebuilt_catalog(
    q: str | None = Query(default=None, description="Search name or condition"),
    indicator: str | None = Query(default=None, description="Filter by indicator id e.g. RSI, SMA"),
    direction: str | None = Query(default=None, description="bullish, bearish, or all"),
    category: str | None = Query(default=None, description="Indicator category filter"),
    letter: str | None = Query(default=None, description="A-Z index letter"),
):
    """All pre-built strategy suggestions grouped by primary indicator (full strategies table)."""
    if not is_db_available():
        return {
            "total_strategies": 0,
            "total_indicators": 0,
            "categories": ["All"],
            "alphabet": [],
            "indicators": [],
            "suggestions_by_indicator": {},
        }

    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    "SELECT name, slug, category, hypothesis, entry_rules, exit_rules, risk_params "
                    "FROM strategies ORDER BY name ASC"
                )
            )
            rows = result.fetchall()
    except Exception as e:
        print(f"Error loading prebuilt catalog: {e}")
        raise HTTPException(status_code=500, detail="Could not load prebuilt suggestions")

    catalog = build_prebuilt_catalog(rows)
    if q or indicator or direction or category or letter:
        catalog = filter_catalog(
            catalog,
            q=q,
            indicator=indicator,
            direction=direction,
            category=category,
            letter=letter,
        )
    return catalog


@router.get("/strategies/{slug}")
async def get_strategy(slug: str):
    if is_db_available():
        try:
            async with async_session() as session:
                result = await session.execute(
                    text(
                        "SELECT name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, backtest_results "
                        "FROM strategies WHERE slug = :slug"
                    ),
                    {"slug": slug},
                )
                row = result.fetchone()
                if row:
                    strategy = _serialize_strategy_row(row, include_full_results=True)
                    if not strategy:
                        raise HTTPException(status_code=404, detail="Strategy not found or not equity")
                    return strategy
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error loading strategy {slug} from database: {e}")

    for s in _load_strategies():
        if s.get("slug") == slug:
            path = glob.glob(f"{STRATEGIES_DIR}/**/{slug}.json", recursive=True)
            if path:
                with open(path[0], "r") as f:
                    return json.load(f)
            return s
    raise HTTPException(status_code=404, detail="Strategy not found")


@router.post("/strategies/{slug}/backtest")
async def backtest_strategy(slug: str, request: StrategyBacktestRequest):
    return await _run_and_store_backtest(slug, request.symbol, request.period)


@router.post("/strategies")
async def create_strategy(strategy: StrategyCreate):
    return {"status": "created", "strategy": strategy.model_dump()}


@router.put("/strategies/{slug}")
async def update_strategy(slug: str, strategy: StrategyCreate):
    return {"status": "updated", "slug": slug}
