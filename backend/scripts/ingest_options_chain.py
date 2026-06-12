"""
Download and store historical options chain snapshots for NIFTY/BANKNIFTY.
Uses yfinance to fetch options data.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from app.market.provider_yfinance import YFinanceProvider
from app.db.session import get_db
from app.db.models import OptionsChain
from sqlalchemy import text

provider = YFinanceProvider()

SYMBOLS = ["NIFTY", "BANKNIFTY"]

async def ingest_options_chain(symbol: str, expiry: str = None):
    print(f"Fetching options chain for {symbol} expiry {expiry}...")
    result = await provider.get_options_chain(symbol, expiry)
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    calls = result.get("calls", [])
    puts = result.get("puts", [])
    print(f"  Calls: {len(calls)}, Puts: {len(puts)}")

    async for db in get_db():
        for opt_type, contracts in [("CE", calls), ("PE", puts)]:
            for contract in contracts:
                try:
                    entry = OptionsChain(
                        time=datetime.utcnow(),
                        symbol=symbol,
                        expiry=pd.to_datetime(result.get("expiry")).date(),
                        strike=float(contract.get("strike", 0)),
                        option_type=opt_type,
                        oi=int(contract.get("openInterest", 0)),
                        volume=int(contract.get("volume", 0)),
                        iv=float(contract.get("impliedVolatility", 0)),
                        ltp=float(contract.get("lastPrice", 0)),
                    )
                    db.add(entry)
                except Exception as e:
                    print(f"  Error adding contract: {e}")
        await db.commit()
        print(f"  Stored {len(calls) + len(puts)} contracts for {symbol}")
        break

async def main():
    for symbol in SYMBOLS:
        await ingest_options_chain(symbol)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
