import asyncio
import sys
import os
import json
import glob
import uuid
from datetime import datetime

# Add the 'app' directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://quant_user:quant_password@postgres:5432/quant_db'
STRATEGIES_DIR = '/training/data/strategies/auto_generated'

async def seed_auto_generated():
    print(f"Scanning for auto-generated strategies in {STRATEGIES_DIR}...")
    files = glob.glob(f"{STRATEGIES_DIR}/*.json")
    
    if not files:
        print("No JSON files found. Did you run the generation script?")
        return
        
    print(f"Found {len(files)} strategy files. Starting database ingestion...")
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    success_count = 0
    skip_count = 0
    
    async with async_session() as session:
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                slug = data.get('slug')
                
                # Check if exists
                res = await session.execute(text("SELECT id FROM strategies WHERE slug = :slug"), {'slug': slug})
                if res.fetchone():
                    skip_count += 1
                    continue
                    
                # Format logic for DB
                logic = data.get('logic', {})
                entry_rules = json.dumps(logic.get('entry', {}))
                exit_rules = json.dumps(logic.get('exit', {}))
                
                # We can put 'timeframe' into risk_params or strategy_metadata for now
                risk_params = json.dumps({
                    "stop_loss": logic.get('exit', {}).get('stop_loss', '1%'),
                    "take_profit": logic.get('exit', {}).get('target', '2%'),
                    "timeframe": logic.get('entry', {}).get('timeframe', '15min')
                })

                await session.execute(
                    text("INSERT INTO strategies (id, name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, created_at) "
                         "VALUES (:id, :name, :slug, :category, :hypothesis, :entry_rules, :exit_rules, :risk_params, :created_at)"),
                    {
                        'id': uuid.uuid4(),
                        'name': data.get('name'),
                        'slug': slug,
                        'category': data.get('category', 'Indicator Based'),
                        'hypothesis': data.get('description', ''),
                        'entry_rules': entry_rules,
                        'exit_rules': exit_rules,
                        'risk_params': risk_params,
                        'created_at': datetime.utcnow()
                    }
                )
                success_count += 1
                
                # Commit every 100 to avoid locking up
                if success_count % 100 == 0:
                    await session.commit()
                    print(f"Inserted {success_count}...")
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                
        # Final commit
        await session.commit()
    
    await engine.dispose()
    print(f"Seeding Complete! Inserted: {success_count}, Skipped (already exist): {skip_count}")

if __name__ == "__main__":
    asyncio.run(seed_auto_generated())
