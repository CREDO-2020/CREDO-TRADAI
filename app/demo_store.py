import json
from pathlib import Path
from .account import DemoAccount

STORE = Path(__file__).parent.parent / "demo_account.json"

def load_account():
    if not STORE.exists():
        return DemoAccount()
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
        return DemoAccount(
            starting_balance=float(data.get("starting_balance", 10000)),
            balance=float(data.get("balance", 10000)),
            realized_pnl=float(data.get("realized_pnl", 0)),
        )
    except (ValueError, TypeError, json.JSONDecodeError):
        return DemoAccount()

def save_account(account):
    STORE.write_text(json.dumps({
        "starting_balance": account.starting_balance,
        "balance": account.balance,
        "realized_pnl": account.realized_pnl,
    }, indent=2), encoding="utf-8")
    return account
