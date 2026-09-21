import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

DB = Path(__file__).parent.parent / "trades.db"
MAX_OPEN_TRADES = 3
MAX_DAILY_LOSS = 0.03

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY, symbol TEXT NOT NULL, side TEXT NOT NULL,
            entry REAL NOT NULL, stop_loss REAL NOT NULL, take_profit REAL NOT NULL,
            quantity REAL NOT NULL, status TEXT NOT NULL, exit REAL, pnl REAL,
            opened_at TEXT NOT NULL, closed_at TEXT)""")

def _today_pnl(db):
    row = db.execute("""SELECT COALESCE(SUM(pnl),0) pnl FROM trades
        WHERE status='CLOSED' AND closed_at >= date('now')""").fetchone()
    return float(row["pnl"])

def _open_count(db):
    row = db.execute("SELECT COUNT(*) n FROM trades WHERE status='OPEN'").fetchone()
    return int(row["n"])

def open_trade(symbol, side, entry, stop_loss, take_profit, quantity):
    side = side.upper()
    if side == "LONG" and not (stop_loss < entry < take_profit):
        raise ValueError("LONG requires stop-loss < entry < take-profit")
    if side == "SHORT" and not (take_profit < entry < stop_loss):
        raise ValueError("SHORT requires take-profit < entry < stop-loss")
    with conn() as db:
        if _open_count(db) >= MAX_OPEN_TRADES:
            raise ValueError(f"Maximum open paper trades reached ({MAX_OPEN_TRADES})")
    trade = (str(uuid4())[:8], symbol.upper(), side, entry, stop_loss, take_profit,
             quantity, "OPEN", None, None, datetime.now(timezone.utc).isoformat(), None)
    with conn() as db:
        db.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", trade)
    return get_trade(trade[0])

def get_trade(trade_id):
    with conn() as db:
        row = db.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
        return dict(row) if row else None

def close_trade(trade_id, exit_price):
    with conn() as db:
        row = db.execute("SELECT * FROM trades WHERE id=? AND status='OPEN'", (trade_id,)).fetchone()
        if not row:
            return None
        direction = 1 if row["side"] == "LONG" else -1
        pnl = round((exit_price - row["entry"]) * row["quantity"] * direction, 8)
        db.execute("UPDATE trades SET exit=?, pnl=?, status='CLOSED', closed_at=? WHERE id=?",
                   (exit_price, pnl, datetime.now(timezone.utc).isoformat(), trade_id))
    return get_trade(trade_id)

def list_trades():
    with conn() as db:
        rows = db.execute("SELECT * FROM trades ORDER BY opened_at DESC").fetchall()
        return [dict(r) for r in rows]

def summary():
    with conn() as db:
        row = db.execute("""SELECT COUNT(*) count,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) wins,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) losses,
            COALESCE(SUM(pnl),0) pnl FROM trades WHERE status='CLOSED'""").fetchone()
        open_count = _open_count(db)
    count, wins, losses, pnl = row["count"], row["wins"] or 0, row["losses"] or 0, row["pnl"]
    return {"closed_trades": count, "wins": wins, "losses": losses,
            "win_rate_percent": round(wins/count*100,2) if count else 0,
            "total_pnl": round(pnl,8), "open_trades": open_count,
            "max_open_trades": MAX_OPEN_TRADES}
