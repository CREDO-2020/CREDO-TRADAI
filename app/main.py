from fastapi import FastAPI
from pydantic import BaseModel, Field
from .indicators import ema, rsi, macd, atr
from .signals import generate_signal
from .risk import position_size

app = FastAPI(title="CREDO-TRADAI API", version="0.1.0")

class AnalysisRequest(BaseModel):
    closes: list[float] = Field(min_length=30)
    highs: list[float] | None = None
    lows: list[float] | None = None

class RiskRequest(BaseModel):
    balance: float = Field(gt=0)
    risk_percent: float = Field(gt=0, le=10)
    entry: float
    stop_loss: float

@app.get("/health")
def health():
    return {"status": "ok", "project": "CREDO-TRADAI"}

@app.post("/analyze")
def analyze(req: AnalysisRequest):
    closes = req.closes
    return {
        "ema20": ema(closes, 20),
        "ema50": ema(closes, 50),
        "rsi14": rsi(closes, 14),
        "macd": macd(closes),
        "atr14": atr(req.highs, req.lows, closes, 14) if req.highs and req.lows else None,
        "signal": generate_signal(closes),
    }

@app.post("/risk/position-size")
def risk(req: RiskRequest):
    return position_size(req.balance, req.risk_percent, req.entry, req.stop_loss)
