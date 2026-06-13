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

async def ingest_historical(symbol: str, years: int = 10):
    provider = YFinanceProvider()
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365 * years)
    
    print(f"Fetching historical data for {symbol} from {start_date.date()} to {end_date.date()}...")
    df = await provider.get_ohlcv(symbol, interval="1d", start=start_date, end=end_date)
    
    if df.empty:
        print(f"No data found for {symbol}.")
        return

    print(f"Fetched {len(df)} records. Ingesting into database...")

    df["time"] = pd.to_datetime(df["time"], utc=True)
    df["resolution"] = "1d" # Since we fetched with interval="1d"
    records = df.to_dict(orient="records")
    
    async with async_session() as session:
        # Upsert into PostgreSQL (TimescaleDB)
        stmt = insert(OHLCV).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=['time', 'symbol', 'resolution'],
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
    
    print(f"Successfully ingested {symbol} historical data.")

async def main():
    for sym in ["NIFTY", "BANKNIFTY"]:
        await ingest_historical(sym, years=14)


if __name__ == "__main__":
    asyncio.run(main())
