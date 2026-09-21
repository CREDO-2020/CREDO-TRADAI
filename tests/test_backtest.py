from app.backtest import run_backtest

def test_backtest_requires_data():
    result = run_backtest(list(range(20)))
    assert "error" in result

def test_backtest_runs():
    prices = [100 + i * 0.1 for i in range(100)]
    result = run_backtest(prices)
    assert "ending_balance" in result
    assert "fees_paid" in result

def test_backtest_costs_are_reported():
    prices = [100 + i * 0.1 for i in range(100)]
    result = run_backtest(prices, fee_bps=10, spread_bps=5, slippage_bps=2)
    assert result["fees_paid"] > 0
    assert result["cost_model"]["fee_bps"] == 10

def test_backtest_rejects_invalid_costs():
    result = run_backtest([100 + i * 0.1 for i in range(100)], fee_bps=-1)
    assert "error" in result
