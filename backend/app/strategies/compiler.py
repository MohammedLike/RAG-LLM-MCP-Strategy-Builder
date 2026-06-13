import re
import json
from ..backtest.indicators import IndicatorManager

def _normalize_indicator_ref(ref: dict | float | int | str) -> dict | float | int | str:
    if isinstance(ref, dict) and "indicator" in ref:
        return {
            **ref,
            "indicator": IndicatorManager.normalize_name(ref["indicator"]),
        }
    return ref

def _normalize_condition(cond: dict) -> dict:
    normalized = dict(cond)
    if "indicator" in normalized:
        normalized["indicator"] = IndicatorManager.normalize_name(normalized["indicator"])
    if "value" in normalized:
        normalized["value"] = _normalize_indicator_ref(normalized["value"])
    return normalized

def _normalize_rule_group(rule_group: dict) -> dict:
    if not rule_group:
        return {}
    if "conditions" in rule_group:
        return {
            **rule_group,
            "conditions": [_normalize_condition(c) for c in rule_group.get("conditions", [])],
        }
    if "indicator" in rule_group:
        return _normalize_condition(rule_group)
    return rule_group

def _compile_exit_rules(exit_rules: dict) -> dict:
    if "condition" in exit_rules:
        return {
            "conditions": [_normalize_condition(parse_condition_str(exit_rules["condition"]))],
            "logical_operator": "AND",
        }
    if exit_rules.get("conditions"):
        return _normalize_rule_group(exit_rules)
    if any(k in exit_rules for k in ("target", "stop_loss", "take_profit")):
        # Risk-only exits are handled via strategy-level stop_loss / take_profit.
        return {}
    if "indicator" in exit_rules:
        return _normalize_condition(exit_rules)
    return {}

def parse_single_indicator(part: str) -> dict | float:
    part = part.strip()
    
    # Check if it's a number
    try:
        if '.' in part:
            return float(part)
        return int(part)
    except ValueError:
        pass
        
    # Check for basic OHLCV
    part_upper = part.upper()
    if part_upper in ["CLOSE", "CLOSE(0)", "CLOSE(-1)", "CLOSE(0)"]:
        return {"indicator": "CLOSE", "params": {}}
    if part_upper in ["OPEN", "OPEN(0)", "OPEN(-1)"]:
        return {"indicator": "OPEN", "params": {}}
    if part_upper in ["HIGH", "HIGH(0)", "HIGH(-1)"]:
        return {"indicator": "HIGH", "params": {}}
    if part_upper in ["LOW", "LOW(0)", "LOW(-1)"]:
        return {"indicator": "LOW", "params": {}}
    if part_upper in ["VOLUME", "VOLUME(0)", "VOLUME(-1)"]:
        return {"indicator": "VOLUME", "params": {}}

    # Handle functions like Name(args...)
    match = re.match(r"([A-Za-z0-9%\s_]+)\(([^)]+)\)", part)
    if match:
        name = match.group(1).strip().upper()
        args_str = match.group(2)
        args = [a.strip() for a in args_str.split(',')]
        
        # Determine period from args
        period = 14
        for arg in args:
            if arg.isdigit():
                period = int(arg)
                break
        
        # Standardize names
        if "MOVING AVERAGE" in name or name.strip().upper() == "MOVING_AVERAGE":
            args_lower = args_str.lower()
            if "hull" in args_lower:
                ind_name = "HMA"
            elif "vwma" in args_lower or "volume" in args_lower:
                ind_name = "VWMA"
            elif "weighted" in args_lower or "wma" in args_lower:
                ind_name = "WMA"
            elif "exponential" in args_lower or "ema" in args_lower:
                ind_name = "EMA"
            elif "dema" in args_lower or "double" in args_lower:
                ind_name = "DEMA"
            elif "tema" in args_lower or "triple" in args_lower:
                ind_name = "TEMA"
            else:
                ind_name = "SMA"
        elif "SMA" in name or "SIMPLE" in name:
            ind_name = "SMA"
        elif "EMA" in name or "EXPONENTIAL" in name:
            ind_name = "EMA"
        elif "DEMA" in name:
            ind_name = "DEMA"
        elif "TEMA" in name:
            ind_name = "TEMA"
        elif "WMA" in name:
            ind_name = "WMA"
        elif "RSI" in name:
            ind_name = "RSI"
        elif "MACD" in name:
            ind_name = "MACD"
        elif "BOLLINGER" in name or "BBANDS" in name:
            ind_name = "BBANDS"
        elif "ATR" in name:
            ind_name = "ATR"
        elif "ADX" in name:
            ind_name = "ADX"
        elif "CCI" in name:
            ind_name = "CCI"
        elif "STOCH" in name:
            ind_name = "STOCH"
        elif "OBV" in name:
            ind_name = "OBV"
        elif "MOM" in name or "MOMENTUM" in name:
            ind_name = "MOM"
        elif "ROC" in name:
            ind_name = "ROC"
        elif "MFI" in name:
            ind_name = "MFI"
        elif "KAMA" in name:
            ind_name = "KAMA"
        elif "TSF" in name:
            ind_name = "TSF"
        elif "VWAP" in name:
            ind_name = "VWAP"
        elif "ALLIGATOR" in name:
            # lips = 5, teeth = 8, jaw = 13
            ind_name = "SMA"
            if "LIPS" in args_str.upper():
                period = 5
            elif "TEETH" in args_str.upper():
                period = 8
            elif "JAW" in args_str.upper():
                period = 13
        elif "PIVOT" in name:
            ind_name = "MIDPOINT"
        elif "NTH CANDLE" in name:
            if "HIGH" in args_str.upper():
                return {"indicator": "HIGH", "params": {}}
            elif "LOW" in args_str.upper():
                return {"indicator": "LOW", "params": {}}
            else:
                return {"indicator": "CLOSE", "params": {}}
        else:
            ind_name = name
            
        return {
            "indicator": IndicatorManager.normalize_name(ind_name),
            "params": {"timeperiod": period}
        }
        
    return {"indicator": "CLOSE", "params": {}}

def parse_operator(op_str: str) -> str:
    op_str = op_str.strip().lower()
    if op_str == "crosses above":
        return "crosses_above"
    if op_str == "crosses below":
        return "crosses_below"
    if op_str in ["higher than", ">"]:
        return ">"
    if op_str in ["lower than", "<"]:
        return "<"
    if op_str in ["equal to", "==", "="]:
        return "=="
    return "=="

def parse_condition_str(cond_str: str) -> dict:
    operators = ["crosses above", "crosses below", "higher than", "lower than", "equal to", ">", "<", "=="]
    for op in operators:
        if op in cond_str.lower():
            # Split by first occurrence of the operator
            idx = cond_str.lower().find(op)
            lhs_str = cond_str[:idx]
            rhs_str = cond_str[idx + len(op):]
            
            lhs = parse_single_indicator(lhs_str)
            rhs = parse_single_indicator(rhs_str)
            operator = parse_operator(op)
            
            if isinstance(lhs, dict):
                return {
                    "indicator": lhs["indicator"],
                    "params": lhs["params"],
                    "operator": operator,
                    "value": rhs
                }
    return {"indicator": "CLOSE", "operator": ">", "value": 0}

def compile_db_strategy(db_strat: dict) -> dict:
    entry_rules = db_strat.get("entry_rules")
    if isinstance(entry_rules, str):
        entry_rules = json.loads(entry_rules)
    elif not entry_rules:
        entry_rules = {}

    exit_rules = db_strat.get("exit_rules")
    if isinstance(exit_rules, str):
        exit_rules = json.loads(exit_rules)
    elif not exit_rules:
        exit_rules = {}

    # Check for string condition format (auto-generated)
    if "condition" in entry_rules:
        cond_str = entry_rules["condition"]
        compiled_entry = {
            "conditions": [_normalize_condition(parse_condition_str(cond_str))],
            "logical_operator": "AND"
        }
    else:
        compiled_entry = _normalize_rule_group(entry_rules)

    compiled_exit = _compile_exit_rules(exit_rules)

    # Handle Options format
    instrument_type = db_strat.get("category", "Equity")
    if "Option" in instrument_type or db_strat.get("entry_rules", {}).get("instrument_type") == "OPTION":
        instrument_type = "OPTION"
    else:
        instrument_type = "EQUITY"

    risk_params = db_strat.get("risk_params") or {}
    if isinstance(risk_params, str):
        risk_params = json.loads(risk_params)
        
    stop_loss = 2.0
    take_profit = 5.0
    
    # Try to extract stop_loss / take_profit
    sl_val = risk_params.get("stop_loss") or exit_rules.get("stop_loss")
    tp_val = risk_params.get("take_profit") or exit_rules.get("target") or risk_params.get("take_profit")
    
    if sl_val is not None:
        if isinstance(sl_val, str) and "%" in sl_val:
            stop_loss = float(sl_val.replace("%", ""))
        else:
            try:
                stop_loss = float(sl_val)
            except:
                pass
                
    if tp_val is not None:
        if isinstance(tp_val, str) and "%" in tp_val:
            take_profit = float(tp_val.replace("%", ""))
        else:
            try:
                take_profit = float(tp_val)
            except:
                pass

    return {
        "instrument_type": instrument_type,
        "entry": compiled_entry,
        "exit": compiled_exit,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }
