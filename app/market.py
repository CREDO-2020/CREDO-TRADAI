import requests

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

SYMBOLS = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
}

def get_market(symbol: str, interval: str = "1h", range_: str = "5d"):
    key = symbol.upper().replace("/", "")
    yahoo_symbol = SYMBOLS.get(key, symbol.upper())
    params = {"interval": interval, "range": range_}
    response = requests.get(YAHOO_URL.format(symbol=yahoo_symbol), params=params, timeout=15)
    response.raise_for_status()
    result = response.json()["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    quote = result["indicators"]["quote"][0]
    closes = quote.get("close", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    opens = quote.get("open", [])
    volumes = quote.get("volume", [])
    candles = []
    for i, ts in enumerate(timestamps):
        if i >= len(closes) or closes[i] is None:
            continue
        candles.append({
            "time": ts,
            "open": opens[i],
            "high": highs[i],
            "low": lows[i],
            "close": closes[i],
            "volume": volumes[i] if i < len(volumes) else None,
        })
    return {"symbol": key, "source_symbol": yahoo_symbol, "candles": candles}
