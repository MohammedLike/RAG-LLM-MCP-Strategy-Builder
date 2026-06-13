import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.session import async_session, is_db_available
from app.strategies.compiler import compile_db_strategy
from sqlalchemy import text

router = APIRouter()

def _normalize_json_field(field):
    if field is None:
        return {}
    if isinstance(field, str):
        try:
            return json.loads(field)
        except Exception:
            return {}
    return field

class IndependentStrategyCreate(BaseModel):
    name: str
    category: str
    rules: dict

@router.get("/independent-strategies")
async def list_independent_strategies(category: str = None):
    db_strategies = []
    if is_db_available():
        try:
            async with async_session() as session:
                query = "SELECT name, slug, category, hypothesis, entry_rules, exit_rules, risk_params FROM independent_strategies"
                params = {}
                if category:
                    query += " WHERE category = :category"
                    params["category"] = category
                query += " ORDER BY name ASC"
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                for row in rows:
                    entry_rules = _normalize_json_field(row[4])
                    exit_rules = _normalize_json_field(row[5])
                    risk_params = _normalize_json_field(row[6])
                    db_strat = {
                        "name": row[0],
                        "slug": row[1],
                        "category": row[2],
                        "hypothesis": row[3],
                        "entry_rules": entry_rules,
                        "exit_rules": exit_rules,
                        "risk_params": risk_params
                    }
                    try:
                        backtest_spec = compile_db_strategy(db_strat)
                        db_strategies.append({
                            "name": row[0],
                            "slug": row[1],
                            "category": row[2],
                            "description": row[3] or f"Independent strategy built from {row[2]} conditions.",
                            "hypothesis": row[3],
                            "tags": [row[2], "Independent"],
                            "backtest_results": {},
                            "backtest_spec": backtest_spec
                        })
                    except Exception:
                        db_strategies.append({
                            "name": row[0],
                            "slug": row[1],
                            "category": row[2],
                            "description": row[3] or f"Independent strategy built from {row[2]} conditions.",
                            "hypothesis": row[3],
                            "tags": [row[2], "Independent"],
                            "backtest_results": {},
                            "backtest_spec": {
                                "entry": entry_rules,
                                "exit": exit_rules,
                                **({} if not risk_params else {"risk_params": risk_params})
                            }
                        })
        except Exception as e:
            print(f"Error loading independent strategies from database: {e}")
    return db_strategies

@router.get("/independent-strategies/{slug}")
async def get_independent_strategy(slug: str):
    if is_db_available():
        try:
            async with async_session() as session:
                result = await session.execute(
                    text("SELECT name, slug, category, hypothesis, entry_rules, exit_rules, risk_params FROM independent_strategies WHERE slug = :slug"),
                    {"slug": slug}
                )
                row = result.fetchone()
                if row:
                    entry_rules = _normalize_json_field(row[4])
                    exit_rules = _normalize_json_field(row[5])
                    risk_params = _normalize_json_field(row[6])
                    backtest_spec = compile_db_strategy({
                        "entry_rules": entry_rules,
                        "exit_rules": exit_rules,
                        "risk_params": risk_params,
                        "category": row[2]
                    })
                    return {
                        "name": row[0],
                        "slug": row[1],
                        "category": row[2],
                        "description": row[3],
                        "hypothesis": row[3],
                        "backtest_spec": backtest_spec
                    }
        except Exception as e:
            print(f"Error loading independent strategy {slug} from database: {e}")
    raise HTTPException(status_code=404, detail="Strategy not found")

@router.post("/independent-strategies")
async def create_independent_strategy(strategy: IndependentStrategyCreate):
    if not is_db_available():
        raise HTTPException(status_code=500, detail="Database not available")
    async with async_session() as session:
        await session.execute(
            text("INSERT INTO independent_strategies (id, name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, created_at) VALUES (:id, :name, :slug, :category, :hypothesis, :entry_rules, :exit_rules, :risk_params, :created_at)"),
            {
                "id": uuid.uuid4(),
                "name": strategy.name,
                "slug": strategy.name.lower().replace(' ', '-'),
                "category": strategy.category,
                "hypothesis": strategy.rules.get('hypothesis', ''),
                "entry_rules": json.dumps(strategy.rules.get('entry', {})),
                "exit_rules": json.dumps(strategy.rules.get('exit', {})),
                "risk_params": json.dumps(strategy.rules.get('risk_params', {})),
                "created_at": datetime.utcnow()
            }
        )
        await session.commit()
    return {"status": "created", "slug": strategy.name.lower().replace(' ', '-')}
