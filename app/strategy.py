from .indicators import ema, rsi, macd

def explain(closes):
    e20, e50, r = ema(closes, 20), ema(closes, 50), rsi(closes, 14)
    m = macd(closes)
    if None in (e20, e50, r):
        return {"action": "WAIT", "confidence": 0, "reasons": ["Need at least 50 closing prices."]}
    reasons = []
    score = 0
    if e20 > e50:
        score += 1
        reasons.append("Short-term EMA is above the longer EMA, indicating upward trend pressure.")
    else:
        score -= 1
        reasons.append("Short-term EMA is below the longer EMA, indicating downward trend pressure.")
    if r > 50:
        score += 1
        reasons.append(f"RSI is {r:.1f}, above the midpoint.")
    else:
        score -= 1
        reasons.append(f"RSI is {r:.1f}, below the midpoint.")
    if m:
        if m["histogram"] > 0:
            score += 1
            reasons.append("MACD histogram is positive.")
        else:
            score -= 1
            reasons.append("MACD histogram is negative.")
    action = "WATCH_LONG" if score >= 2 else "WATCH_SHORT" if score <= -2 else "WAIT"
    confidence = min(90, 50 + abs(score) * 12)
    reasons.append("This is an analytical signal, not a guarantee or financial advice.")
    return {"action": action, "confidence": confidence, "score": score, "reasons": reasons}
