"""Paper broker — simulated order fills for live strategy automation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


class PaperBroker:
    """Simulates market orders at latest close price."""

    def __init__(self, initial_capital: float = 100_000.0):
        self.initial_capital = initial_capital

    def execute(
        self,
        strategy: dict,
        side: str,
        price: float,
        quantity: int,
        reason: str,
    ) -> dict[str, Any]:
        position = strategy.get("position") or {"side": "flat", "qty": 0, "avg_price": 0.0}
        orders = strategy.get("orders") or []
        cash = float(strategy.get("cash", self.initial_capital))

        order = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.utcnow().isoformat(),
            "side": side.upper(),
            "symbol": strategy.get("symbol"),
            "price": round(price, 4),
            "quantity": quantity,
            "reason": reason,
            "mode": "paper",
            "status": "filled",
        }

        side_u = side.upper()
        if side_u == "BUY" and position.get("side") == "flat":
            cost = price * quantity
            if cost > cash:
                order["status"] = "rejected"
                order["error"] = "Insufficient paper capital"
                orders.append(order)
                strategy["orders"] = orders[-100:]
                return order
            position = {"side": "long", "qty": quantity, "avg_price": price, "entry_time": order["timestamp"]}
            cash -= cost
        elif side_u == "SELL" and position.get("side") == "long" and position.get("qty", 0) > 0:
            qty = min(quantity, position["qty"])
            proceeds = price * qty
            entry = position["avg_price"] * qty
            pnl = proceeds - entry
            order["pnl"] = round(pnl, 2)
            order["quantity"] = qty
            cash += proceeds
            position = {"side": "flat", "qty": 0, "avg_price": 0.0}
        else:
            order["status"] = "skipped"
            order["error"] = f"No action: position={position.get('side')}, side={side_u}"

        orders.append(order)
        strategy["position"] = position
        strategy["cash"] = round(cash, 2)
        strategy["orders"] = orders[-100:]
        return order


def broker_for_mode(mode: str) -> PaperBroker:
    if mode == "live":
        from ..config import settings
        if not settings.BROKER_ACCESS_TOKEN:
            raise RuntimeError(
                "Live broker not connected. Set BROKER_ACCESS_TOKEN in .env (Zerodha Kite / Angel SmartAPI)."
            )
        # Future: return KiteBroker(...)
        raise RuntimeError("Live broker adapter coming soon — use paper mode to validate signals.")
    return PaperBroker()
