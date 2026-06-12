import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime, timedelta

# Create mock data
dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(100)]
close = [100 + i + (5 if i % 10 == 0 else 0) for i in range(100)]
df = pd.DataFrame({'time': dates, 'close': close})

# Signals
entries = pd.Series(False, index=df.index)
entries.iloc[10] = True
entries.iloc[30] = True

exits = pd.Series(False, index=df.index)
exits.iloc[20] = True
exits.iloc[40] = True

# Run VectorBT without datetime index
portfolio = vbt.Portfolio.from_signals(df['close'], entries, exits)
print("--- Records Readable (Integer Index) ---")
print(portfolio.trades.records_readable.columns)
print(portfolio.trades.records_readable.head())

# Run VectorBT with datetime index
df_dt = df.set_index('time')
entries_dt = entries.copy()
entries_dt.index = df_dt.index
exits_dt = exits.copy()
exits_dt.index = df_dt.index

portfolio_dt = vbt.Portfolio.from_signals(df_dt['close'], entries_dt, exits_dt)
print("\n--- Records Readable (Datetime Index) ---")
print(portfolio_dt.trades.records_readable.columns)
print(portfolio_dt.trades.records_readable.head())
