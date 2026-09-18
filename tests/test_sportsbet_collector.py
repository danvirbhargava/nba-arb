from pathlib import Path

from collectors.sportsbet import _parse_events

FIXTURE = (Path(__file__).parent / "fixtures" / "sportsbet_basketball_us.html").read_text()


def test_parse_events_returns_all_fixture_events():
    events = _parse_events(FIXTURE)
    assert len(events) == 6
    for event in events:
        assert set(event.keys()) == {"competition", "team_a", "odds_a", "team_b", "odds_b"}
        assert isinstance(event["odds_a"], float)
        assert isinstance(event["odds_b"], float)


def test_no_nba_games_in_current_fixture():
    events = _parse_events(FIXTURE)
    nba_events = [e for e in events if e["competition"] == "NBA"]
    assert nba_events == []


def test_parse_events_skips_malformed_card():
    html = """
    <div data-automation-id="123-competition-event-card">
        <span data-automation-id="competition-name">NBA</span>
        <span data-automation-id="123-two-outcome-captioned-label">Lakers</span>
        <span data-automation-id="123-two-outcome-captioned-text">1.50</span>
    </div>
    """
    assert _parse_events(html) == []


def test_parse_events_skips_non_numeric_price():
    html = """
    <div data-automation-id="123-competition-event-card">
        <span data-automation-id="competition-name">NBA</span>
        <span data-automation-id="123-two-outcome-captioned-label">Lakers</span>
        <span data-automation-id="123-two-outcome-captioned-label">Celtics</span>
        <span data-automation-id="123-two-outcome-captioned-text">SUSP</span>
        <span data-automation-id="123-two-outcome-captioned-text">2.10</span>
    </div>
    """
    assert _parse_events(html) == []
