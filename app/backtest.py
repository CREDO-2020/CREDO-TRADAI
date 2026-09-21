from .strategy import explain

def run_backtest(closes, starting_balance=10000.0, risk_percent=1.0):
    if len(closes) < 60:
        return {"error": "Need at least 60 closing prices."}
    balance = float(starting_balance)
    equity_peak = balance
    max_drawdown = 0.0
    wins = losses = 0
    trades = []
    for i in range(50, len(closes) - 1):
        analysis = explain(closes[:i + 1])
        action = analysis["action"]
        if action == "WAIT":
            continue
        entry = closes[i]
        next_price = closes[i + 1]
        risk_amount = balance * risk_percent / 100
        stop_distance = entry * 0.005
        qty = risk_amount / stop_distance
        if action == "WATCH_LONG":
            pnl = (next_price - entry) * qty
        else:
            pnl = (entry - next_price) * qty
        balance += pnl
        wins += pnl > 0
        losses += pnl < 0
        equity_peak = max(equity_peak, balance)
        drawdown = (equity_peak - balance) / equity_peak * 100
        max_drawdown = max(max_drawdown, drawdown)
        trades.append({"index": i, "action": action, "entry": entry, "exit": next_price, "pnl": round(pnl, 4)})
    total = len(trades)
    return {
        "starting_balance": starting_balance,
        "ending_balance": round(balance, 2),
        "net_pnl": round(balance - starting_balance, 2),
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate_percent": round(wins / total * 100, 2) if total else 0,
        "max_drawdown_percent": round(max_drawdown, 2),
        "note": "Educational backtest only. It does not include spreads, fees, slippage or execution latency."
    }
