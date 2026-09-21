from .strategy import explain

def _validate(starting_balance, risk_percent, fee_bps, spread_bps, slippage_bps, sl, tp):
    if starting_balance <= 0 or not 0 < risk_percent <= 2:
        return "Starting balance must be positive and risk must be 0-2%."
    if min(fee_bps, spread_bps, slippage_bps, sl, tp) < 0:
        return "Costs and SL/TP percentages cannot be negative."
    if sl <= 0 or tp <= 0:
        return "SL and TP percentages must be positive."
    return None

def run_backtest(
    closes,
    starting_balance=10000.0,
    risk_percent=1.0,
    fee_bps=5.0,
    spread_bps=2.0,
    slippage_bps=1.0,
    stop_loss_percent=0.5,
    take_profit_percent=1.0,
    highs=None,
    lows=None,
    ambiguity="stop_first",
):
    if len(closes) < 60:
        return {"error": "Need at least 60 closing prices."}
    error = _validate(starting_balance, risk_percent, fee_bps, spread_bps, slippage_bps,
                      stop_loss_percent, take_profit_percent)
    if error:
        return {"error": error}
    ohlc = highs is not None or lows is not None
    if ohlc and (highs is None or lows is None or len(highs) != len(closes) or len(lows) != len(closes)):
        return {"error": "highs and lows must both be supplied and match closes length."}
    if ambiguity not in {"stop_first", "target_first"}:
        return {"error": "ambiguity must be 'stop_first' or 'target_first'."}

    balance = float(starting_balance)
    equity_peak = balance
    max_drawdown = 0.0
    wins = losses = 0
    fees_paid = 0.0
    trades = []
    equity_curve = [{"index": 0, "balance": round(balance, 2)}]

    for i in range(50, len(closes) - 1):
        action = explain(closes[:i + 1])["action"]
        if action == "WAIT":
            continue

        entry = float(closes[i])
        next_price = float(closes[i + 1])
        direction = 1 if action == "WATCH_LONG" else -1
        risk_amount = balance * risk_percent / 100
        stop_distance = entry * stop_loss_percent / 100
        qty = risk_amount / stop_distance

        stop = entry - direction * stop_distance
        target = entry + direction * (entry * take_profit_percent / 100)

        exit_price = next_price
        exit_reason = "NEXT_CLOSE"
        ambiguous_bar = False

        if ohlc:
            high = float(highs[i + 1])
            low = float(lows[i + 1])
            if direction == 1:
                hit_stop, hit_target = low <= stop, high >= target
            else:
                hit_stop, hit_target = high >= stop, low <= target
            ambiguous_bar = hit_stop and hit_target
            if ambiguous_bar:
                exit_price = stop if ambiguity == "stop_first" else target
                exit_reason = "AMBIGUOUS_STOP_FIRST" if ambiguity == "stop_first" else "AMBIGUOUS_TARGET_FIRST"
            elif hit_stop:
                exit_price, exit_reason = stop, "STOP_LOSS"
            elif hit_target:
                exit_price, exit_reason = target, "TAKE_PROFIT"
        else:
            if direction == 1 and next_price <= stop:
                exit_price, exit_reason = stop, "STOP_LOSS"
            elif direction == 1 and next_price >= target:
                exit_price, exit_reason = target, "TAKE_PROFIT"
            elif direction == -1 and next_price >= stop:
                exit_price, exit_reason = stop, "STOP_LOSS"
            elif direction == -1 and next_price <= target:
                exit_price, exit_reason = target, "TAKE_PROFIT"

        spread_cost = entry * spread_bps / 10000
        slip_cost = entry * slippage_bps / 10000
        effective_entry = entry + direction * (spread_cost / 2 + slip_cost)
        effective_exit = exit_price - direction * (spread_cost / 2 + slip_cost)
        gross_pnl = (effective_exit - effective_entry) * qty * direction
        turnover = abs(effective_entry * qty) + abs(effective_exit * qty)
        fees = turnover * fee_bps / 10000
        pnl = gross_pnl - fees
        fees_paid += fees
        balance += pnl

        wins += int(pnl > 0)
        losses += int(pnl < 0)
        equity_peak = max(equity_peak, balance)
        max_drawdown = max(max_drawdown, (equity_peak - balance) / equity_peak * 100)

        trades.append({
            "index": i, "action": action, "entry": round(entry, 8),
            "exit": round(exit_price, 8), "stop_loss": round(stop, 8),
            "take_profit": round(target, 8), "exit_reason": exit_reason,
            "ambiguous_bar": ambiguous_bar, "quantity": round(qty, 8),
            "gross_pnl": round(gross_pnl, 4), "fees": round(fees, 4),
            "pnl": round(pnl, 4),
        })
        equity_curve.append({"index": i, "balance": round(balance, 2)})
        if balance <= 0:
            break

    total = len(trades)
    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    return {
        "starting_balance": starting_balance,
        "ending_balance": round(balance, 2),
        "net_pnl": round(balance - starting_balance, 2),
        "return_percent": round((balance - starting_balance) / starting_balance * 100, 2),
        "trades": total, "wins": wins, "losses": losses,
        "win_rate_percent": round(wins / total * 100, 2) if total else 0,
        "max_drawdown_percent": round(max_drawdown, 2),
        "profit_factor": round(gross_profit / gross_loss, 3) if gross_loss else None,
        "fees_paid": round(fees_paid, 4),
        "cost_model": {"fee_bps": fee_bps, "spread_bps": spread_bps,
                       "slippage_bps": slippage_bps, "stop_loss_percent": stop_loss_percent,
                       "take_profit_percent": take_profit_percent},
        "ohlc_mode": ohlc,
        "ambiguous_bar_policy": ambiguity,
        "equity_curve": equity_curve,
        "trade_log": trades[-100:],
        "note": "Educational simulation only. OHLC mode uses the next candle's high/low and applies the selected deterministic ambiguity policy; it is not a forecast.",
    }
