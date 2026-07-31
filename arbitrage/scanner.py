from collectors.mock_sportsbet import MockSportsbetCollector
from collectors.mock_tab import MockTabCollector
from matcher.matcher import normalize_team_name
from arbitrage.calculator import calculate_arbitrage
from arbitrage.stakes import calculate_stakes

COLLECTORS = [MockSportsbetCollector(), MockTabCollector()]

_latest_odds: list[dict] = []
_latest_opportunities: list[dict] = []
_latest_games: list[str] = []


async def run_scan(bankroll: float) -> list[dict]:
    global _latest_odds, _latest_opportunities, _latest_games

    all_odds = []
    for collector in COLLECTORS:
        all_odds.extend(await collector.fetch_odds())

    normalized = []
    for o in all_odds:
        home_raw, away_raw = [p.strip() for p in o["event"].split(" vs ")]
        home = normalize_team_name(home_raw)
        away = normalize_team_name(away_raw)
        selection = normalize_team_name(o["selection"])
        if home is None or away is None or selection is None:
            continue  # unmatched team name, drop this quote
        normalized.append({**o, "event": f"{home} vs {away}", "selection": selection})

    by_game: dict[tuple, dict[str, list[dict]]] = {}
    for o in normalized:
        key = (o["event"], o["market"])
        by_game.setdefault(key, {}).setdefault(o["selection"], []).append(o)

    opportunities = []
    for (event, market), selections in by_game.items():
        if len(selections) != 2:
            continue  # moneyline needs exactly two selections
        (sel_a, odds_a_list), (sel_b, odds_b_list) = selections.items()
        best_a = max(odds_a_list, key=lambda o: o["odds"])
        best_b = max(odds_b_list, key=lambda o: o["odds"])

        arb = calculate_arbitrage(best_a["odds"], best_b["odds"])
        if not arb["is_arbitrage"]:
            continue

        stake = calculate_stakes(bankroll, best_a["odds"], best_b["odds"])
        opportunities.append({
            "game": event,
            "market": market,
            "sportsbook_a": best_a["sportsbook"],
            "selection_a": sel_a,
            "odds_a": best_a["odds"],
            "stake_a": stake["stake_a"],
            "sportsbook_b": best_b["sportsbook"],
            "selection_b": sel_b,
            "odds_b": best_b["odds"],
            "stake_b": stake["stake_b"],
            "arbitrage_percentage": arb["arbitrage_percentage"],
            "roi_percentage": arb["roi_percentage"],
            "guaranteed_return": stake["guaranteed_return"],
            "guaranteed_profit": stake["profit"],
            "timestamp": max(best_a["timestamp"], best_b["timestamp"]),
        })

    _latest_odds = normalized
    _latest_opportunities = opportunities
    _latest_games = sorted({o["event"] for o in normalized})
    return opportunities


def get_latest_odds() -> list[dict]:
    return _latest_odds


def get_latest_opportunities() -> list[dict]:
    return _latest_opportunities


def get_latest_games() -> list[str]:
    return _latest_games
