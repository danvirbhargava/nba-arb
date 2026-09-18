import pytest

from collectors.mock_tab import MockTabCollector


@pytest.mark.asyncio
async def test_tab_returns_normalized_odds():
    odds = await MockTabCollector().fetch_odds()
    assert len(odds) == 10
    first = odds[0]
    assert set(first.keys()) == {"event", "market", "selection", "odds", "sportsbook", "timestamp"}
    assert first["sportsbook"] == "TAB"
    assert first["market"] == "moneyline"
    assert " vs " in first["event"]
