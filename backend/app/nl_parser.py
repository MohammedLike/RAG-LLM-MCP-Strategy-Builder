import re
from typing import Optional

class NLParser:
    """
    Parses natural language backtest requests into structured strategy specs.
    Falls back to LLM if no pattern matches.
    """

    PATTERNS = {
        "rsi_mean_reversion": re.compile(
            r"(?:backtest|run|test)?\s*(?P<symbol>NIFTY|BANKNIFTY|RELIANCE|TCS|INFY|HDFCBANK|SBI|ICICIBANK)\s*"
            r"(?:when|if|:)?\s*RSI\s*(?:crosses\s*)?(?P<op>below|above|<|>)\s*(?P<entry_val>\d+)"
            r"(?:.*?exit\s*(?:when|at|:)?\s*RSI\s*(?:crosses\s*)?(?P<exit_op>above|below|>|<)\s*(?P<exit_val>\d+))?"
            r"(?:.*?for\s*(?P<period>\d+\s*(?:year|y)))?",
            re.IGNORECASE
        ),
        "sma_crossover": re.compile(
            r"(?:backtest|run|test)?\s*(?P<symbol>NIFTY|BANKNIFTY|RELIANCE|TCS|INFY|HDFCBANK)\s*"
            r"(?:when|:)?\s*SMA\s*(?P<fast>\d+)\s*(?:crosses\s*)?(?P<op>above|below)\s*SMA\s*(?P<slow>\d+)"
            r"(?:.*?for\s*(?P<period>\d+\s*(?:year|y)))?",
            re.IGNORECASE
        ),
        "options_strategy": re.compile(
            r"(?:backtest|run|test)?\s*(?P<symbol>NIFTY|BANKNIFTY|FINNIFTY)\s*"
            r"(?:(?P<strike>ATM|OTM|ITM|OTM\+?\d*|ITM-?\d*)\s*)?"
            r"(?P<option_type>CE|PE|Straddle|strangle|Iron\s*Condor)"
            r"(?:.*?for\s*(?P<period>\d+\s*(?:year|y)))?",
            re.IGNORECASE
        ),
        "generic_strategy": re.compile(
            r"""(?:backtest|run|test)\s*(?P<symbol>[A-Z]+)"""
            r"""(?:.*?period\s*(?P<period>\d+\s*y))?"""
            r"""(?:.*?entry\s*(?P<entry_indicator>[A-Z]+)\s*(?P<entry_op><|>|=)\s*(?P<entry_val>\d+\.?\d*))?"""
            r"""(?:.*?exit\s*(?P<exit_indicator>[A-Z]+)\s*(?P<exit_op><|>|=)\s*(?P<exit_val>\d+\.?\d*))?""",
            re.IGNORECASE
        ),
    }

    PERIOD_MAP = {"1 year": "1y", "2 year": "2y", "5 year": "5y", "8 year": "8y", "1y": "1y", "2y": "2y", "5y": "5y", "8y": "8y"}

    def parse(self, text: str) -> Optional[dict]:
        for name, pattern in self.PATTERNS.items():
            match = pattern.search(text)
            if match:
                return self._build_spec(name, match)
        return None

    def _build_spec(self, name: str, match: re.Match) -> dict:
        g = match.groupdict()
        symbol = (g.get("symbol") or "NIFTY").upper()
        period = g.get("period", "2y")
        period = self.PERIOD_MAP.get(period.strip().lower(), "2y") if period else "2y"

        if name == "rsi_mean_reversion":
            op = "<" if g.get("op", "below").lower() in ("below", "<") else ">"
            entry_val = float(g.get("entry_val", 30))
            exit_op = ">" if g.get("exit_op", "above").lower() in ("above", ">") else "<"
            exit_val = float(g.get("exit_val", 70))
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "EQUITY",
                "strategy_spec": {
                    "entry": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": op, "value": entry_val}], "logical_operator": "AND"},
                    "exit": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": exit_op, "value": exit_val}], "logical_operator": "AND"}
                }
            }

        if name == "sma_crossover":
            fast = int(g.get("fast", 20))
            slow = int(g.get("slow", 50))
            op = "crosses_above" if g.get("op", "above").lower() == "above" else "crosses_below"
            exit_op = "crosses_below" if op == "crosses_above" else "crosses_above"
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "EQUITY",
                "strategy_spec": {
                    "entry": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": fast}, "operator": op, "value": {"indicator": "SMA", "params": {"timeperiod": slow}}}], "logical_operator": "AND"},
                    "exit": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": fast}, "operator": exit_op, "value": {"indicator": "SMA", "params": {"timeperiod": slow}}}], "logical_operator": "AND"}
                }
            }

        if name == "options_strategy":
            strike = (g.get("strike") or "ATM").upper()
            option_type = (g.get("option_type") or "CE").upper()
            if option_type == "IRON CONDOR":
                option_type = "STRADDLE"
            if option_type == "STRANGLE":
                option_type = "STRADDLE"
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "OPTION",
                "strategy_spec": {
                    "instrument_type": "OPTION",
                    "strike": strike, "option_type": option_type,
                    "entry": {"conditions": [], "logical_operator": "AND"},
                    "exit": {"conditions": [], "logical_operator": "AND"}
                }
            }

        return None

nl_parser = NLParser()
