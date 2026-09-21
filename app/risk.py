def position_size(balance, risk_percent, entry, stop_loss):
    distance = abs(entry - stop_loss)
    risk_amount = balance * risk_percent / 100
    if distance <= 0:
        raise ValueError("Entry and stop-loss must be different")
    return {
        "risk_amount": round(risk_amount, 2),
        "price_distance": round(distance, 8),
        "units": round(risk_amount / distance, 8),
    }
