import pytest

from arbitrage import scanner


@pytest.mark.asyncio
async def test_run_scan_finds_seeded_arbitrage():
    opportunities = await scanner.run_scan(bankroll=1000)

    game0 = next(o for o in opportunities if o["game"] == "Los Angeles Lakers vs Boston Celtics")
    assert game0["sportsbook_a"] == "Sportsbet"
    assert game0["odds_a"] == 2.15
    assert game0["sportsbook_b"] == "TAB"
    assert game0["odds_b"] == 4.2
    assert game0["arbitrage_percentage"] > 0
    assert game0["stake_a"] + game0["stake_b"] == pytest.approx(1000, abs=0.5)


@pytest.mark.asyncio
async def test_run_scan_updates_latest_state():
    await scanner.run_scan(bankroll=500)
    assert scanner.get_latest_odds()
    assert scanner.get_latest_opportunities()
    assert "Los Angeles Lakers vs Boston Celtics" in scanner.get_latest_games()


@pytest.mark.asyncio
async def test_repeated_scans_are_stable():
    # Sanity: scanning twice in a row doesn't error even though random
    # games (1-4) rarely produce arbitrage.
    result_1 = await scanner.run_scan(bankroll=1000)
    result_2 = await scanner.run_scan(bankroll=1000)
    assert isinstance(result_1, list)
    assert isinstance(result_2, list)
