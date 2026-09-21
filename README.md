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


## Authentication
The dashboard uses Supabase email/password authentication. The browser uses only the Supabase publishable key. The FastAPI server verifies the user's Supabase access token before accessing cloud demo accounts and paper trades.

For local development, create a file named .env from .env.example and set:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- TRADING_MODE=demo
- ENABLE_LIVE_TRADING=false

Never commit the service-role key. It must stay server-side.

Open /login to create an account or sign in, then the dashboard loads the authenticated user's cloud demo account and paper trades.

## Safety
CREDO-TRADAI is research/paper-trading software. Live broker execution is not configured. No profitability or trading outcome is guaranteed.
