import os
from datetime import datetime, timezone
from uuid import uuid4

TRADING_MODE = os.getenv("TRADING_MODE", "demo").lower()
LIVE_TRADING_ENABLED = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"

def get_mode():
    if TRADING_MODE not in {"demo", "live"}:
        return "demo"
    return TRADING_MODE

def execute_order(symbol, side, quantity, order_type="MARKET", price=None):
    mode = get_mode()
    side = side.upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError("Side must be BUY or SELL")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    if mode == "live":
        if not LIVE_TRADING_ENABLED:
            raise PermissionError("Live trading is disabled. Set ENABLE_LIVE_TRADING=true only after configuring a broker adapter.")
        raise NotImplementedError("Live broker adapter is not configured yet.")

    return {
        "id": str(uuid4())[:8],
        "mode": "demo",
        "status": "SIMULATED",
        "symbol": symbol.upper(),
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "requested_price": price,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": "Demo order simulated. No real money was used."
    }
