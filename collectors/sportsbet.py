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
