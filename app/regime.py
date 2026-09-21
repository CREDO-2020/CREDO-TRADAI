from .indicators import ema, rsi, atr

def detect_regime(closes, highs=None, lows=None):
    e20, e50, r = ema(closes, 20), ema(closes, 50), rsi(closes, 14)
    if e20 is None or e50 is None or r is None:
        return {"regime":"UNKNOWN","description":"Need at least 50 closing prices."}
    spread = abs(e20 - e50) / e50 * 100 if e50 else 0
    volatility = None
    if highs and lows and len(highs) == len(lows) == len(closes):
        volatility = atr(highs, lows, closes, 14)
        if volatility is not None and closes[-1]:
            volatility = volatility / closes[-1] * 100
    if volatility is not None and volatility >= 2:
        return {"regime":"VOLATILE","description":"Recent candle range is relatively large.", "ema_spread_percent":round(spread,4),"atr_percent":round(volatility,4)}
    if spread >= 0.5 and e20 > e50 and r >= 50:
        return {"regime":"TRENDING_UP","description":"EMA separation and RSI support upward trend pressure.","ema_spread_percent":round(spread,4)}
    if spread >= 0.5 and e20 < e50 and r < 50:
        return {"regime":"TRENDING_DOWN","description":"EMA separation and RSI support downward trend pressure.","ema_spread_percent":round(spread,4)}
    return {"regime":"RANGING","description":"EMA separation is limited and indicators do not show a strong directional regime.","ema_spread_percent":round(spread,4)}
