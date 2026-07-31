def calculate_arbitrage(odds_a: float, odds_b: float) -> dict:
    if odds_a <= 1 or odds_b <= 1:
        raise ValueError("Odds must be greater than 1.0")

    implied_a = 1 / odds_a
    implied_b = 1 / odds_b
    total_implied = implied_a + implied_b

    is_arbitrage = total_implied < 1
    arbitrage_percentage = round((1 - total_implied) * 100, 2)
    roi_percentage = round(((1 / total_implied) - 1) * 100, 2)

    return {
        "is_arbitrage": is_arbitrage,
        "total_implied_probability": round(total_implied, 4),
        "arbitrage_percentage": arbitrage_percentage,
        "roi_percentage": roi_percentage,
    }
