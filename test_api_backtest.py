import requests
import json

url = "http://localhost:8001/api/backtest"
payload = {
    "symbol": "NIFTY",
    "period": "1y",
    "strategy_spec": {
        "entry": {
            "indicator": "RSI",
            "params": {"timeperiod": 14},
            "operator": "<",
            "value": 30
        },
        "exit": {
            "indicator": "RSI",
            "params": {"timeperiod": 14},
            "operator": ">",
            "value": 70
        }
    }
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
try:
    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")
except:
    print(f"Response (raw): {response.text[:500]}...")
