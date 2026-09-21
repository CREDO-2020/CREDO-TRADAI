from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from uuid import uuid4

@dataclass
class Trade:
    id: str
    symbol: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    quantity: float
    status: str = "OPEN"
    exit: float | None = None
    pnl: float | None = None
    opened_at: str = ""
    closed_at: str | None = None

trades: list[Trade] = []

def open_trade(symbol, side, entry, stop_loss, take_profit, quantity):
    trade = Trade(
        id=str(uuid4())[:8], symbol=symbol.upper(), side=side.upper(),
        entry=entry, stop_loss=stop_loss, take_profit=take_profit,
        quantity=quantity,
        opened_at=datetime.now(timezone.utc).isoformat()
    )
    trades.append(trade)
    return asdict(trade)

def close_trade(trade_id, exit_price):
    for trade in trades:
        if trade.id == trade_id and trade.status == "OPEN":
            direction = 1 if trade.side == "LONG" else -1
            trade.exit = exit_price
            trade.pnl = round((exit_price - trade.entry) * trade.quantity * direction, 8)
            trade.status = "CLOSED"
            trade.closed_at = datetime.now(timezone.utc).isoformat()
            return asdict(trade)
    return None

def list_trades():
    return [asdict(t) for t in reversed(trades)]
