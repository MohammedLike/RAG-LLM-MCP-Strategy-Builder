import asyncio
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# Add app directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import async_session
from app.db.models import OHLCV
from sqlalchemy.dialects.postgresql import insert

MISSING_SYMBOLS = [
    "VIKASPROP", "VIKASWSP", "VIMALEL", "VIMTAPABS", "VINYLINDIA", "VIPCL", 
    "VIPULLTD", "VISAKAIND", "VISASTEEL", "VISESHINFO", "VISHAL", "VISHNU", 
    "VISHWARAJ", "VIVIDIND", "VIVIMED", "VLSFINANCE", "VMART", "VOLTAMP", 
    "VOLTAS", "VRLLOG", "VSSL", "VSTIND", "VSTTILLERS", "VTL", "WABAG"
]

def get_ticker_symbol(sym: str) -> str:
    return f"{sym.upper()}.NS"

async def main():
    print(f"[*] Starting ingestion of {len(MISSING_SYMBOLS)} missing symbols...", flush=True)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365 * 7) # Past 7 Years
    
    for original_sym in MISSING_SYMBOLS:
        ticker = get_ticker_symbol(original_sym)
        print(f"[*] Downloading {original_sym} ({ticker})...", flush=True)
        try:
            def _fetch():
                return yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
            
            df = await asyncio.to_thread(_fetch)
            
            if df.empty:
                # Fallback to BSE (.BO) if NSE (.NS) returns empty
                alternative_ticker = ticker.replace(".NS", ".BO")
                print(f"[*] Falling back to BSE: {alternative_ticker}...", flush=True)
                def _fetch_alt():
                    return yf.download(alternative_ticker, start=start_date, end=end_date, interval="1d", progress=False)
                df = await asyncio.to_thread(_fetch_alt)
                
                if df.empty:
                    print(f"[-] No data found for {original_sym} on NSE or BSE", flush=True)
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
            
            if records:
                async with async_session() as session:
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
                print(f"[+] Ingested {len(records)} rows for {original_sym}", flush=True)
            
        except Exception as e:
            print(f"[-] Error processing {original_sym}: {e}", flush=True)
            
        # Small delay between tickers to avoid rate limit
        await asyncio.sleep(1.0)
        
    print("[*] Ingestion of missing symbols completed!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
