from dataclasses import dataclass

@dataclass
class DemoAccount:
    balance: float = 10000.0
    equity: float = 10000.0
    margin_used: float = 0.0
    realized_pnl: float = 0.0

    def snapshot(self):
        return {
            "balance": round(self.balance, 2),
            "equity": round(self.equity, 2),
            "margin_used": round(self.margin_used, 2),
            "free_margin": round(self.equity - self.margin_used, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "mode": "demo",
        }

def apply_pnl(account: DemoAccount, pnl: float):
    account.balance += pnl
    account.equity = account.balance
    account.realized_pnl += pnl
    if account.balance < 0:
        raise ValueError("Account balance cannot become negative")
    return account.snapshot()
