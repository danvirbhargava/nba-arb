import pytest

from collectors.mock_sportsbet import MockSportsbetCollector
from collectors.mock_tab import MockTabCollector


@pytest.mark.asyncio
async def test_sportsbet_returns_normalized_odds():
    odds = await MockSportsbetCollector().fetch_odds()
    assert len(odds) == 10  # 5 games x 2 selections
    first = odds[0]
    assert set(first.keys()) == {"event", "market", "selection", "odds", "sportsbook", "timestamp"}
    assert first["sportsbook"] == "Sportsbet"
    assert first["market"] == "moneyline"
    assert " vs " in first["event"]


@pytest.mark.asyncio
async def test_tab_returns_normalized_odds():
    odds = await MockTabCollector().fetch_odds()
    assert len(odds) == 10
    assert odds[0]["sportsbook"] == "TAB"


@pytest.mark.asyncio
async def test_seeded_game_has_expected_odds():
    sportsbet_odds = await MockSportsbetCollector().fetch_odds()
    lakers = next(o for o in sportsbet_odds if o["selection"] == "LA Lakers")
    assert lakers["odds"] == 2.15
