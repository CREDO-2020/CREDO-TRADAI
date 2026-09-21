MAX_OPEN_POSITIONS = 3
MAX_RISK_PER_TRADE_PERCENT = 2.0
MAX_DAILY_LOSS_PERCENT = 3.0

def validate_risk(balance, risk_percent):
    if balance <= 0:
        raise ValueError("Balance must be positive")
    if not 0 < risk_percent <= MAX_RISK_PER_TRADE_PERCENT:
        raise ValueError(f"Risk per trade must be between 0 and {MAX_RISK_PER_TRADE_PERCENT}%")
    return {
        "allowed": True,
        "risk_amount": round(balance * risk_percent / 100, 2),
        "max_risk_percent": MAX_RISK_PER_TRADE_PERCENT,
        "max_daily_loss_percent": MAX_DAILY_LOSS_PERCENT,
        "max_open_positions": MAX_OPEN_POSITIONS,
    }
