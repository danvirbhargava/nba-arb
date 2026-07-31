def calculate_stakes(bankroll: float, odds_a: float, odds_b: float) -> dict:
    if bankroll <= 0:
        raise ValueError("Bankroll must be positive")
    if odds_a <= 1 or odds_b <= 1:
        raise ValueError("Odds must be greater than 1.0")

    implied_a = 1 / odds_a
    implied_b = 1 / odds_b
    total_implied = implied_a + implied_b

    stake_a = round(bankroll * implied_a / total_implied, 2)
    stake_b = round(bankroll * implied_b / total_implied, 2)
    guaranteed_return = round(min(stake_a * odds_a, stake_b * odds_b), 2)
    profit = round(guaranteed_return - bankroll, 2)

    return {
        "stake_a": stake_a,
        "stake_b": stake_b,
        "guaranteed_return": guaranteed_return,
        "profit": profit,
    }
