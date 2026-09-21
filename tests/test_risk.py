from app.risk import position_size

def test_position_size():
    result = position_size(1000, 1, 100, 95)
    assert result["risk_amount"] == 10
    assert result["units"] == 2
