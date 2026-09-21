from dataclasses import dataclass

@dataclass
class DemoAccount:
    starting_balance: float = 10000.0
    balance: float = 10000.0
    realized_pnl: float = 0.0

    def snapshot(self, floating_pnl=0.0, margin_used=0.0):
        equity = self.balance + floating_pnl
        return {
            "starting_balance": round(self.starting_balance, 2),
            "balance": round(self.balance, 2),
            "equity": round(equity, 2),
            "margin_used": round(margin_used, 2),
            "free_margin": round(equity - margin_used, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "floating_pnl": round(floating_pnl, 2),
            "return_percent": round((self.balance - self.starting_balance) / self.starting_balance * 100, 2),
            "mode": "demo",
        }

def apply_pnl(account: DemoAccount, pnl: float, floating_pnl=0.0, margin_used=0.0):
    account.balance += pnl
    account.realized_pnl += pnl
    if account.balance < 0:
        raise ValueError("Account balance cannot become negative")
    return account.snapshot(floating_pnl, margin_used)
