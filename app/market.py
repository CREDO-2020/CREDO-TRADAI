import requests

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
BINANCE_URL = "https://api.binance.com/api/v3/klines"
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"

SYMBOLS = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
}

BINANCE_SYMBOLS = {"BTCUSDT", "ETHUSDT"}

INTERVALS = {
    "1h": "1h",
    "15m": "15m",
    "4h": "4h",
    "1d": "1d",
}

def _clean_candles(rows):
    candles = []
    for row in rows:
        if len(row) < 6:
            continue
        try:
            candles.append({
                "time": int(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]) if row[5] is not None else None,
            })
        except (TypeError, ValueError):
            continue
    return candles

def _binance_market(key, interval, range_):
    if key not in BINANCE_SYMBOLS:
        return None
    # Binance does not use Yahoo-style range strings. 600 candles gives
    # the analysis/backtest enough history while keeping requests small.
    limit = 500 if range_ in {"5d", "1mo"} else 1000
    response = requests.get(
        BINANCE_URL,
        params={"symbol": key, "interval": INTERVALS.get(interval, interval), "limit": limit},
        timeout=15,
        headers={"User-Agent": "CREDO-TRADAI/1.0"},
    )
    response.raise_for_status()
    candles = _clean_candles(response.json())
    if not candles:
        raise RuntimeError("Binance returned no candle data")
    ticker = requests.get(
        BINANCE_TICKER_URL,
        params={"symbol": key},
        timeout=10,
        headers={"User-Agent": "CREDO-TRADAI/1.0"},
    )
    ticker.raise_for_status()
    ticker_price = float(ticker.json()["price"])
    return {"symbol": key, "source_symbol": key, "source": "binance", "price": ticker_price, "price_source": "binance_spot_ticker", "candles": candles}

def _yahoo_market(key, interval, range_):
    yahoo_symbol = SYMBOLS.get(key, key)
    response = requests.get(
        YAHOO_URL.format(symbol=yahoo_symbol),
        params={"interval": interval, "range": range_},
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 CREDO-TRADAI/1.0"},
    )
    response.raise_for_status()
    payload = response.json()
    result = (payload.get("chart") or {}).get("result")
    if not result:
        error = (payload.get("chart") or {}).get("error")
        message = error.get("description") if isinstance(error, dict) else "Yahoo returned no data"
        raise RuntimeError(message)
    result = result[0]
    timestamps = result.get("timestamp", [])
    quote = result["indicators"]["quote"][0]
    rows = zip(
        timestamps,
        quote.get("open", []),
        quote.get("high", []),
        quote.get("low", []),
        quote.get("close", []),
        quote.get("volume", []),
    )
    candles = []
    for ts, op, hi, lo, close, volume in rows:
        if close is None:
            continue
        try:
            candles.append({
                "time": int(ts),
                "open": float(op),
                "high": float(hi),
                "low": float(lo),
                "close": float(close),
                "volume": float(volume) if volume is not None else None,
            })
        except (TypeError, ValueError):
            continue
    if not candles:
        raise RuntimeError("Yahoo returned no usable candle data")
    meta = result.get("meta") or {}
    current_price = meta.get("regularMarketPrice") or candles[-1]["close"]
    return {"symbol": key, "source_symbol": yahoo_symbol, "source": "yahoo", "price": float(current_price), "price_source": "yahoo_market_price", "candles": candles}

def get_market(symbol: str, interval: str = "1h", range_: str = "5d"):
    key = symbol.upper().replace("/", "")
    interval = INTERVALS.get(interval, interval)

    # Use Binance for crypto because it is a direct crypto market-data source.
    if key in BINANCE_SYMBOLS:
        return _binance_market(key, interval, range_)

    return _yahoo_market(key, interval, range_)
