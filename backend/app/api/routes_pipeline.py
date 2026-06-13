"""Full quant pipeline API — INPUT → AI → EXECUTION → ANALYSIS → OUTPUT."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from ..backtest.export import (
    export_optimization_html,
    export_result_json,
    export_result_xlsx,
    export_trades_csv,
)
from ..backtest.optimizer import run_grid_search
from ..config import settings
from ..db.pine_store import delete_pine_script, get_pine_script, list_pine_scripts, save_pine_script
from ..execution.live_runner import (
    convert_pine_to_strategy,
    deploy_strategy,
    get_strategy_detail,
    list_strategies,
    start_strategy,
    stop_strategy,
    tick_strategy,
)
from ..market.parquet_store import SUPPORTED_RESOLUTIONS, list_available, read_ohlcv, write_ohlcv
from ..market.provider_yfinance import YFinanceProvider
from ..mcp.tool_analyze_backtest import analyze_backtest_result
from ..mcp.tool_run_backtest import RunBacktestInput, run_backtest_tool
from ..nl_parser import nl_parser
from ..strategies.pine_parser import parse_pine_script
from ..strategies.pine_ai import (
    chat_pine_assistant,
    generate_pine_strategy,
    interpret_with_ai,
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

provider = YFinanceProvider()
_validation_sessions: dict[str, dict] = {}


class InterpretRequest(BaseModel):
    source_type: str = Field(description="pine | text | ai")
    content: str = ""
    script_id: Optional[str] = None
    symbol: str = "NIFTY"
    period: str = "1y"
    interval: str = "1d"
    use_ai: bool = False


class PineAiGenerateRequest(BaseModel):
    prompt: str
    symbol: str = "NIFTY"
    period: str = "2y"
    interval: str = "1d"
    save_pine: bool = True


class PineAiChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    symbol: str = "NIFTY"


class PineAiBacktestRequest(BaseModel):
    prompt: str
    symbol: str = "NIFTY"
    period: str = "2y"
    interval: str = "1d"
    save_pine: bool = True
    skip_validation: bool = True


class ValidateRequest(BaseModel):
    session_id: str
    action: str = Field(description="approve | reject | rerun")


class OptimizeRequest(BaseModel):
    strategy_spec: dict
    symbol: str = "NIFTY"
    period: str = "1y"
    interval: str = "1d"
    param_grid: dict[str, list] = Field(default_factory=lambda: {"stop_loss": [1.0, 2.0, 3.0, 4.0, 5.0]})


class AnalyzeRequest(BaseModel):
    result: dict


class ExportRequest(BaseModel):
    format: str = Field(description="csv | json | xlsx | html | optimization_html")
    result: dict
    title: str = "StrykeX Report"


class ApplyOptimizationRequest(BaseModel):
    session_id: str
    approved: bool = True


class PineConvertRequest(BaseModel):
    pine_script: str
    symbol: str = "NIFTY"
    period: str = "2y"
    interval: str = "1d"
    use_ai: bool = True
    run_backtest: bool = True


class LiveDeployRequest(BaseModel):
    name: str = "Pine Live Strategy"
    symbol: str = "NIFTY"
    interval: str = "1d"
    strategy_spec: dict
    pine_script: str = ""
    mode: str = Field(default="paper", description="paper | live")
    capital: float = 100_000.0
    quantity: int = 1


class PineToLiveRequest(BaseModel):
    """Full bridge: Pine Script → convert → backtest on DB → deploy paper live."""
    pine_script: str
    name: str = "TradingView Pine Strategy"
    symbol: str = "NIFTY"
    period: str = "2y"
    interval: str = "1d"
    mode: str = "paper"
    capital: float = 100_000.0
    quantity: int = 1
    auto_tick: bool = True


@router.get("/status")
async def pipeline_status():
    live = list_strategies()
    active = sum(1 for s in live if s.get("status") == "active")
    pine_count = len(await list_pine_scripts(limit=500))
    return {
        "stages": ["input", "ai_layer", "execution", "analysis", "output", "live_execution"],
        "pine_scripts": pine_count,
        "parquet_datasets": len(list_available()),
        "supported_resolutions": list(SUPPORTED_RESOLUTIONS),
        "pending_validations": len(_validation_sessions),
        "live_strategies": len(live),
        "live_active": active,
        "broker_connected": bool(settings.BROKER_ACCESS_TOKEN),
    }


# ── INPUT ──────────────────────────────────────────────────────────────────

@router.post("/pine/upload")
async def upload_pine_script(file: UploadFile = File(...)):
    if not file.filename or not (file.filename.endswith(".pine") or file.filename.endswith(".txt")):
        raise HTTPException(400, "Upload a .pine or .txt file")

    script_id = Path(file.filename).stem.replace(" ", "_")
    content = (await file.read()).decode("utf-8", errors="replace")
    saved = await save_pine_script(
        content,
        name=script_id.replace("_", " ").title(),
        source="upload",
        slug=script_id,
    )
    if not saved:
        raise HTTPException(503, "Database unavailable — could not store Pine script")
    return {"id": saved["slug"], "filename": saved["filename"], "bytes": saved["size"]}


@router.get("/pine")
async def list_pine_scripts_route():
    scripts = await list_pine_scripts()
    return {"scripts": scripts}


@router.get("/pine/{script_id}")
async def get_pine_script_route(script_id: str):
    row = await get_pine_script(script_id)
    if not row:
        raise HTTPException(404, "Script not found")
    return {"id": row.get("slug") or row.get("id"), "content": row.get("content")}


@router.delete("/pine/{script_id}")
async def delete_pine_script_route(script_id: str):
    deleted = await delete_pine_script(script_id)
    if not deleted:
        raise HTTPException(404, "Script not found")
    return {"deleted": script_id}


@router.get("/ohlcv/resolutions")
async def ohlcv_resolutions(symbol: Optional[str] = None):
    return {
        "supported": list(SUPPORTED_RESOLUTIONS),
        "available": list_available(symbol),
    }


@router.post("/ohlcv/cache/{symbol}/{resolution}")
async def cache_ohlcv_to_parquet(symbol: str, resolution: str, period: str = "1y"):
    if resolution not in SUPPORTED_RESOLUTIONS:
        raise HTTPException(400, f"Use one of {SUPPORTED_RESOLUTIONS}")

    days_map = {"1y": 365, "2y": 730, "5y": 1825, "6m": 180, "3y": 1095}
    days = days_map.get(period, 365)
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    df = await provider.get_ohlcv(symbol, resolution, start, end)
    if df.empty:
        raise HTTPException(404, f"No OHLCV for {symbol} {resolution}")

    path = write_ohlcv(symbol, resolution, df)
    return {"symbol": symbol, "resolution": resolution, "rows": len(df), "path": str(path)}


# ── PINE → LIVE EXECUTION BRIDGE ───────────────────────────────────────────

@router.post("/pine/convert")
async def pine_convert_to_strategy(request: PineConvertRequest):
    """Convert TradingView Pine Script into executable strategy_spec (AI + heuristics)."""
    converted = await convert_pine_to_strategy(
        request.pine_script,
        request.symbol,
        request.period,
        request.interval,
        request.use_ai,
    )
    if converted.get("error") and not converted.get("strategy_spec"):
        return converted

    out = {**converted}
    if request.run_backtest:
        bt = await run_backtest_tool(RunBacktestInput(
            strategy_spec=converted["strategy_spec"],
            symbol=converted.get("symbol") or request.symbol,
            period=converted.get("period") or request.period,
            interval=request.interval,
            strategy_label="Pine Convert Backtest",
            source="pipeline",
            pine_script=request.pine_script,
            user_request={"action": "pine_convert"},
        ))
        out["backtest_result"] = bt
        if not bt.get("error"):
            out["analysis"] = analyze_backtest_result(bt)
    return out


@router.post("/pine/to-live")
async def pine_to_live_automation(request: PineToLiveRequest):
    """
    End-to-end: Pine Script → strategy JSON → backtest on database → deploy automated execution.
    Paper mode simulates fills; live mode requires broker token.
    """
    converted = await convert_pine_to_strategy(
        request.pine_script,
        request.symbol,
        request.period,
        request.interval,
        use_ai=True,
    )
    if converted.get("error") and not converted.get("strategy_spec"):
        raise HTTPException(400, converted.get("error", "Pine conversion failed"))

    symbol = converted.get("symbol") or request.symbol
    period = converted.get("period") or request.period
    spec = converted["strategy_spec"]

    backtest = await run_backtest_tool(RunBacktestInput(
        strategy_spec=spec,
        symbol=symbol,
        period=period,
        interval=request.interval,
        strategy_label=request.name,
        source="pipeline_live",
        pine_script=converted.get("pine_script") or request.pine_script,
        user_request={"action": "pine_to_live", "mode": request.mode},
    ))
    if backtest.get("error"):
        return {
            "stage": "backtest_failed",
            "converted": converted,
            "backtest_result": backtest,
            "error": backtest["error"],
        }

    script_id = backtest.get("pine_slug") or backtest.get("pine_script_id")
    if not script_id:
        saved = await save_pine_script(
            converted.get("pine_script") or request.pine_script,
            name=request.name,
            source="live",
            symbol=symbol,
            period=period,
            resolution=request.interval,
            strategy_spec=spec,
        )
        script_id = saved.get("slug") if saved else None
    converted["script_id"] = script_id

    deployed = await deploy_strategy(
        name=request.name,
        symbol=symbol,
        interval=request.interval,
        strategy_spec=spec,
        pine_script=converted.get("pine_script") or request.pine_script,
        mode=request.mode,
        capital=request.capital,
        quantity=request.quantity,
    )

    tick_result = None
    if request.auto_tick:
        tick_result = await tick_strategy(deployed["id"])

    return {
        "stage": "live_deployed",
        "message": "Pine Script bridged to automated execution on your database signals.",
        "converted": converted,
        "backtest_result": backtest,
        "analysis": analyze_backtest_result(backtest),
        "live_strategy": deployed,
        "first_tick": tick_result,
        "execution_mode": request.mode,
        "data_source": backtest.get("data_source", "postgres"),
    }


@router.post("/live/deploy")
async def live_deploy(request: LiveDeployRequest):
    deployed = await deploy_strategy(
        name=request.name,
        symbol=request.symbol,
        interval=request.interval,
        strategy_spec=request.strategy_spec,
        pine_script=request.pine_script,
        mode=request.mode,
        capital=request.capital,
        quantity=request.quantity,
    )
    return deployed


@router.get("/live")
async def live_list():
    return {"strategies": list_strategies()}


@router.get("/live/{strategy_id}")
async def live_detail(strategy_id: str):
    detail = get_strategy_detail(strategy_id)
    if not detail:
        raise HTTPException(404, "Live strategy not found")
    return detail


@router.post("/live/{strategy_id}/tick")
async def live_tick(strategy_id: str):
    """Run signal check on latest DB bar and execute orders (paper or live broker)."""
    return await tick_strategy(strategy_id)


@router.post("/live/{strategy_id}/stop")
async def live_stop(strategy_id: str):
    return stop_strategy(strategy_id)


@router.post("/live/{strategy_id}/start")
async def live_start(strategy_id: str):
    return start_strategy(strategy_id)


# ── AI LAYER ───────────────────────────────────────────────────────────────

@router.post("/interpret")
async def interpret_strategy(request: InterpretRequest):
    content = request.content
    if request.source_type == "pine" and request.script_id:
        row = await get_pine_script(request.script_id)
        if not row:
            raise HTTPException(404, "Pine script not found")
        content = row.get("content") or content

    use_ai = request.use_ai or request.source_type == "ai"
    pine_script = content if request.source_type == "pine" and content.strip() else None
    sym = request.symbol
    per = request.period

    if use_ai:
        try:
            result = await interpret_with_ai(
                content,
                "pine" if request.source_type == "pine" else "text",
                request.symbol,
                request.period,
                request.interval,
            )
        except ValueError as e:
            return {"error": str(e)}
        if result.get("error") and not result.get("strategy_spec"):
            return result
        strategy_spec = result["strategy_spec"]
        source = result.get("source", "ai")
        warnings = result.get("warnings", [])
        summary = result.get("summary") or result.get("explanation", "")
        pine_script = result.get("pine_script")
        sym = result.get("symbol") or request.symbol
        per = result.get("period") or request.period
    elif request.source_type == "pine":
        parsed = parse_pine_script(content)
        if parsed.get("error") and not parsed.get("strategy_spec"):
            result = await interpret_with_ai(content, "pine", request.symbol, request.period, request.interval)
            strategy_spec = result["strategy_spec"]
            source = result.get("source", "ai_from_pine")
            warnings = result.get("warnings", [])
            summary = result.get("explanation", "")
            pine_script = result.get("pine_script")
        else:
            strategy_spec = parsed["strategy_spec"]
            source = parsed.get("source", "pine")
            warnings = parsed.get("warnings", [])
            summary = parsed.get("summary", "")
    else:
        nl = nl_parser.parse(content)
        if nl and nl.get("strategy_spec"):
            strategy_spec = nl["strategy_spec"]
            source = "nl_parser"
            warnings = []
            summary = content[:200]
        else:
            result = await generate_pine_strategy(content, request.symbol, request.period, request.interval)
            strategy_spec = result["strategy_spec"]
            source = result.get("source", "ai")
            warnings = [result["llm_error"]] if result.get("llm_error") else []
            summary = result.get("explanation", "")
            pine_script = result.get("pine_script")
            sym = result.get("symbol") or request.symbol
            per = result.get("period") or request.period

    session_id = str(uuid.uuid4())
    pine_script_id = None
    if pine_script:
        saved = await save_pine_script(
            pine_script,
            name=summary[:80] if summary else "Pipeline Strategy",
            source=source,
            symbol=sym,
            period=per,
            resolution=request.interval,
            strategy_spec=strategy_spec,
            prompt=content[:2000] if request.source_type == "text" else None,
        )
        if saved:
            pine_script_id = saved.get("id")

    _validation_sessions[session_id] = {
        "session_id": session_id,
        "status": "pending",
        "strategy_spec": strategy_spec,
        "symbol": sym,
        "period": per,
        "interval": request.interval,
        "source": source,
        "pine_script": pine_script,
        "pine_script_id": pine_script_id,
        "created": datetime.utcnow().isoformat(),
    }

    return {
        "session_id": session_id,
        "status": "pending_validation",
        "strategy_spec": strategy_spec,
        "pine_script": pine_script,
        "pine_script_id": pine_script_id,
        "symbol": sym,
        "period": per,
        "source": source,
        "warnings": warnings,
        "summary": summary,
        "validation_required": True,
    }


@router.post("/ai/generate")
async def ai_generate_pine(request: PineAiGenerateRequest):
    """Generate Pine Script + strategy_spec JSON via Ollama."""
    result = await generate_pine_strategy(
        request.prompt,
        symbol=request.symbol,
        period=request.period,
        interval=request.interval,
    )
    if request.save_pine and result.get("pine_script"):
        saved = await save_pine_script(
            result["pine_script"],
            name=result.get("strategy_spec", {}).get("name") or "AI Pine Strategy",
            source="ai",
            symbol=request.symbol,
            period=request.period,
            resolution=request.interval,
            strategy_spec=result.get("strategy_spec"),
            prompt=request.prompt,
        )
        if saved:
            result["script_id"] = saved.get("slug")
            result["pine_script_id"] = saved.get("id")
    return result


@router.post("/ai/chat")
async def ai_chat_assistant(request: PineAiChatRequest):
    """Conversational assistant for the Pine Quant Builder."""
    return await chat_pine_assistant(request.message, request.history, request.symbol)


@router.post("/ai/backtest")
async def ai_generate_and_backtest(request: PineAiBacktestRequest):
    """Generate Pine + strategy_spec with AI, then backtest on Postgres OHLCV."""
    generated = await generate_pine_strategy(
        request.prompt,
        symbol=request.symbol,
        period=request.period,
        interval=request.interval,
    )
    pine_script_id = None
    if request.save_pine and generated.get("pine_script"):
        saved = await save_pine_script(
            generated["pine_script"],
            name="AI Backtest Strategy",
            source="ai",
            symbol=request.symbol,
            period=request.period,
            resolution=request.interval,
            strategy_spec=generated.get("strategy_spec"),
            prompt=request.prompt,
        )
        if saved:
            pine_script_id = saved.get("id")
            generated["script_id"] = saved.get("slug")
            generated["pine_script_id"] = pine_script_id

    symbol = generated.get("symbol") or request.symbol
    period = generated.get("period") or request.period
    interval = generated.get("interval") or request.interval
    spec = generated["strategy_spec"]

    session_id = str(uuid.uuid4())
    _validation_sessions[session_id] = {
        "session_id": session_id,
        "status": "approved" if request.skip_validation else "pending",
        "strategy_spec": spec,
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "source": generated.get("source", "ai"),
        "pine_script": generated.get("pine_script"),
        "prompt": request.prompt,
        "created": datetime.utcnow().isoformat(),
    }

    result = await run_backtest_tool(RunBacktestInput(
        strategy_spec=spec,
        symbol=symbol,
        period=period,
        interval=interval,
        strategy_label="AI Pine Backtest",
        source="ai",
        pine_script=generated.get("pine_script"),
        pine_script_id=pine_script_id,
        user_request={"prompt": request.prompt, "action": "ai_backtest"},
    ))
    _validation_sessions[session_id]["backtest_result"] = result
    analysis = analyze_backtest_result(result) if not result.get("error") else None

    return {
        "session_id": session_id,
        "generated": generated,
        "backtest_result": result,
        "analysis": analysis,
        "data_source": result.get("data_source", "postgres"),
    }


@router.post("/validate")
async def validate_strategy(request: ValidateRequest):
    session = _validation_sessions.get(request.session_id)
    if not session:
        raise HTTPException(404, "Validation session not found")

    if request.action == "reject":
        session["status"] = "rejected"
        return {"session_id": request.session_id, "status": "rejected"}

    if request.action == "rerun":
        session["status"] = "pending"
        return {"session_id": request.session_id, "status": "pending", "strategy_spec": session["strategy_spec"]}

    if request.action == "approve":
        session["status"] = "approved"
        result = await run_backtest_tool(RunBacktestInput(
            strategy_spec=session["strategy_spec"],
            symbol=session.get("symbol", "NIFTY"),
            period=session.get("period", "1y"),
            interval=session.get("interval", "1d"),
            strategy_label=(session.get("summary") or "Pipeline Strategy")[:120],
            source="pipeline",
            pine_script=session.get("pine_script"),
            pine_script_id=session.get("pine_script_id"),
            user_request={"session_id": request.session_id, "action": "validate_approve"},
        ))
        session["backtest_result"] = result
        analysis = analyze_backtest_result(result) if not result.get("error") else None
        return {
            "session_id": request.session_id,
            "status": "approved",
            "backtest_result": result,
            "analysis": analysis,
        }

    raise HTTPException(400, "action must be approve, reject, or rerun")


@router.get("/validate/{session_id}")
async def get_validation_session(session_id: str):
    session = _validation_sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


# ── EXECUTION (optimize wraps VectorBT engine) ─────────────────────────────

@router.post("/optimize")
async def optimize_strategy(request: OptimizeRequest):
    days_map = {"1y": 365, "2y": 730, "5y": 1825, "6m": 180, "3y": 1095}
    days = days_map.get(request.period, 365)
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    df = await provider.get_ohlcv(request.symbol, request.interval, start, end)
    if df.empty:
        parquet_df = read_ohlcv(request.symbol, request.interval, start, end)
        df = parquet_df if not parquet_df.empty else df
    if df.empty:
        raise HTTPException(404, f"No data for {request.symbol} ({request.interval})")

    opt = run_grid_search(df, request.strategy_spec, request.param_grid)
    return {
        "symbol": request.symbol,
        "period": request.period,
        "interval": request.interval,
        **opt,
    }


# ── ANALYSIS ───────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_results(request: AnalyzeRequest):
    return analyze_backtest_result(request.result)


@router.post("/apply-optimization")
async def apply_optimization(request: ApplyOptimizationRequest):
    session = _validation_sessions.get(request.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if not request.approved:
        session["optimization_status"] = "rejected"
        return {"status": "rejected"}

    best = session.get("optimization", {}).get("best_params") or {}
    if not best:
        raise HTTPException(400, "No optimization results on session")

    spec = session.get("strategy_spec", {})
    for path, val in best.items():
        if path == "stop_loss":
            spec["stop_loss"] = val
        elif path == "take_profit":
            spec["take_profit"] = val
    session["strategy_spec"] = spec
    session["optimization_status"] = "approved"
    return {"status": "approved", "strategy_spec": spec}


# ── OUTPUT / EXPORT ──────────────────────────────────────────────────────

@router.post("/export")
async def export_results(request: ExportRequest):
    fmt = request.format.lower()
    symbol = request.result.get("symbol", "STRATEGY")

    if fmt == "csv":
        content = export_trades_csv(request.result)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="trades-{symbol}.csv"'},
        )
    if fmt == "json":
        return Response(
            content=export_result_json(request.result),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="backtest-{symbol}.json"'},
        )
    if fmt == "xlsx":
        data = export_result_xlsx(request.result)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="backtest-{symbol}.xlsx"'},
        )
    if fmt == "optimization_html":
        html = export_optimization_html(request.result, request.title)
        return HTMLResponse(content=html)
    raise HTTPException(400, "format must be csv, json, xlsx, or optimization_html")
