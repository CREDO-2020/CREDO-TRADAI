from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .indicators import ema, rsi, macd, atr
from .signals import generate_signal
from .risk import position_size
from .strategy import explain
from .strategies import compare_strategies
from .regime import detect_regime
from .market import get_market
from .paper import init_db, open_trade, close_trade, list_trades, monitor_trade, unrealized_pnl
from .journal import summary, export_rows
from .backtest import run_backtest
from .execution import get_mode, execute_order
from .mt5_broker import status as mt5_status, quote as mt5_quote
from .account import DemoAccount, apply_pnl
from .demo_store import load_account, save_account
from .trading_engine import evaluate
from .supabase_store import (
    enabled as supabase_enabled,
    get_user_from_access_token,
    get_demo_account,
    create_demo_account,
    upsert_demo_account,
    list_paper_trades,
    create_paper_trade,
    close_paper_trade,
)

init_db()
demo_account = load_account()
app = FastAPI(title="CREDO-TRADAI API", version="1.8.0")

class AnalysisRequest(BaseModel):
    closes: list[float] = Field(min_length=30)
    highs: list[float] | None = None
    lows: list[float] | None = None

class RiskRequest(BaseModel):
    balance: float = Field(gt=0)
    risk_percent: float = Field(gt=0, le=2)
    entry: float
    stop_loss: float

class PaperTradeRequest(BaseModel):
    symbol: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    quantity: float = Field(gt=0)

class CloseTradeRequest(BaseModel):
    trade_id: str
    exit_price: float

class MonitorRequest(BaseModel):
    symbol: str
    current_price: float = Field(gt=0)

class BacktestRequest(BaseModel):
    closes: list[float] = Field(min_length=60)
    starting_balance: float = Field(gt=0, default=10000)
    risk_percent: float = Field(gt=0, le=2)
    fee_bps: float = Field(ge=0, default=5)
    spread_bps: float = Field(ge=0, default=2)
    slippage_bps: float = Field(ge=0, default=1)
    stop_loss_percent: float = Field(gt=0, default=0.5)
    take_profit_percent: float = Field(gt=0, default=1)
    highs: list[float] | None = None
    lows: list[float] | None = None
    ambiguity: str = "stop_first"

class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float = Field(gt=0)
    order_type: str = "MARKET"
    price: float | None = None

class PnlRequest(BaseModel):
    pnl: float

class EngineRequest(BaseModel):
    closes: list[float] = Field(min_length=50)
    balance: float = Field(gt=0)
    risk_percent: float = Field(gt=0, le=2, default=1)

def _current_user(authorization: str | None):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required. Please sign in.")
    token = authorization.split(" ", 1)[1].strip()
    user = get_user_from_access_token(token)
    if not user:
        raise HTTPException(401, "Invalid or expired Supabase session.")
    if not supabase_enabled():
        raise HTTPException(503, "Supabase persistence is not configured.")
    return user

@app.get("/")
def dashboard():
    return FileResponse(Path(__file__).parent.parent / "static" / "index.html")

@app.get("/login")
def login_page():
    return FileResponse(Path(__file__).parent.parent / "static" / "auth.html")

@app.get("/auth.js")
def auth_script():
    return FileResponse(Path(__file__).parent.parent / "static" / "auth.js", media_type="application/javascript")

@app.get("/auth/me")
def auth_me(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    return {"id": str(user.id), "email": user.email}

@app.get("/health")
def health():
    return {"status":"ok","project":"CREDO-TRADAI","mode":get_mode(),"database":"sqlite","version":"1.7.0","supabase_persistence":supabase_enabled(),"live_orders_configured":False}

@app.get("/execution/mode")
def execution_mode():
    return {"mode":get_mode(),"live_enabled":get_mode()=="live","mt5_demo_enabled":get_mode()=="mt5_demo","real_orders_configured":False}

def _floating_pnl():
    prices = {}
    for symbol in {"BTCUSDT","ETHUSDT","EURUSD","GBPUSD","USDJPY"}:
        try:
            candles = get_market(symbol, "1h", "1d")["candles"]
            if candles:
                prices[symbol] = candles[-1]["close"]
        except Exception:
            pass
    return sum(unrealized_pnl(t, prices[t["symbol"]]) for t in list_trades()
               if t["status"] == "OPEN" and t["symbol"] in prices)

def _save():
    save_account(demo_account)

@app.get("/demo/account")
def demo_account_status():
    return demo_account.snapshot(_floating_pnl())

@app.get("/cloud/demo/account")
def cloud_demo_account(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    account = get_demo_account(str(user.id))
    if not account:
        account = create_demo_account(str(user.id))
    return account

@app.post("/cloud/demo/account/reset")
def cloud_demo_account_reset(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    return upsert_demo_account(str(user.id), 10000, 10000, 0)

@app.get("/cloud/paper/trades")
def cloud_paper_trades(authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    return {"trades": list_paper_trades(str(user.id))}

@app.post("/cloud/paper/open")
def cloud_paper_open(req: PaperTradeRequest, authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    side = req.side.upper()
    if side not in {"LONG", "SHORT"}:
        raise HTTPException(400, "Side must be LONG or SHORT")
    if side == "LONG" and not (req.stop_loss < req.entry < req.take_profit):
        raise HTTPException(400, "LONG requires stop-loss < entry < take-profit")
    if side == "SHORT" and not (req.take_profit < req.entry < req.stop_loss):
        raise HTTPException(400, "SHORT requires take-profit < entry < stop-loss")
    trade = {"symbol": req.symbol.upper(), "side": side, "entry": req.entry,
             "stop_loss": req.stop_loss, "take_profit": req.take_profit,
             "quantity": req.quantity, "status": "OPEN"}
    result = create_paper_trade(str(user.id), trade)
    if result is None:
        raise HTTPException(503, "Supabase persistence is unavailable.")
    return result

@app.post("/cloud/paper/close")
def cloud_paper_close(req: CloseTradeRequest, authorization: str | None = Header(default=None)):
    user = _current_user(authorization)
    user_id = str(user.id)
    trades = list_paper_trades(user_id)
    trade = next((t for t in trades if str(t["id"]) == req.trade_id and t["status"] == "OPEN"), None)
    if not trade:
        raise HTTPException(404, "Open cloud trade not found")
    direction = 1 if trade["side"] == "LONG" else -1
    pnl = round((req.exit_price - float(trade["entry"])) * float(trade["quantity"]) * direction, 8)
    result = close_paper_trade(user_id, req.trade_id, req.exit_price, pnl)
    if not result:
        raise HTTPException(409, "Trade could not be closed")
    return {**result, "close_reason": "MANUAL"}

@app.post("/demo/account/reset")
def demo_account_reset():
    global demo_account
    demo_account = DemoAccount()
    _save()
    return demo_account.snapshot()

@app.post("/demo/account/pnl")
def demo_account_pnl(req: PnlRequest):
    try:
        result = apply_pnl(demo_account, req.pnl, _floating_pnl())
        _save()
        return result
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.post("/engine/evaluate")
def engine_evaluate(req: EngineRequest):
    try:
        return evaluate(req.closes, req.balance, req.risk_percent)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.post("/execution/order")
def execution_order(req: OrderRequest):
    try:
        return execute_order(req.symbol, req.side, req.quantity, req.order_type, req.price)
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except NotImplementedError as exc:
        raise HTTPException(501, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@app.get("/broker/mt5/status")
def broker_mt5_status():
    try:
        return mt5_status()
    except Exception as exc:
        raise HTTPException(502, f"MetaTrader 5 unavailable: {exc}")


@app.get("/broker/mt5/quote/{symbol}")
def broker_mt5_quote(symbol: str):
    try:
        return mt5_quote(symbol)
    except Exception as exc:
        raise HTTPException(502, f"MetaTrader 5 quote unavailable: {exc}")


@app.get("/market/{symbol}")
def market(symbol: str, interval: str = "1h", range_: str = "5d"):
    try:
        return get_market(symbol, interval, range_)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {exc}")

@app.post("/analyze")
def analyze(req: AnalysisRequest):
    closes = req.closes
    return {"ema20":ema(closes,20),"ema50":ema(closes,50),"rsi14":rsi(closes,14),
            "macd":macd(closes),"atr14":atr(req.highs,req.lows,closes,14) if req.highs and req.lows else None,
            "signal":generate_signal(closes)}

@app.post("/ai-explain")
def ai_explain(req: AnalysisRequest):
    return explain(req.closes)

@app.post("/strategies/compare")
def strategies(req: AnalysisRequest):
    return {"strategies": compare_strategies(req.closes)}

@app.post("/regime")
def regime(req: AnalysisRequest):
    return detect_regime(req.closes, req.highs, req.lows)

@app.post("/risk/position-size")
def risk(req: RiskRequest):
    return position_size(req.balance,req.risk_percent,req.entry,req.stop_loss)

@app.post("/paper/open")
def paper_open(req: PaperTradeRequest):
    side=req.side.upper()
    if side not in {"LONG","SHORT"}:
        raise HTTPException(400,"Side must be LONG or SHORT")
    try:
        return open_trade(req.symbol,side,req.entry,req.stop_loss,req.take_profit,req.quantity)
    except ValueError as exc:
        raise HTTPException(400,str(exc))

@app.get("/paper/trades")
def paper_trades():
    return {"trades":list_trades()}

@app.get("/paper/positions")
def paper_positions():
    return {"positions":list_trades()}

@app.get("/paper/position/{trade_id}")
def paper_position(trade_id: str):
    trade = next((t for t in list_trades() if t["id"] == trade_id), None)
    if not trade: raise HTTPException(404, "Trade not found")
    return trade

@app.post("/paper/close")
def paper_close(req: CloseTradeRequest):
    trade=close_trade(req.trade_id,req.exit_price)
    if not trade: raise HTTPException(404,"Open trade not found")
    try:
        result = apply_pnl(demo_account, trade["pnl"], _floating_pnl())
        _save()
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    trade["account"] = result
    return trade

@app.post("/paper/monitor")
def paper_monitor(req: MonitorRequest):
    checked=[]
    for trade in list_trades():
        if trade["status"]=="OPEN" and trade["symbol"]==req.symbol.upper():
            result = monitor_trade(trade,req.current_price)
            if result:
                try:
                    account = apply_pnl(demo_account, result["pnl"], _floating_pnl())
                    _save()
                    result["account"] = account
                except ValueError as exc:
                    raise HTTPException(400, str(exc))
                checked.append(result)
            else:
                trade["unrealized_pnl"] = unrealized_pnl(trade, req.current_price)
                checked.append(trade)
    return {"symbol":req.symbol.upper(),"current_price":req.current_price,"checked":checked}

@app.get("/journal/summary")
def journal_summary():
    data = summary()
    data["unrealized_pnl"] = _floating_pnl()
    return data

@app.get("/journal/export")
def journal_export():
    return {"trades":export_rows()}

@app.post("/backtest")
def backtest(req: BacktestRequest):
    return run_backtest(req.closes, req.starting_balance, req.risk_percent,
        req.fee_bps, req.spread_bps, req.slippage_bps,
        req.stop_loss_percent, req.take_profit_percent,
        req.highs, req.lows, req.ambiguity)
