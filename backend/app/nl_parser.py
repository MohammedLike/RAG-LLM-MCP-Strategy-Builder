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
        
        # Fallback Heuristic Parser
        text_lower = text.lower()
        
        # 1. Extract Symbol
        symbol = "NIFTY"  # default
        for sym in ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK", "SBI", "ICICIBANK", "FINNIFTY", "SENSEX", "NIFTY100", "NIFTY500"]:
            if sym.lower() in text_lower:
                symbol = sym
                break
                
        # 2. Extract Period
        period = "2y"  # default
        period_match = re.search(r"(\d+)\s*(?:y|year)s?", text_lower)
        if period_match:
            p_val = period_match.group(1)
            period = f"{p_val}y"
            # Normalize to allowed periods
            if period not in ["1y", "2y", "5y", "8y"]:
                period = "2y"
                
        # 3. Check for Options Strategy
        options_keywords = ["straddle", "strangle", "iron condor", "option"]
        is_option = any(kw in text_lower for kw in options_keywords) or bool(re.search(r"\b(?:ce|pe)\b", text_lower))
        
        if is_option:
            strike = "ATM"
            if "itm-2" in text_lower or "itm -2" in text_lower: strike = "ITM-2"
            elif "itm-1" in text_lower or "itm -1" in text_lower: strike = "ITM-1"
            elif "otm+1" in text_lower or "otm +1" in text_lower: strike = "OTM+1"
            elif "otm+2" in text_lower or "otm +2" in text_lower: strike = "OTM+2"
            elif "otm" in text_lower: strike = "OTM"
            elif "itm" in text_lower: strike = "ITM"
            
            option_type = "CE"
            if "pe" in text_lower or "put" in text_lower:
                option_type = "PE"
            elif "straddle" in text_lower or "strangle" in text_lower or "iron condor" in text_lower:
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
            
        # 4. Check for SMA/EMA Crossover
        if "sma" in text_lower or "ema" in text_lower:
            nums = [int(n) for n in re.findall(r"\b\d+\b", text) if int(n) in [5, 9, 10, 20, 30, 50, 100, 200] or (2 < int(n) < 300)]
            sma_periods = [int(n) for n in re.findall(r"(?:sma|ema)\s*(?:period\s*)?(\d+)", text_lower)]
            if not sma_periods:
                sma_periods = [n for n in nums if n not in [1, 2, 5, 8]]
            
            if len(sma_periods) >= 2:
                fast = min(sma_periods)
                slow = max(sma_periods)
            else:
                fast = 20
                slow = 50
                
            op = "crosses_above"
            if "below" in text_lower or "under" in text_lower:
                op = "crosses_below"
                
            exit_op = "crosses_below" if op == "crosses_above" else "crosses_above"
            ind_type = "EMA" if "ema" in text_lower else "SMA"
            
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "EQUITY",
                "strategy_spec": {
                    "entry": {"conditions": [{"indicator": ind_type, "params": {"timeperiod": fast}, "operator": op, "value": {"indicator": ind_type, "params": {"timeperiod": slow}}}], "logical_operator": "AND"},
                    "exit": {"conditions": [{"indicator": ind_type, "params": {"timeperiod": fast}, "operator": exit_op, "value": {"indicator": ind_type, "params": {"timeperiod": slow}}}], "logical_operator": "AND"}
                }
            }
            
        # 5. Check for RSI Mean Reversion
        if "rsi" in text_lower:
            nums = [float(n) for n in re.findall(r"\b\d+\.?\d*\b", text) if 10 < float(n) < 90]
            entry_val = 30.0
            exit_val = 70.0
            
            if len(nums) >= 2:
                entry_val = min(nums)
                exit_val = max(nums)
            elif len(nums) == 1:
                val = nums[0]
                if val <= 50:
                    entry_val = val
                else:
                    exit_val = val
                    
            op = "<"
            if "above" in text_lower or ">" in text_lower:
                if len(nums) == 1 and nums[0] > 50:
                    exit_val = nums[0]
                op = ">"
                
            exit_op = ">"
            if "below" in text_lower or "<" in text_lower:
                exit_op = "<"
                
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "EQUITY",
                "strategy_spec": {
                    "entry": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": op, "value": entry_val}], "logical_operator": "AND"},
                    "exit": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": exit_op, "value": exit_val}], "logical_operator": "AND"}
                }
            }
            
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
