import asyncio
import os
import sys
import csv
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# Add app directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import async_session
from app.db.models import OHLCV
from sqlalchemy.dialects.postgresql import insert

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../company_profiles.csv"))

SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "NIFTYFIN": "NIFTY_FIN_SERVICE.NS"
}

def get_ticker_symbol(sym: str) -> str:
    return SYMBOL_MAP.get(sym.upper(), f"{sym.upper()}.NS")

def load_tickers():
    tickers = []
    # Add indices first
    for index_sym in SYMBOL_MAP.keys():
        tickers.append((index_sym, get_ticker_symbol(index_sym)))
        
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sym = row.get("ticker")
                    if sym and sym not in SYMBOL_MAP:
                        tickers.append((sym, get_ticker_symbol(sym)))
        except Exception as e:
            print(f"Error loading company profiles: {e}")
    return tickers

async def download_and_insert_batch(batch, start_date, end_date, sem, db_queue):
    for original_sym, ticker in batch:
        async with sem:
            try:
                def _fetch():
                    return yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
                
                df = await asyncio.to_thread(_fetch)
                
                if df.empty:
                    # Fallback to BSE (.BO) if NSE (.NS) returns empty
                    if ticker.endswith(".NS"):
                        alternative_ticker = ticker.replace(".NS", ".BO")
                        def _fetch_alt():
                            return yf.download(alternative_ticker, start=start_date, end=end_date, interval="1d", progress=False)
                        df = await asyncio.to_thread(_fetch_alt)
                    
                    if df.empty:
                        print(f"[-] No data found for {original_sym} ({ticker})")
                        continue
                
                # Format columns properly (deal with potential MultiIndex output from yfinance)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                    
                df = df.reset_index()
                df = df.rename(columns={df.columns[0]: 'time'})
                df.columns = [c.lower() for c in df.columns]
                
                records = []
                for _, row in df.iterrows():
                    t_val = row['time']
                    if hasattr(t_val, 'to_pydatetime'):
                        dt = t_val.to_pydatetime()
                    else:
                        dt = pd.to_datetime(t_val).to_pydatetime()
                        
                    records.append({
                        "time": dt,
                        "symbol": original_sym,
                        "resolution": "1d",
                        "open": float(row['open']),
                        "high": float(row['high']),
                        "low": float(row['low']),
                        "close": float(row['close']),
                        "volume": int(row['volume']) if not pd.isna(row['volume']) else 0
                    })
                
                db_queue.extend(records)
                print(f"[+] Downloaded {len(records)} rows for {original_sym}")
                
            except Exception as e:
                print(f"[-] Error downloading {original_sym} ({ticker}): {e}")

async def db_writer_task(db_queue, finish_event):
    while not finish_event.is_set() or db_queue:
        if len(db_queue) >= 3000 or (finish_event.is_set() and db_queue):
            # Pop chunk of up to 3000 items to avoid exceeding asyncpg's 32767 parameter limit
            chunk = []
            for _ in range(min(3000, len(db_queue))):
                if db_queue:
                    chunk.append(db_queue.pop(0))
            
            if chunk:
                try:
                    async with async_session() as session:
                        stmt = insert(OHLCV).values(chunk)
                        stmt = stmt.on_conflict_do_update(
                            constraint='ohlcv_unique_pk',
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
                    print(f"[*] Ingested {len(chunk)} rows to database (Remaining queue: {len(db_queue)})")
                except Exception as e:
                    print(f"[!] Database bulk insertion error: {e}")
                    
        await asyncio.sleep(0.5)

async def main():
    tickers = load_tickers()
    print(f"[*] Found {len(tickers)} symbols in configuration catalog.")
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365 * 7) # Past 7 Years
    
    db_queue = []
    sem = asyncio.Semaphore(10) # 10 concurrent requests limit
    finish_event = asyncio.Event()
    
    # Start writer background task
    writer = asyncio.create_task(db_writer_task(db_queue, finish_event))
    
    # Process in batches of 50 to log cleaner progress and prevent memory overflow
    chunk_size = 50
    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i:i+chunk_size]
        print(f"\n---> Batch {i//chunk_size + 1}/{(len(tickers)-1)//chunk_size + 1} (Processing {len(batch)} tickers)")
        
        tasks = [download_and_insert_batch([item], start_date, end_date, sem, db_queue) for item in batch]
        await asyncio.gather(*tasks)
        
        # Tiny rest to prevent Yahoo rate-limiting block
        await asyncio.sleep(1.2)
        
    finish_event.set()
    await writer
    print("[*] Historical NSE/BSE stock data ingestion completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
