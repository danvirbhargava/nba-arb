import pytest

from arbitrage.stakes import calculate_stakes


def test_clean_stake_split():
    result = calculate_stakes(1000, 2.0, 3.0)
    assert result["stake_a"] == pytest.approx(600.0, abs=0.01)
    assert result["stake_b"] == pytest.approx(400.0, abs=0.01)
    assert result["guaranteed_return"] == pytest.approx(1200.0, abs=0.01)
    assert result["profit"] == pytest.approx(200.0, abs=0.01)


def test_stakes_are_rounded_to_nearest_ten():
    result = calculate_stakes(750, 2.15, 4.20)
    assert result["stake_a"] % 10 == 0
    assert result["stake_b"] % 10 == 0


def test_stakes_sum_to_bankroll():
    # Each stake rounds to the nearest $10 independently, so the sum can be
    # off by up to $10 from the bankroll.
    result = calculate_stakes(750, 2.15, 4.20)
    assert result["stake_a"] + result["stake_b"] == pytest.approx(750, abs=10)


def test_payout_close_on_both_outcomes():
    # $10 rounding trades exact payout parity for clean bet-slip amounts;
    # returns should still be close, not necessarily equal to the cent.
    result = calculate_stakes(1000, 2.15, 4.20)
    return_a = result["stake_a"] * 2.15
    return_b = result["stake_b"] * 4.20
    assert return_a == pytest.approx(return_b, rel=0.02)


def test_rejects_non_positive_bankroll():
    with pytest.raises(ValueError):
        calculate_stakes(0, 2.0, 3.0)
    with pytest.raises(ValueError):
        calculate_stakes(-100, 2.0, 3.0)


def test_rejects_odds_at_or_below_one():
    with pytest.raises(ValueError):
        calculate_stakes(1000, 1.0, 2.0)
