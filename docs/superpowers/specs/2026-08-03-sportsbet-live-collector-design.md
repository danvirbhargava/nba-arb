# Live Sportsbet Collector — Design

## Goal

Replace the mock Sportsbet collector with a real one that scrapes NBA
moneyline odds from `sportsbet.com.au`, while keeping the app fully
functional today even though NBA is currently off-season (only WNBA games
are listed on the shared basketball-us page right now).

## Scope

In scope:
- `collectors/sportsbet.py`: a real `SportsbetCollector` matching the
  existing `SportsbookCollector` interface, using Playwright (headless
  Chromium) to render `sportsbet.com.au/betting/basketball-us` and extract
  NBA moneyline odds.
- A pure `_parse_events(html) -> list[dict]` function, separable from the
  live fetch, unit-tested against a real captured HTML fixture.
- Swapping `scanner.py`'s `COLLECTORS` list to use the real
  `SportsbetCollector` in place of `MockSportsbetCollector`, keeping
  `MockTabCollector` as-is.
- Changing `scanner.run_scan` to fetch all collectors concurrently
  (`asyncio.gather`) instead of sequentially, so scan time stays close to
  the slowest single collector as more real (slow) collectors are added
  later.
- New dependencies: `playwright`, `beautifulsoup4` (HTML parsing for the
  pure parse function; Playwright's own DOM queries are used for the live
  fetch, but the pure/testable path parses a plain HTML string).
- A one-time manual live verification (not part of the automated test
  suite) that the fetch pipeline works against the real site today.

Out of scope:
- Any other real sportsbook (TAB, betr, etc.) — one collector at a time.
- Retrying failed scrapes, caching, or rate-limiting — a single fetch per
  scan, fail-soft to `[]`, is enough for a local single-user MVP.
- Any change to the arbitrage/stakes/matcher logic — this is a data-source
  change only.

## Architecture

`collectors/sportsbet.py`:

```python
import logging

from playwright.async_api import async_playwright

from collectors.base import SportsbookCollector

logger = logging.getLogger(__name__)

BASKETBALL_US_URL = "https://www.sportsbet.com.au/betting/basketball-us"

CARD_SELECTOR = '[data-automation-id$="-competition-event-card"]'
COMPETITION_SELECTOR = '[data-automation-id="competition-name"]'
LABEL_SELECTOR = '[data-automation-id$="-two-outcome-captioned-label"]'
TEXT_SELECTOR = '[data-automation-id$="-two-outcome-captioned-text"]'


def _parse_events(html: str) -> list[dict]:
    """Pure parse: raw page HTML -> [{competition, team_a, odds_a, team_b, odds_b}, ...].

    No filtering by competition here — that's fetch_odds()'s job, so this
    function can be unit-tested against a fixture without caring which
    competitions happen to be listed on a given day.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    events = []
    for card in soup.select(CARD_SELECTOR):
        competition_el = card.select_one(COMPETITION_SELECTOR)
        labels = card.select(LABEL_SELECTOR)
        texts = card.select(TEXT_SELECTOR)
        if competition_el is None or len(labels) != 2 or len(texts) != 2:
            continue  # not a standard two-outcome moneyline card, skip

        try:
            odds_a = float(texts[0].get_text(strip=True))
            odds_b = float(texts[1].get_text(strip=True))
        except ValueError:
            continue  # price wasn't a plain number (suspended market etc.)

        events.append({
            "competition": competition_el.get_text(strip=True),
            "team_a": labels[0].get_text(strip=True),
            "odds_a": odds_a,
            "team_b": labels[1].get_text(strip=True),
            "odds_b": odds_b,
        })
    return events


class SportsbetCollector(SportsbookCollector):
    sportsbook_name = "Sportsbet"

    async def fetch_odds(self) -> list[dict]:
        try:
            html = await self._fetch_rendered_html()
        except Exception:
            logger.warning("Sportsbet fetch failed", exc_info=True)
            return []

        results = []
        for event in _parse_events(html):
            if event["competition"] != "NBA":
                continue
            matchup = f"{event['team_a']} vs {event['team_b']}"
            results.append(self._normalize(matchup, event["team_a"], event["odds_a"]))
            results.append(self._normalize(matchup, event["team_b"], event["odds_b"]))
        return results

    async def _fetch_rendered_html(self) -> str:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(BASKETBALL_US_URL, timeout=15000)
                await page.wait_for_selector(CARD_SELECTOR, timeout=10000)
                return await page.content()
            finally:
                await browser.close()
```

`scanner.py` changes:

```python
COLLECTORS = [SportsbetCollector(), MockTabCollector()]

async def run_scan(bankroll: float) -> list[dict]:
    ...
    odds_lists = await asyncio.gather(*(c.fetch_odds() for c in COLLECTORS))
    all_odds = [o for odds in odds_lists for o in odds]
    ...
```

Each collector already catches its own scrape/parse errors and returns
`[]`, so `gather`'s default "raise on first exception" behavior never
actually triggers here — one collector failing just means fewer odds in
`all_odds` that scan, not a broken scan.

## Testing

`tests/fixtures/sportsbet_basketball_us.html`: a real HTML snapshot
captured live from `sportsbet.com.au/betting/basketball-us` during this
design session (6 real WNBA games, real odds, real markup — not
synthetic).

`tests/test_sportsbet_collector.py`:
- `_parse_events` against the fixture returns all 6 WNBA events with
  correct team names and odds (proves the parser works against real
  markup).
- `fetch_odds`'s NBA-only filtering logic, tested directly against the
  fixture's parsed events (not through a live Playwright call): filtering
  the fixture's events for `competition == "NBA"` returns `[]`, since
  today's real page has no NBA games — this documents and verifies
  today's off-season reality is handled as a normal empty result, not an
  error.
- A malformed/partial card (e.g. missing a label or non-numeric price) is
  skipped without raising — tests this against a small hand-built HTML
  snippet.

One-time manual verification (run once during implementation, documented
in the task, not part of `pytest`): actually run `SportsbetCollector().fetch_odds()`
against the live site to confirm the real Playwright fetch pipeline works
today (expected result: `[]`, since NBA isn't listed — the point is
proving the *pipeline* works, not that it returns data).

## Risks / assumptions

- Sportsbet's DOM structure (the `data-automation-id` attributes) could
  change at any time; this scraper isn't guaranteed to keep working
  without maintenance. The fail-soft design (log + return `[]`) means a
  breakage degrades the app rather than crashing it, but recommended
  opportunities would silently stop including Sportsbet until someone
  notices and fixes the selectors.
- Playwright requires a one-time `playwright install chromium` step
  (downloads a browser binary) beyond `pip install` — must be documented
  in the README, since a fresh `pip install -r requirements.txt` alone
  won't be enough to run this collector.
- A live scan now takes several seconds (real page load + render) instead
  of being near-instant. `asyncio.gather` keeps this from compounding as
  more real collectors are added, but a single slow/hanging collector
  (e.g. network stall) still adds that latency to every scan until it
  times out (15s page-load timeout, 10s selector-wait timeout — worst
  case ~25s for one collector).
- This is scraping a public-facing page for personal/informational
  display only (no automated betting, no redistribution) — consistent
  with the project's stated non-negotiable: the app never places bets.
