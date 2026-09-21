def ema(values, period):
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    value = sum(values[:period]) / period
    for price in values[period:]:
        value = price * k + value * (1 - k)
    return round(value, 8)

def rsi(values, period=14):
    if len(values) <= period:
        return None
    gains, losses = [], []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    return round(100 - 100 / (1 + avg_gain / avg_loss), 4)

def macd(values, fast_period=12, slow_period=26, signal_period=9):
    if len(values) < slow_period + signal_period:
        return None
    fast = []
    kf = 2 / (fast_period + 1)
    v = sum(values[:fast_period]) / fast_period
    for p in values[fast_period:]:
        v = p * kf + v * (1-kf)
        fast.append(v)
    slow = []
    ks = 2 / (slow_period + 1)
    v = sum(values[:slow_period]) / slow_period
    for p in values[slow_period:]:
        v = p * ks + v * (1-ks)
        slow.append(v)
    offset = len(fast) - len(slow)
    line = [fast[i + offset] - slow[i] for i in range(len(slow))]
    sig = ema(line, signal_period)
    return {"line": round(line[-1], 8), "signal": sig, "histogram": round(line[-1] - sig, 8)} if sig is not None else None

def atr(highs, lows, closes, period=14):
    if not (len(highs) == len(lows) == len(closes)) or len(closes) <= period:
        return None
    tr = [max(highs[0]-lows[0], abs(highs[0]-closes[0]), abs(lows[0]-closes[0]))]
    for i in range(1, len(closes)):
        tr.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    return round(sum(tr[-period:]) / period, 8)
