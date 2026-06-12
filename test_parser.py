from app.nl_parser import nl_parser
import json

text = "Backtest NIFTY RSI < 30, exit RSI > 70, 1y"
parsed = nl_parser.parse(text)
print(f"Parsed: {json.dumps(parsed, indent=2)}")
print(f"Params: {parsed.get('params', {})}")
