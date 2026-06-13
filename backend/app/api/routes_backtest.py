from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ..mcp.tool_run_backtest import run_backtest_tool, RunBacktestInput
from ..mcp import tool_run_backtest
from ..db.backtest_store import get_backtest_run, list_backtest_runs
from ..db.task_store import task_store
from ..backtest.indicators import IndicatorManager
from ..nl_parser import nl_parser
from ..db.session import is_db_available
from datetime import datetime
import uuid
import html
from typing import Optional

router = APIRouter()

class AsyncBacktestRequest(BaseModel):
    strategy_spec: dict
    symbol: str
    period: str = "1y"

class BacktestStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None

class ParseStrategyRequest(BaseModel):
    text: str

class BacktestReportRequest(BaseModel):
    symbol: str
    period: str = "1y"
    strategy_label: str = "Custom Strategy"
    strategy_text: str = ""
    result: dict

@router.get("/health/data")
async def data_health():
    """Quick check that Postgres OHLCV and strategies are available."""
    if not is_db_available():
        return {"database": "unavailable", "ohlcv": 0, "strategies": 0}

    from sqlalchemy import text
    from ..config import settings
    from ..db.session import async_session

    async with async_session() as session:
        ohlcv_count = (await session.execute(text("SELECT COUNT(*) FROM ohlcv"))).scalar() or 0
        strat_count = (
            await session.execute(
                text(
                    "SELECT COUNT(*) FROM strategies "
                    "WHERE category NOT IN ('Options', 'Indicator Based', 'Fundamental')"
                )
            )
        ).scalar() or 0
        nifty_count = (
            await session.execute(
                text("SELECT COUNT(*) FROM ohlcv WHERE symbol = 'NIFTY' AND resolution = '1d'")
            )
        ).scalar() or 0

    return {
        "database": "connected",
        "ohlcv_rows": ohlcv_count,
        "equity_strategies": strat_count,
        "nifty_daily_bars": nifty_count,
        "db_only_mode": settings.OHLCV_DB_ONLY,
    }

@router.post("/backtest/parse")
async def parse_strategy(request: ParseStrategyRequest):
    parsed = nl_parser.parse(request.text)
    if not parsed:
        return {"error": "Could not parse strategy text. Try RSI/SMA patterns or use the Chat panel with Ollama."}
    return parsed

@router.post("/backtest/report", response_class=HTMLResponse)
async def backtest_report(request: BacktestReportRequest):
    r = request.result
    trades = r.get("trades") or []
    rows = ""
    for t in trades[:50]:
        pnl = t.get("pnl", 0)
        pnl_pct = t.get("pnl_pct", 0)
        cls = "pos" if pnl >= 0 else "neg"
        rows += (
            f"<tr><td>#{t.get('id','')}</td><td>{html.escape(str(t.get('entry_date','')))}</td>"
            f"<td>{html.escape(str(t.get('exit_date','')))}</td>"
            f"<td>{t.get('entry_price', 0):,.2f}</td><td>{t.get('exit_price', 0):,.2f}</td>"
            f"<td class='{cls}'>{pnl:+,.2f}</td><td class='{cls}'>{pnl_pct:+.2f}%</td></tr>"
        )

    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>StrykeX Backtest Report</title>
<style>
body{{font-family:Georgia,serif;max-width:960px;margin:40px auto;padding:0 24px;color:#111}}
h1{{font-size:1.75rem;margin-bottom:4px}} .meta{{color:#555;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}
.card{{border:1px solid #ddd;border-radius:8px;padding:14px}} .label{{font-size:12px;color:#666}}
.val{{font-size:1.4rem;font-weight:700;font-family:monospace;margin-top:6px}}
.pos{{color:#15803d}} .neg{{color:#dc2626}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}}
th,td{{border-bottom:1px solid #eee;padding:8px;text-align:left}} th{{color:#666;font-weight:600}}
</style></head><body>
<h1>StrykeX Backtest Report</h1>
<p class="meta">{html.escape(request.strategy_label)} · {html.escape(request.symbol)} · {html.escape(request.period)} · Generated {generated}</p>
<p class="meta">Data source: {html.escape(str(r.get('data_source', 'postgres')))} · {r.get('data_rows', '—')} bars · {html.escape(str(r.get('data_start','')))} → {html.escape(str(r.get('data_end','')))}</p>
<div class="grid">
<div class="card"><div class="label">Total Return</div><div class="val">{r.get('total_return', 0):+.2f}%</div></div>
<div class="card"><div class="label">Sharpe</div><div class="val">{r.get('sharpe', 0):.2f}</div></div>
<div class="card"><div class="label">Max Drawdown</div><div class="val neg">{r.get('max_drawdown', 0):.2f}%</div></div>
<div class="card"><div class="label">Win Rate</div><div class="val">{r.get('win_rate', 0):.0f}%</div></div>
<div class="card"><div class="label">Profit Factor</div><div class="val">{r.get('profit_factor', 0):.2f}</div></div>
<div class="card"><div class="label">Sortino</div><div class="val">{r.get('sortino', 0):.2f}</div></div>
<div class="card"><div class="label">Total Trades</div><div class="val">{len(trades)}</div></div>
<div class="card"><div class="label">Strategy</div><div class="label" style="margin-top:8px;line-height:1.5">{html.escape(request.strategy_text[:240])}</div></div>
</div>
<h2>Trade Log</h2>
<table><thead><tr><th>ID</th><th>Entry</th><th>Exit</th><th>Entry ₹</th><th>Exit ₹</th><th>P&amp;L</th><th>P&amp;L %</th></tr></thead>
<tbody>{rows or "<tr><td colspan='7'>No trades</td></tr>"}</tbody></table>
</body></html>"""
    return HTMLResponse(content=doc)

@router.get("/indicators")
async def get_indicators():
    return IndicatorManager.get_indicators_list()

@router.get("/backtest/history")
async def list_backtest_history(limit: int = 50, symbol: str | None = None):
    """List persisted backtest runs from Postgres."""
    return {"history": await list_backtest_runs(limit=limit, symbol=symbol)}


@router.get("/backtest/latest")
async def get_latest_backtest():
    return tool_run_backtest.LAST_BACKTEST


@router.post("/backtest")
async def run_backtest(request: RunBacktestInput):
    return await run_backtest_tool(request)

@router.post("/backtest/async")
async def run_backtest_async(requests: list[AsyncBacktestRequest], background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    await task_store.create(task_id, meta={"count": len(requests)})

    async def execute():
        try:
            results = []
            for req in requests:
                result = await run_backtest_tool(RunBacktestInput(
                    strategy_spec=req.strategy_spec,
                    symbol=req.symbol,
                    period=req.period,
                    source="async_batch",
                    persist=True,
                ))
                results.append({"symbol": req.symbol, "period": req.period, **result})
            await task_store.complete(task_id, results)
        except Exception as e:
            await task_store.fail(task_id, str(e))

    background_tasks.add_task(execute)
    return {"task_id": task_id, "status": "running"}

@router.get("/backtest/async/{task_id}")
async def get_async_result(task_id: str):
    task = await task_store.get(task_id)
    if not task:
        return {"error": "Task not found"}
    return task

@router.get("/backtest/{backtest_id}")
async def get_backtest(backtest_id: str):
    """Fetch a persisted backtest run by UUID."""
    if backtest_id in ("history", "latest", "async"):
        return {"error": "Invalid backtest id"}
    row = await get_backtest_run(backtest_id)
    if not row:
        return {"error": "Backtest not found", "id": backtest_id}
    return row
