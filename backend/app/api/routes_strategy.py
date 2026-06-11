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
        with open(path, "r") as f:
            data = json.load(f)
        strategies.append({
            "name": data.get("name"),
            "slug": data.get("slug", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "tags": data.get("tags", []),
            "backtest_results": data.get("backtest_results", {}),
        })
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
