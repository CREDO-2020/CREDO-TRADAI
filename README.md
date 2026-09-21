# CREDO-TRADAI

AI-assisted Forex & Crypto trading research platform.

## Phase 1
- Market data adapter interfaces
- Technical indicators: EMA, RSI, MACD, ATR
- Signal engine with transparent rules
- Risk calculator
- Paper-trading engine
- Backtesting foundation
- FastAPI backend

> This project is for research and paper trading first. It does not guarantee profits and does not place real-money trades by default.

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
