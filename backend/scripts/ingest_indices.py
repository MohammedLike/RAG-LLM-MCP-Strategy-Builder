import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add the 'app' directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.market.provider_yfinance import YFinanceProvider
from app.db.session import async_session
from app.db.models import OHLCV
from sqlalchemy.dialects.postgresql import insert

# Mapping for indices
INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "NIFTY100", "NIFTY500"]

async def ingest_historical(symbol: str, years: int = 8):
    provider = YFinanceProvider()
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365 * years)
    
    print(f"[{symbol}] Fetching historical data (last {years} years)...")
    try:
        df = await provider.get_ohlcv(symbol, interval="1d", start=start_date, end=end_date)
        
        if df.empty:
            print(f"[{symbol}] No data found.")
            return

        print(f"[{symbol}] Fetched {len(df)} records. Processing...")

        # Prepare for DB
        df["time"] = pd.to_datetime(df["time"], utc=True)
        # Drop columns not in OHLCV table if any
        expected_cols = ['time', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'resolution']
        df['resolution'] = '1d'
        df['symbol'] = symbol
        
        # Clean up column names to match model
        records = []
        for _, row in df.iterrows():
            records.append({
                "time": row["time"],
                "symbol": row["symbol"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]) if pd.notna(row["volume"]) else 0,
                "resolution": row["resolution"]
            })
        
        async with async_session() as session:
            # Batch upsert
            for i in range(0, len(records), 500):
                batch = records[i:i+500]
                stmt = insert(OHLCV).values(batch)
                stmt = stmt.on_conflict_do_update(
                    constraint='ohlcv_unique_pk', # composite pk: time, symbol, resolution
                    set_={
                        'open': stmt.excluded.open,
                        'high': stmt.excluded.high,
                        'low': stmt.excluded.low,
                        'close': stmt.excluded.close,
                        'volume': stmt.excluded.volume
                    }
                )
                await session.execute(stmt)
            await session.commit()
        
        print(f"[{symbol}] Ingestion complete.")
    except Exception as e:
        print(f"[{symbol}] Error: {e}")

async def main():
    print(f"Starting ingestion for indices: {', '.join(INDICES)}")
    for sym in INDICES:
        await ingest_historical(sym, years=8) # Fetching 8 years for safety
    print("All indices ingested.")

if __name__ == "__main__":
    asyncio.run(main())
