import json
import glob
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

STRATEGIES_DIR = os.environ.get(
    "STRATEGIES_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../training/data/strategies")),
)

class StrategyCreate(BaseModel):
    name: str
    category: str
    rules: dict

def _load_strategies():
    strategies = []
    for path in glob.glob(f"{STRATEGIES_DIR}/**/*.json", recursive=True):
        if "_schema" in path:
            continue
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            # Auto-extract slug from filename if not explicit
            file_slug = os.path.basename(path).replace(".json", "")
            slug = data.get("slug") or file_slug
            
            # Normalize auto-generated format if needed
            logic = data.get("logic", {})
            entry_rules = data.get("entry_rules") or logic.get("entry", {})
            exit_rules = data.get("exit_rules") or logic.get("exit", {})
            
            strategies.append({
                "name": data.get("name") or file_slug.replace("_", " ").title(),
                "slug": slug,
                "category": data.get("category", "General"),
                "description": data.get("description") or data.get("hypothesis", ""),
                "hypothesis": data.get("hypothesis") or data.get("description", ""),
                "tags": data.get("tags") or [data.get("category", "General")],
                "backtest_results": data.get("backtest_results", {}),
                "backtest_spec": data.get("backtest_spec") or {
                    "entry": entry_rules,
                    "exit": exit_rules,
                    "stop_loss": exit_rules.get("stop_loss"),
                    "take_profit": exit_rules.get("target") or exit_rules.get("take_profit")
                },
                "entry_rules": entry_rules,
                "exit_rules": exit_rules
            })
        except Exception as e:
            print(f"Error loading strategy file {path}: {e}")
    return strategies


@router.get("/strategies")
async def list_strategies():
    return _load_strategies()

@router.get("/strategies/{slug}")
async def get_strategy(slug: str):
    for s in _load_strategies():
        if s.get("slug") == slug:
            path = glob.glob(f"{STRATEGIES_DIR}/**/{slug}.json", recursive=True)
            if path:
                with open(path[0], "r") as f:
                    return json.load(f)
    raise HTTPException(status_code=404, detail="Strategy not found")

@router.post("/strategies")
async def create_strategy(strategy: StrategyCreate):
    return {"status": "created", "strategy": strategy.model_dump()}

@router.put("/strategies/{slug}")
async def update_strategy(slug: str, strategy: StrategyCreate):
    return {"status": "updated", "slug": slug}
