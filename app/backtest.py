from .strategy import explain

def run_backtest(closes, starting_balance=10000.0, risk_percent=1.0):
    if len(closes) < 60:
        return {"error": "Need at least 60 closing prices."}
    if starting_balance <= 0 or not 0 < risk_percent <= 2:
        return {"error": "Starting balance must be positive and risk must be 0-2%."}
    balance = float(starting_balance)
    equity_peak = balance
    max_drawdown = 0.0
    wins = losses = 0
    trades = []
    equity_curve = [{"index": 0, "balance": round(balance, 2)}]

    for i in range(50, len(closes) - 1):
        action = explain(closes[:i + 1])["action"]
        if action == "WAIT":
            continue
        entry, next_price = closes[i], closes[i + 1]
        risk_amount = balance * risk_percent / 100
        stop_distance = entry * 0.005
        qty = risk_amount / stop_distance
        pnl = (next_price - entry) * qty if action == "WATCH_LONG" else (entry - next_price) * qty
        balance += pnl
        wins += int(pnl > 0)
        losses += int(pnl < 0)
        equity_peak = max(equity_peak, balance)
        drawdown = (equity_peak - balance) / equity_peak * 100
        max_drawdown = max(max_drawdown, drawdown)
        trades.append({"index": i, "action": action, "entry": entry, "exit": next_price, "pnl": round(pnl, 4)})
        equity_curve.append({"index": i, "balance": round(balance, 2)})

    total = len(trades)
    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    profit_factor = round(gross_profit / gross_loss, 3) if gross_loss else None
    return {
        "starting_balance": starting_balance,
        "ending_balance": round(balance, 2),
        "net_pnl": round(balance - starting_balance, 2),
        "return_percent": round((balance - starting_balance) / starting_balance * 100, 2),
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate_percent": round(wins / total * 100, 2) if total else 0,
        "max_drawdown_percent": round(max_drawdown, 2),
        "profit_factor": profit_factor,
        "equity_curve": equity_curve,
        "trade_log": trades[-100:],
        "note": "Educational backtest only; historical simulation is not a forecast and excludes fees, spreads, slippage and latency."
    }
