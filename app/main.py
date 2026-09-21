from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .indicators import ema, rsi, macd, atr
from .signals import generate_signal
from .risk import position_size
from .strategy import explain
from .market import get_market
from .paper import open_trade, close_trade, list_trades
from .journal import summary, export_rows
from .backtest import run_backtest

app = FastAPI(title="CREDO-TRADAI API", version="0.3.0")

class AnalysisRequest(BaseModel):
    closes: list[float] = Field(min_length=30)
    highs: list[float] | None = None
    lows: list[float] | None = None

class RiskRequest(BaseModel):
    balance: float = Field(gt=0)
    risk_percent: float = Field(gt=0, le=10)
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

class BacktestRequest(BaseModel):
    closes: list[float] = Field(min_length=60)
    starting_balance: float = Field(gt=0, default=10000)
    risk_percent: float = Field(gt=0, le=2, default=1)

@app.get("/")
def dashboard():
    return FileResponse(Path(__file__).parent.parent / "static" / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "project": "CREDO-TRADAI", "mode": "paper-trading"}

@app.get("/market/{symbol}")
def market(symbol: str, interval: str = "1h", range_: str = "5d"):
    try:
        return get_market(symbol, interval, range_)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {exc}")

@app.post("/analyze")
def analyze(req: AnalysisRequest):
    closes = req.closes
    return {
        "ema20": ema(closes, 20), "ema50": ema(closes, 50),
        "rsi14": rsi(closes, 14), "macd": macd(closes),
        "atr14": atr(req.highs, req.lows, closes, 14) if req.highs and req.lows else None,
        "signal": generate_signal(closes),
    }

@app.post("/ai-explain")
def ai_explain(req: AnalysisRequest):
    return explain(req.closes)

@app.post("/risk/position-size")
def risk(req: RiskRequest):
    return position_size(req.balance, req.risk_percent, req.entry, req.stop_loss)

@app.post("/paper/open")
def paper_open(req: PaperTradeRequest):
    side = req.side.upper()
    if side not in {"LONG", "SHORT"}:
        raise HTTPException(status_code=400, detail="Side must be LONG or SHORT")
    if req.entry == req.stop_loss:
        raise HTTPException(status_code=400, detail="Stop-loss must differ from entry")
    return open_trade(req.symbol, side, req.entry, req.stop_loss, req.take_profit, req.quantity)

@app.get("/paper/trades")
def paper_trades():
    return {"trades": list_trades()}

@app.post("/paper/close")
def paper_close(req: CloseTradeRequest):
    trade = close_trade(req.trade_id, req.exit_price)
    if not trade:
        raise HTTPException(status_code=404, detail="Open trade not found")
    return trade

@app.get("/journal/summary")
def journal_summary():
    return summary()

@app.get("/journal/export")
def journal_export():
    return {"trades": export_rows()}

@app.post("/backtest")
def backtest(req: BacktestRequest):
    return run_backtest(req.closes, req.starting_balance, req.risk_percent)
