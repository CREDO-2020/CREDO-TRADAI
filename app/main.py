from pathlib import Path
from fastapi import FastAPI, HTTPException
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
from .account import DemoAccount, apply_pnl
from .trading_engine import evaluate

init_db()
demo_account = DemoAccount()
app = FastAPI(title="CREDO-TRADAI API", version="1.2.0")

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

@app.get("/")
def dashboard():
    return FileResponse(Path(__file__).parent.parent / "static" / "index.html")

@app.get("/health")
def health():
    return {"status":"ok","project":"CREDO-TRADAI","mode":get_mode(),"database":"sqlite","version":"1.2.0"}

@app.get("/execution/mode")
def execution_mode():
    return {"mode":get_mode(),"live_enabled":get_mode()=="live","real_orders_configured":False}

@app.get("/demo/account")
def demo_account_status():
    return demo_account.snapshot()

@app.post("/demo/account/reset")
def demo_account_reset():
    global demo_account
    demo_account = DemoAccount()
    return demo_account.snapshot()

@app.post("/demo/account/pnl")
def demo_account_pnl(req: PnlRequest):
    try:
        return apply_pnl(demo_account, req.pnl)
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

@app.get("/market/{symbol}")
def market(symbol: str, interval: str = "1h", range_: str = "5d"):
    try:
        return get_market(symbol, interval, range_)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {exc}")

@app.post("/analyze")
def analyze(req: AnalysisRequest):
    closes=req.closes
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
    if side not in {"LONG","SHORT"}: raise HTTPException(400,"Side must be LONG or SHORT")
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
    if not trade:
        raise HTTPException(404, "Trade not found")
    return trade

@app.post("/paper/close")
def paper_close(req: CloseTradeRequest):
    trade=close_trade(req.trade_id,req.exit_price)
    if not trade: raise HTTPException(404,"Open trade not found")
    return trade

@app.post("/paper/monitor")
def paper_monitor(req: MonitorRequest):
    checked=[]
    for trade in list_trades():
        if trade["status"]=="OPEN" and trade["symbol"]==req.symbol.upper():
            checked.append(monitor_trade(trade,req.current_price) or trade)
    return {"symbol":req.symbol.upper(),"current_price":req.current_price,"checked":checked}

@app.get("/journal/summary")
def journal_summary():
    return summary()

@app.get("/journal/export")
def journal_export():
    return {"trades":export_rows()}

@app.post("/backtest")
def backtest(req: BacktestRequest):
    return run_backtest(req.closes,req.starting_balance,req.risk_percent)
