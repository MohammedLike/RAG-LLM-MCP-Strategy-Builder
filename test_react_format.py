import requests
import json

url = "http://localhost:8001/api/backtest"
payload = {
    "symbol": "NIFTY",
    "period": "1y",
    "strategy_spec": {
        "entry": {
            "conditions": [
                {
                    "indicator": "RSI",
                    "params": {"timeperiod": 14},
                    "operator": "<",
                    "value": 30
                }
            ],
            "logical_operator": "AND"
        },
        "exit": {
            "conditions": [
                {
                    "indicator": "RSI",
                    "params": {"timeperiod": 14},
                    "operator": ">",
                    "value": 70
                }
            ],
            "logical_operator": "AND"
        },
        "instrument_type": "EQUITY",
        "fees": 0.001,
        "slippage": 0.001
    }
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
try:
    data = response.json()
    print(f"Total Return: {data.get('total_return')}")
    print(f"Trades Count: {len(data.get('trades', []))}")
    print(f"Equity Curve Length: {len(data.get('equity_curve', []))}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response (raw): {response.text[:500]}...")
