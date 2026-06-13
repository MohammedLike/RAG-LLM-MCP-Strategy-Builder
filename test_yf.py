import yfinance as yf
import pandas as pd

symbol = "^NSEI"
data = yf.download(symbol, period="1y", interval="1d")
print(f"Data for {symbol}:")
print(data.head())
print(f"Empty: {data.empty}")
print(f"Columns: {data.columns}")
