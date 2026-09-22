import os
from typing import Any

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


def _settings():
    return {
        "path": os.getenv("MT5_PATH", "").strip() or None,
        "login": int(os.getenv("MT5_LOGIN", "0") or 0) or None,
        "password": os.getenv("MT5_PASSWORD", "") or None,
        "server": os.getenv("MT5_SERVER", "") or None,
    }


def _connect():
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is not installed. Run: pip install MetaTrader5")

    cfg = _settings()
    kwargs = {}
    if cfg["login"]:
        kwargs["login"] = cfg["login"]
    if cfg["password"]:
        kwargs["password"] = cfg["password"]
    if cfg["server"]:
        kwargs["server"] = cfg["server"]

    ok = mt5.initialize(cfg["path"], **kwargs) if cfg["path"] else mt5.initialize(**kwargs)
    if not ok:
        code = mt5.last_error()
        raise RuntimeError(f"MetaTrader 5 initialize failed: {code}")
    return cfg


def _result_dict(result: Any):
    if result is None:
        return None
    try:
        return result._asdict()
    except AttributeError:
        return str(result)


def status():
    _connect()
    try:
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        if account is None:
            raise RuntimeError(f"MT5 account_info failed: {mt5.last_error()}")
        return {
            "connected": True,
            "login": account.login,
            "server": account.server,
            "currency": account.currency,
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "terminal": str(terminal.name) if terminal else None,
            "trade_allowed": bool(getattr(terminal, "trade_allowed", False)) if terminal else False,
        }
    finally:
        mt5.shutdown()


def quote(symbol: str):
    _connect()
    try:
        symbol = symbol.upper()
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"Broker symbol not found: {symbol}")
        if not info.visible and not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"Could not enable broker symbol: {symbol}")
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"No tick available for {symbol}")
        return {
            "symbol": symbol,
            "bid": float(tick.bid),
            "ask": float(tick.ask),
            "time": int(tick.time),
            "point": float(info.point),
            "digits": int(info.digits),
        }
    finally:
        mt5.shutdown()


def market_order(symbol: str, side: str, volume: float, sl: float | None = None, tp: float | None = None):
    _connect()
    try:
        symbol = symbol.upper()
        side = side.upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("Side must be BUY or SELL")
        if volume <= 0:
            raise ValueError("Volume must be positive")

        info = mt5.symbol_info(symbol)
        if info is None:
            raise ValueError(f"Broker symbol not found: {symbol}")
        if not info.visible and not mt5.symbol_select(symbol, True):
            raise ValueError(f"Could not enable broker symbol: {symbol}")

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"No tick available for {symbol}")

        order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if side == "BUY" else tick.bid
        filling = getattr(info, "filling_mode", mt5.ORDER_FILLING_RETURN)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl or 0.0,
            "tp": tp or 0.0,
            "deviation": 20,
            "magic": 20260922,
            "comment": "CREDO-TRADAI demo",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }

        check = mt5.order_check(request)
        if check is None:
            raise RuntimeError(f"MT5 order_check failed: {mt5.last_error()}")

        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"MT5 order_send failed: {mt5.last_error()}")

        payload = _result_dict(result)
        retcode = int(getattr(result, "retcode", 0))
        return {
            "status": "EXECUTED" if retcode == mt5.TRADE_RETCODE_DONE else "REJECTED",
            "broker": "MetaTrader 5",
            "symbol": symbol,
            "side": side,
            "volume": volume,
            "retcode": retcode,
            "result": payload,
        }
    finally:
        mt5.shutdown()
