from collectors.base import SportsbookCollector
from collectors.mock_data import GAMES, SEEDED_ARB_ODDS, random_odds_pair


class MockTabCollector(SportsbookCollector):
    sportsbook_name = "TAB"

    async def fetch_odds(self) -> list[dict]:
        results = []
        for i, game in enumerate(GAMES):
            event = f"{game['tab_home']} vs {game['tab_away']}"
            if i == 0:
                home_odds, away_odds = SEEDED_ARB_ODDS["tab"]
            else:
                home_odds, away_odds = random_odds_pair(seed=i + 100)
            results.append(self._normalize(event, game["tab_home"], home_odds))
            results.append(self._normalize(event, game["tab_away"], away_odds))
        return results
