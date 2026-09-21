from app.account import DemoAccount, apply_pnl

def test_demo_account_snapshot():
    account = DemoAccount()
    data = account.snapshot()
    assert data["balance"] == 10000
    assert data["equity"] == 10000
    assert data["free_margin"] == 10000
    assert data["mode"] == "demo"

def test_apply_pnl():
    account = DemoAccount()
    data = apply_pnl(account, 125)
    assert data["balance"] == 10125
    assert data["realized_pnl"] == 125
