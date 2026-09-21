from datetime import datetime, timezone
from .paper import trades

def summary():
    closed = [t for t in trades if t.status == "CLOSED"]
    pnl = sum((t.pnl or 0) for t in closed)
    wins = sum(1 for t in closed if (t.pnl or 0) > 0)
    losses = sum(1 for t in closed if (t.pnl or 0) < 0)
    return {
        "closed_trades": len(closed),
        "wins": wins,
        "losses": losses,
        "win_rate_percent": round(wins / len(closed) * 100, 2) if closed else 0,
        "total_pnl": round(pnl, 8),
    }

def export_rows():
    return [{
        "id": t.id, "symbol": t.symbol, "side": t.side,
        "entry": t.entry, "exit": t.exit, "quantity": t.quantity,
        "pnl": t.pnl, "status": t.status,
        "opened_at": t.opened_at, "closed_at": t.closed_at
    } for t in trades]
