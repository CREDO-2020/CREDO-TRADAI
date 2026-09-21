from .indicators import ema, rsi

def generate_signal(closes):
    e20, e50, r = ema(closes, 20), ema(closes, 50), rsi(closes, 14)
    if None in (e20, e50, r):
        return {"action": "WAIT", "reason": "Not enough data"}
    if e20 > e50 and 50 < r < 70:
        return {"action": "WATCH_LONG", "reason": "EMA20 above EMA50 with RSI confirmation"}
    if e20 < e50 and 30 < r < 50:
        return {"action": "WATCH_SHORT", "reason": "EMA20 below EMA50 with RSI confirmation"}
    return {"action": "WAIT", "reason": "Indicators are not aligned"}
