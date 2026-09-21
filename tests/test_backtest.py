from app.backtest import run_backtest

def test_backtest_requires_data():
    result = run_backtest(list(range(20)))
    assert "error" in result

def test_backtest_runs():
    prices = [100 + i * 0.1 for i in range(100)]
    result = run_backtest(prices)
    assert "ending_balance" in result
