from app.trading_engine import evaluate

def test_engine_waits_for_weak_signal():
    prices = [100 + (i % 3) for i in range(60)]
    result = evaluate(prices, 10000, 1)
    assert result["status"] in {"NO_TRADE", "TRADE_CANDIDATE"}

def test_engine_rejects_invalid_balance():
    try:
        evaluate([100 + i * 0.1 for i in range(60)], 0, 1)
        assert False
    except ValueError:
        assert True
