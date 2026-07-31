import random

GAMES = [
    {
        "sportsbet_home": "LA Lakers", "sportsbet_away": "Boston Celtics",
        "tab_home": "Los Angeles Lakers", "tab_away": "Celtics",
    },
    {
        "sportsbet_home": "Golden State Warriors", "sportsbet_away": "Miami Heat",
        "tab_home": "GS Warriors", "tab_away": "Miami Heat",
    },
    {
        "sportsbet_home": "OKC Thunder", "sportsbet_away": "Denver Nuggets",
        "tab_home": "Oklahoma City Thunder", "tab_away": "Denver Nuggets",
    },
    {
        "sportsbet_home": "Milwaukee Bucks", "sportsbet_away": "Phoenix Suns",
        "tab_home": "Milwaukee Bucks", "tab_away": "Phoenix Suns",
    },
    {
        "sportsbet_home": "Dallas Mavericks", "sportsbet_away": "NY Knicks",
        "tab_home": "Dallas Mavericks", "tab_away": "New York Knicks",
    },
]

# Game 0 (Lakers vs Celtics) is seeded so a scan always produces at least
# one arbitrage opportunity, for a reliable demo/test.
SEEDED_ARB_ODDS = {
    "sportsbet": (2.15, 3.60),  # (home, away)
    "tab": (1.95, 4.20),
}


def random_odds_pair(seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    home = round(rng.uniform(1.5, 4.0), 2)
    away = round(rng.uniform(1.5, 4.0), 2)
    return home, away
