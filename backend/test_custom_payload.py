import urllib.request
import json
import asyncio

async def test():
    # Construct exact payload sent by client-side parser
    payload = {
        "strategy_spec": {
            "entry": {
                "conditions": [
                    {
                        "indicator": "RSI",
                        "params": {"timeperiod": 14},
                        "operator": "<",
                        "value": 35.0
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
                        "value": 70.0
                    }
                ],
                "logical_operator": "AND"
            },
            "stop_loss": 0.02,
            "take_profit": 0.05,
            "fees": 0.001,
            "slippage": 0.001
        },
        "symbol": "NIFTY",
        "period": "2y"
    }

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/backtest",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        res = urllib.request.urlopen(req)
        result = json.loads(res.read().decode())
        print("API Response keys:", list(result.keys()))
        print("Total Return:", result.get("total_return"))
        print("Trades count:", len(result.get("trades", [])))
        print("Equity curve length:", len(result.get("equity_curve", [])))
    except Exception as e:
        print("API Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
