from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class StrategyCreate(BaseModel):
    name: str
    category: str
    rules: dict

@router.get("/strategies")
async def list_strategies():
    return [{"name": "Short Strangle"}, {"name": "Iron Condor"}]

@router.get("/strategies/{slug}")
async def get_strategy(slug: str):
    return {"name": slug, "details": "..."}

@router.post("/strategies")
async def create_strategy(strategy: StrategyCreate):
    return {"status": "created", "strategy": strategy.dict()}

@router.put("/strategies/{slug}")
async def update_strategy(slug: str, strategy: StrategyCreate):
    return {"status": "updated", "slug": slug}
