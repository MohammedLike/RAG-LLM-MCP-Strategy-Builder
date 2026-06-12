import yfinance as yf
import pandas as pd
from datetime import datetime
from .provider_base import MarketDataProvider
import asyncio

class YFinanceProvider(MarketDataProvider):
    
    # Mapping for common Indian indices
    SYMBOL_MAP = {
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "FINNIFTY": "CNXFIN.NS",
        "SENSEX": "^BSESN",
        "NIFTY100": "^CNX100",
        "NIFTY500": "^CRSLDX"
    }

    def _get_ticker(self, symbol: str) -> str:
        symbol = symbol.upper()
        if symbol in self.SYMBOL_MAP:
            return self.SYMBOL_MAP[symbol]
        
        # If user explicitly provided suffix
        if symbol.endswith(".NS") or symbol.endswith(".BO") or symbol.startswith("^"):
            return symbol
            
        # Default to NSE
        return f"{symbol}.NS"

    async def get_quote(self, symbol: str) -> dict:
        ticker = self._get_ticker(symbol)
        def _fetch():
            t = yf.Ticker(ticker)
            info = t.fast_info
            return {
                "symbol": symbol,
                "ltp": info.last_price,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "yfinance"
            }
        return await asyncio.to_thread(_fetch)

    async def get_ohlcv(self, symbol: str, interval: str, start: datetime, end: datetime) -> pd.DataFrame:
        # Check database first
        from ..db.session import async_session, is_db_available
        from sqlalchemy import text
        
        if is_db_available():
            try:
                async with async_session() as session:
                    # Normalize symbol (e.g., NIFTY instead of ^NSEI or NIFTY.NS)
                    clean_symbol = symbol.replace("^", "").replace(".NS", "").upper()
                    query = text("""
                        SELECT time, open, high, low, close, volume
                        FROM ohlcv
                        WHERE (symbol = :symbol OR symbol = :clean_symbol)
                          AND resolution = :resolution
                          AND time >= :start
                          AND time <= :end
                        ORDER BY time ASC
                    """)
                    result = await session.execute(query, {
                        "symbol": symbol,
                        "clean_symbol": clean_symbol,
                        "resolution": interval,
                        "start": start,
                        "end": end
                    })
                    rows = result.fetchall()
                    if rows:
                        print(f"Loaded {len(rows)} OHLCV rows for {symbol} ({interval}) from DB.")
                        df = pd.DataFrame(rows, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                        df['symbol'] = symbol
                        # Ensure column names are lowercase
                        df.columns = [c.lower() for c in df.columns]
                        return df
            except Exception as e:
                print(f"Error loading OHLCV from DB: {e}. Falling back to yfinance.")

        ticker = self._get_ticker(symbol)
        def _fetch():
            return yf.download(ticker, start=start, end=end, interval=interval)
        
        df = await asyncio.to_thread(_fetch)
        
        # Format columns properly
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df.reset_index()
        # The index column is typically 'Date' or 'Datetime', but let's be explicit
        df = df.rename(columns={df.columns[0]: 'time'})
        
        # Ensure remaining column names match our schema lowercase
        df.columns = [c.lower() for c in df.columns]
        df['symbol'] = symbol
        return df


    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical data with local Parquet caching.
        """
        ticker = self._get_ticker(symbol)
        
        # Local File Cache Logic
        import os
        import time
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/ohlcv_cache"))
        os.makedirs(cache_dir, exist_ok=True)
        
        # Sanitize filename
        safe_ticker = ticker.replace("^", "").replace(".", "_")
        cache_file = os.path.join(cache_dir, f"{safe_ticker}_{period}_{interval}.parquet")
        
        use_cache = False
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 3600 * 12: # 12 hours cache
                use_cache = True
                
        def _fetch():
            if use_cache:
                try:
                    df = pd.read_parquet(cache_file)
                    if not df.empty:
                        return df
                except Exception as e:
                    print(f"Parquet Cache Read Error: {e}")
                    
            # Fallback to YFinance
            t = yf.Ticker(ticker)
            df = t.history(period=period, interval=interval)
            
            if df.empty:
                return df
                
            df = df.reset_index()
            df = df.rename(columns={df.columns[0]: 'time'})
            df.columns = [c.lower() for c in df.columns]
            df['symbol'] = symbol
            
            # Save to Cache
            try:
                df.to_parquet(cache_file, index=False)
            except Exception as e:
                print(f"Parquet Cache Write Error: {e}")
                
            return df
            
        return await asyncio.to_thread(_fetch)

    async def get_options_chain(self, symbol: str, expiry: str) -> dict:
        ticker = self._get_ticker(symbol)
        def _fetch():
            try:
                t = yf.Ticker(ticker)
                # If expiry is not provided, use the first available expiry
                if not expiry:
                    expirations = t.options
                    if not expirations:
                        return {"error": "No options expirations found."}
                    expiry = expirations[0]
                
                chain = t.option_chain(expiry)
                calls = chain.calls.to_dict(orient="records") if not chain.calls.empty else []
                puts = chain.puts.to_dict(orient="records") if not chain.puts.empty else []
                
                return {
                    "symbol": symbol,
                    "expiry": expiry,
                    "calls": calls,
                    "puts": puts,
                    "provider": "yfinance"
                }
            except Exception as e:
                return {"error": str(e)}
                
        return await asyncio.to_thread(_fetch)

    async def get_futures_data(self, symbol: str, expiry: str | None = None) -> dict:
        ticker = self._get_ticker(symbol)
        def _fetch():
            t = yf.Ticker(ticker)
            info = t.fast_info
            return {
                "symbol": symbol,
                "ltp": info.last_price,
                "expiry": expiry,
                "provider": "yfinance",
            }
        return await asyncio.to_thread(_fetch)

    async def get_equity_meta(self, symbol: str) -> dict:
        ticker = self._get_ticker(symbol)
        def _fetch():
            t = yf.Ticker(ticker)
            info = t.info
            return {
                "symbol": symbol,
                "name": info.get("shortName") or info.get("longName"),
                "exchange": info.get("exchange"),
                "currency": info.get("currency"),
                "provider": "yfinance",
            }
        return await asyncio.to_thread(_fetch)
