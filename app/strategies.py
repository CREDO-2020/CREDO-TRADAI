from .indicators import ema, rsi, macd

def trend_strategy(closes):
    e20, e50 = ema(closes, 20), ema(closes, 50)
    if e20 is None or e50 is None:
        return {"name": "Trend", "action": "WAIT", "score": 0, "reason": "Need 50 candles"}
    if e20 > e50:
        return {"name": "Trend", "action": "WATCH_LONG", "score": 1, "reason": "EMA20 is above EMA50"}
    if e20 < e50:
        return {"name": "Trend", "action": "WATCH_SHORT", "score": -1, "reason": "EMA20 is below EMA50"}
    return {"name": "Trend", "action": "WAIT", "score": 0, "reason": "EMAs are equal"}

def momentum_strategy(closes):
    r = rsi(closes, 14)
    m = macd(closes)
    if r is None or m is None:
        return {"name": "Momentum", "action": "WAIT", "score": 0, "reason": "Need more candles"}
    if r > 50 and m["histogram"] > 0:
        return {"name": "Momentum", "action": "WATCH_LONG", "score": 1, "reason": "RSI above 50 and MACD histogram positive"}
    if r < 50 and m["histogram"] < 0:
        return {"name": "Momentum", "action": "WATCH_SHORT", "score": -1, "reason": "RSI below 50 and MACD histogram negative"}
    return {"name": "Momentum", "action": "WAIT", "score": 0, "reason": "Momentum signals disagree"}

def combined_strategy(closes):
    results = [trend_strategy(closes), momentum_strategy(closes)]
    score = sum(x["score"] for x in results)
    if score >= 2:
        action = "WATCH_LONG"
    elif score <= -2:
        action = "WATCH_SHORT"
    else:
        action = "WAIT"
    return {"name": "Combined", "action": action, "score": score, "components": results}

def compare_strategies(closes):
    return [trend_strategy(closes), momentum_strategy(closes), combined_strategy(closes)]
