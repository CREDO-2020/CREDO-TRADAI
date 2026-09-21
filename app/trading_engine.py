from .strategy import explain
from .risk import position_size
from .risk_limits import validate_risk

def evaluate(closes, balance, risk_percent=1.0):
    if balance <= 0:
        raise ValueError("Balance must be positive")
    limits = validate_risk(balance, risk_percent)
    analysis = explain(closes)
    action = analysis["action"]
    if action == "WAIT":
        return {"status":"NO_TRADE","analysis":analysis,"risk":limits}

    entry = closes[-1]
    stop_distance = entry * 0.005
    stop_loss = entry - stop_distance if action == "WATCH_LONG" else entry + stop_distance
    take_profit = entry + stop_distance * 2 if action == "WATCH_LONG" else entry - stop_distance * 2
    sizing = position_size(balance, risk_percent, entry, stop_loss)

    return {
        "status": "TRADE_CANDIDATE",
        "action": action,
        "entry": round(entry, 8),
        "stop_loss": round(stop_loss, 8),
        "take_profit": round(take_profit, 8),
        "quantity": sizing["units"],
        "risk": limits,
        "analysis": analysis,
        "note": "Analytical trade candidate. Execution requires a separate explicit order step."
    }
