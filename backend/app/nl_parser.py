import re
from typing import Optional

class NLParser:
    """
    Parses natural language backtest requests into structured strategy specs.
    Falls back to LLM if no pattern matches.
    """

    PATTERNS = {
        "rsi_mean_reversion": re.compile(
            r"(?:backtest|run|test)?\s*(?P<symbol>NIFTY|BANKNIFTY|RELIANCE|TCS|INFY|HDFCBANK|SBI|ICICIBANK)?\s*"
            r"(?:when|if|:)?\s*RSI\s*(?:crosses\s*)?(?P<op>below|above|<|>)\s*(?P<entry_val>\d+)"
            r"(?:.*?exit\s*(?:when|at|:)?\s*RSI\s*(?:crosses\s*)?(?P<exit_op>above|below|>|<)\s*(?P<exit_val>\d+))?"
            r"(?:.*?for\s*(?P<period>\d+\s*(?:year|y)))?"
            r"(?:.*?\bon\s+(?P<symbol_alt>NIFTY|BANKNIFTY|RELIANCE|TCS|INFY|HDFCBANK))?",
            re.IGNORECASE
        ),
        "sma_crossover": re.compile(
            r"(?:backtest|run|test)?\s*(?P<symbol>NIFTY|BANKNIFTY|RELIANCE|TCS|INFY|HDFCBANK)?\s*"
            r"(?:when|:)?\s*SMA\s*(?P<fast>\d+)\s*(?:crosses\s*)?(?P<op>above|below|over|under)\s*SMA\s*(?P<slow>\d+)"
            r"(?:.*?for\s*(?P<period>\d+\s*(?:year|y)))?"
            r"(?:.*?\bon\s+(?P<symbol_alt>NIFTY|BANKNIFTY|RELIANCE|TCS|INFY|HDFCBANK))?",
            re.IGNORECASE
        ),
        "options_strategy": re.compile(
            r"(?:backtest|run|test)?\s*(?P<symbol>NIFTY|BANKNIFTY|FINNIFTY)?\s*"
            r"(?:(?P<strike>ATM|OTM|ITM|OTM\+?\d*|ITM-?\d*)\s*)?"
            r"(?P<option_type>CE|PE|Straddle|strangle|Iron\s*Condor)"
            r"(?:.*?for\s*(?P<period>\d+\s*(?:year|y)))?"
            r"(?:.*?\bon\s+(?P<symbol_alt>NIFTY|BANKNIFTY|FINNIFTY))?",
            re.IGNORECASE
        ),
    }

    PERIOD_MAP = {"1 year": "1y", "2 year": "2y", "5 year": "5y", "8 year": "8y", "1y": "1y", "2y": "2y", "5y": "5y", "8y": "8y"}

    def _extract_symbol(self, text_lower: str) -> str:
        for sym in ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK", "SBI", "ICICIBANK", "FINNIFTY", "SENSEX"]:
            if sym.lower() in text_lower:
                return sym
        return "NIFTY"

    def _extract_period(self, text_lower: str) -> str:
        period_match = re.search(r"(\d+)\s*(?:y|year)s?", text_lower)
        if period_match:
            period = f"{period_match.group(1)}y"
            if period in ("1y", "2y", "5y", "8y"):
                return period
        return "1y"

    def _parse_adx(self, text_lower: str) -> Optional[dict]:
        if "adx" not in text_lower:
            return None
        if not re.search(r"[+\-]\s*di|plus\s*di|minus\s*di", text_lower):
            return None

        symbol = self._extract_symbol(text_lower)
        period = self._extract_period(text_lower)
        adx_period = 14
        adx_p = re.search(r"adx\s*\(\s*(\d+)\s*\)", text_lower)
        if adx_p:
            adx_period = int(adx_p.group(1))

        adx_thresh = 25.0
        thresh_m = re.search(r"adx[^0-9]*(?:is\s+)?(?:above|>)\s*(\d+)", text_lower)
        if thresh_m:
            adx_thresh = float(thresh_m.group(1))

        stop_loss = 2.0
        sl_m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*stop", text_lower)
        if sl_m:
            stop_loss = float(sl_m.group(1))

        di_params = {"timeperiod": adx_period}
        return {
            "action": "run_backtest",
            "symbol": symbol,
            "period": period,
            "instrument_type": "EQUITY",
            "strategy_spec": {
                "entry": {
                    "conditions": [
                        {"indicator": "ADX", "params": di_params, "operator": ">", "value": adx_thresh},
                        {
                            "indicator": "PLUS_DI",
                            "params": di_params,
                            "operator": "crosses_above",
                            "value": {"indicator": "MINUS_DI", "params": di_params},
                        },
                    ],
                    "logical_operator": "AND",
                },
                "exit": {
                    "conditions": [
                        {
                            "indicator": "PLUS_DI",
                            "params": di_params,
                            "operator": "crosses_below",
                            "value": {"indicator": "MINUS_DI", "params": di_params},
                        },
                    ],
                    "logical_operator": "OR",
                },
                "stop_loss": stop_loss,
                "take_profit": 5.0,
            },
        }

    def _parse_rsi(self, text_lower: str) -> Optional[dict]:
        if "rsi" not in text_lower:
            return None

        symbol = self._extract_symbol(text_lower)
        period = self._extract_period(text_lower)
        rsi_period = 14
        rsi_p = re.search(r"rsi\s*\(\s*(\d+)\s*\)", text_lower)
        if rsi_p:
            rsi_period = int(rsi_p.group(1))

        entry_val, exit_val = 30.0, 70.0
        entry_op, exit_op = "crosses_below", "crosses_above"

        buy_match = re.search(
            r"(?:buy|enter|long)\s+when\s+rsi[^0-9]*(?:\(\s*\d+\s*\))?[^.]*?(crosses\s+)?(below|above|<|>)\s*(\d+)",
            text_lower,
        )
        exit_match = re.search(
            r"exit\s+when\s+rsi[^0-9]*(?:\(\s*\d+\s*\))?[^.]*?(crosses\s+)?(above|below|>|<)\s*(\d+)",
            text_lower,
        )
        if buy_match:
            entry_op = "crosses_below" if buy_match.group(2) in ("below", "<") else "crosses_above"
            entry_val = float(buy_match.group(3))
        if exit_match:
            exit_op = "crosses_above" if exit_match.group(2) in ("above", ">") else "crosses_below"
            exit_val = float(exit_match.group(3))

        if not buy_match and not exit_match:
            nums = [float(n) for n in re.findall(r"\b\d+\.?\d*\b", text_lower) if 5 < float(n) < 95]
            if len(nums) >= 2:
                entry_val = min(nums)
                exit_val = max(nums)
            elif len(nums) == 1:
                val = nums[0]
                if val <= 50:
                    entry_val = val
                else:
                    exit_val = val

        return {
            "action": "run_backtest",
            "symbol": symbol,
            "period": period,
            "instrument_type": "EQUITY",
            "strategy_spec": {
                "entry": {
                    "conditions": [
                        {"indicator": "RSI", "params": {"timeperiod": rsi_period}, "operator": entry_op, "value": entry_val}
                    ],
                    "logical_operator": "AND",
                },
                "exit": {
                    "conditions": [
                        {"indicator": "RSI", "params": {"timeperiod": rsi_period}, "operator": exit_op, "value": exit_val}
                    ],
                    "logical_operator": "AND",
                },
                "stop_loss": 2.0,
                "take_profit": 5.0,
            },
        }

    def parse(self, text: str) -> Optional[dict]:
        text_lower = text.lower()

        adx = self._parse_adx(text_lower)
        if adx:
            return adx

        rsi = self._parse_rsi(text_lower)
        if rsi:
            return rsi

        for name, pattern in self.PATTERNS.items():
            match = pattern.search(text)
            if match:
                try:
                    return self._build_spec(name, match)
                except (ValueError, TypeError, AttributeError):
                    continue

        # Fallback Heuristic Parser
        symbol = self._extract_symbol(text_lower)
        period = self._extract_period(text_lower)
                
        # 3. Check for Options Strategy
        options_keywords = ["straddle", "strangle", "iron condor", "option"]
        is_option = any(kw in text_lower for kw in options_keywords) or bool(re.search(r"\b(?:ce|pe)\b", text_lower))
        
        if is_option:
            strike = "ATM"
            if "itm-2" in text_lower: strike = "ITM-2"
            elif "itm-1" in text_lower: strike = "ITM-1"
            elif "otm+1" in text_lower: strike = "OTM+1"
            elif "otm+2" in text_lower: strike = "OTM+2"
            elif "otm" in text_lower: strike = "OTM"
            elif "itm" in text_lower: strike = "ITM"
            
            option_type = "CE"
            if "pe" in text_lower or "put" in text_lower:
                option_type = "PE"
            elif any(kw in text_lower for kw in ["straddle", "strangle", "iron condor"]):
                option_type = "STRADDLE"
                
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "OPTION",
                "strategy_spec": {
                    "instrument_type": "OPTION",
                    "strike": strike, "option_type": option_type,
                    "entry": {"conditions": [], "logical_operator": "AND"},
                    "exit": {"conditions": [], "logical_operator": "AND"},
                    "stop_loss": 20.0, "take_profit": 50.0
                }
            }
            
        # 4. Check for SMA/EMA Crossover
        if "sma" in text_lower or "ema" in text_lower:
            nums = [int(n) for n in re.findall(r"\b\d+\b", text) if 2 < int(n) < 300]
            if len(nums) >= 2:
                fast = min(nums)
                slow = max(nums)
            else:
                fast = 20
                slow = 50
                
            op = "crosses_above"
            if any(w in text_lower for w in ["below", "under", "down"]):
                op = "crosses_below"
                
            exit_op = "crosses_below" if op == "crosses_above" else "crosses_above"
            ind_type = "EMA" if "ema" in text_lower else "SMA"
            
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "EQUITY",
                "strategy_spec": {
                    "entry": {"conditions": [{"indicator": ind_type, "params": {"timeperiod": fast}, "operator": op, "value": {"indicator": ind_type, "params": {"timeperiod": slow}}}], "logical_operator": "AND"},
                    "exit": {"conditions": [{"indicator": ind_type, "params": {"timeperiod": fast}, "operator": exit_op, "value": {"indicator": ind_type, "params": {"timeperiod": slow}}}], "logical_operator": "AND"},
                    "stop_loss": 2.0, "take_profit": 5.0
                }
            }
            
        return None

    def _build_spec(self, name: str, match: re.Match) -> dict:
        g = match.groupdict()
        symbol = (g.get("symbol") or g.get("symbol_alt") or "NIFTY").upper()
        period = g.get("period", "1y")
        period = self.PERIOD_MAP.get(period.strip().lower(), "1y") if period else "1y"

        if name == "rsi_mean_reversion":
            op = "<" if g.get("op", "below").lower() in ("below", "<") else ">"
            entry_val = float(g.get("entry_val", 30))
            exit_raw = g.get("exit_op") or "above"
            exit_op = ">" if str(exit_raw).lower() in ("above", ">") else "<"
            exit_val = float(g.get("exit_val", 70))
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "EQUITY",
                "strategy_spec": {
                    "entry": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": op, "value": entry_val}], "logical_operator": "AND"},
                    "exit": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": exit_op, "value": exit_val}], "logical_operator": "AND"},
                    "stop_loss": 2.0, "take_profit": 5.0
                }
            }

        if name == "sma_crossover":
            fast = int(g.get("fast", 20))
            slow = int(g.get("slow", 50))
            op = "crosses_above" if g.get("op", "above").lower() in ["above", "over"] else "crosses_below"
            exit_op = "crosses_below" if op == "crosses_above" else "crosses_above"
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "EQUITY",
                "strategy_spec": {
                    "entry": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": fast}, "operator": op, "value": {"indicator": "SMA", "params": {"timeperiod": slow}}}], "logical_operator": "AND"},
                    "exit": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": fast}, "operator": exit_op, "value": {"indicator": "SMA", "params": {"timeperiod": slow}}}], "logical_operator": "AND"},
                    "stop_loss": 2.0, "take_profit": 5.0
                }
            }

        if name == "options_strategy":
            strike = (g.get("strike") or "ATM").upper()
            option_type = (g.get("option_type") or "CE").upper()
            if "IRON" in option_type: option_type = "STRADDLE"
            if "STRANGLE" in option_type: option_type = "STRADDLE"
            return {
                "action": "run_backtest",
                "symbol": symbol, "period": period,
                "instrument_type": "OPTION",
                "strategy_spec": {
                    "instrument_type": "OPTION",
                    "strike": strike, "option_type": option_type,
                    "entry": {"conditions": [], "logical_operator": "AND"},
                    "exit": {"conditions": [], "logical_operator": "AND"},
                    "stop_loss": 20.0, "take_profit": 50.0
                }
            }

        return None

nl_parser = NLParser()
