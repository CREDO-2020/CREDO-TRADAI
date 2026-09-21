from app.indicators import ema, rsi

def test_ema():
    assert ema(list(range(1, 21)), 5) is not None

def test_rsi():
    assert rsi(list(range(1, 31)), 14) == 100.0
