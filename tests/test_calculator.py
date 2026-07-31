import pytest

from arbitrage.calculator import calculate_arbitrage


def test_clean_arbitrage_case():
    result = calculate_arbitrage(2.0, 3.0)
    assert result["is_arbitrage"] is True
    assert result["total_implied_probability"] == pytest.approx(0.8333, abs=0.001)
    assert result["arbitrage_percentage"] == pytest.approx(16.67, abs=0.01)
    assert result["roi_percentage"] == pytest.approx(20.0, abs=0.01)


def test_symmetric_arbitrage_case():
    result = calculate_arbitrage(2.5, 2.5)
    assert result["is_arbitrage"] is True
    assert result["arbitrage_percentage"] == pytest.approx(20.0, abs=0.01)
    assert result["roi_percentage"] == pytest.approx(25.0, abs=0.01)


def test_equal_odds_boundary_is_not_arbitrage():
    result = calculate_arbitrage(2.0, 2.0)
    assert result["is_arbitrage"] is False
    assert result["arbitrage_percentage"] == pytest.approx(0.0, abs=0.01)


def test_no_arbitrage_case():
    result = calculate_arbitrage(1.5, 1.5)
    assert result["is_arbitrage"] is False
    assert result["arbitrage_percentage"] < 0


def test_rejects_odds_at_or_below_one():
    with pytest.raises(ValueError):
        calculate_arbitrage(1.0, 2.0)
    with pytest.raises(ValueError):
        calculate_arbitrage(2.0, 0.5)
