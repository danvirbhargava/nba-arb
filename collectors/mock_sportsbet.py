from collectors.base import SportsbookCollector
from collectors.mock_data import GAMES, SEEDED_ARB_ODDS, random_odds_pair


class MockSportsbetCollector(SportsbookCollector):
    sportsbook_name = "Sportsbet"

    async def fetch_odds(self) -> list[dict]:
        results = []
        for i, game in enumerate(GAMES):
            event = f"{game['sportsbet_home']} vs {game['sportsbet_away']}"
            if i == 0:
                home_odds, away_odds = SEEDED_ARB_ODDS["sportsbet"]
            else:
                home_odds, away_odds = random_odds_pair(seed=i)
            results.append(self._normalize(event, game["sportsbet_home"], home_odds))
            results.append(self._normalize(event, game["sportsbet_away"], away_odds))
        return results
