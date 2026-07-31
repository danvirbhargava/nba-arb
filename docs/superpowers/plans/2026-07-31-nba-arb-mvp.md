# NBA Arbitrage Scanner MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working local NBA arbitrage scanner: mock odds from 2 sportsbooks, team-name matching, arbitrage/stake calculation, a FastAPI backend, and a React dashboard — no database, no real collectors, no Docker (those are later phases).

**Architecture:** Backend is a small pipeline (`collectors` → `matcher` → `arbitrage/scanner`) with all state held in-memory in `arbitrage/scanner.py`, exposed via FastAPI. Frontend is a single-page Vite/React/TS/Tailwind app that calls the API and renders opportunity cards.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, pytest-asyncio, httpx; React 18, TypeScript, Vite, Tailwind CSS.

## Global Constraints

- The app NEVER places bets — it only displays recommendations. No automated betting actions anywhere in the code.
- Moneyline (two-outcome) market only for this MVP.
- No database — all scan results live in in-memory module state in `arbitrage/scanner.py`.
- Bankroll is passed as an explicit argument/query param, never a global.
- Team matching uses only the stdlib `difflib` plus a static alias dict — no new fuzzy-matching dependency.
- Scanning is on-demand only (`POST /scan`) — no background scheduler.
- All git commits use author email `danvir.bhargava1@gmail.com`.

---

### Task 1: Project setup + arbitrage calculator

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `arbitrage/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Create: `arbitrage/calculator.py`
- Test: `tests/test_calculator.py`

**Interfaces:**
- Produces: `calculate_arbitrage(odds_a: float, odds_b: float) -> dict` with keys `is_arbitrage: bool`, `total_implied_probability: float`, `arbitrage_percentage: float`, `roi_percentage: float`. Raises `ValueError` if either odds value is `<= 1`.

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi>=0.110
uvicorn[standard]>=0.27
pydantic>=2.6
httpx>=0.27
pytest>=8.0
pytest-asyncio>=0.23
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 3: Set up a virtualenv and install dependencies**

Run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 4: Create empty package markers**

Create `arbitrage/__init__.py` and `tests/__init__.py`, both empty.

- [ ] **Step 5: Write the failing test**

Create `tests/test_calculator.py`:

```python
import pytest

from arbitrage.calculator import calculate_arbitrage


def test_clean_arbitrage_case():
    result = calculate_arbitrage(2.0, 3.0)
    assert result["is_arbitrage"] is True
    assert result["total_implied_probability"] == pytest.approx(0.8333, abs=0.001)
    assert result["arbitrage_percentage"] == pytest.approx(16.67, abs=0.01)
    assert result["roi_percentage"] == pytest.approx(20.0, abs=0.01)


def test_symmetric_arbitrage_case():
    result = calculate_arbitrage(2.5, 2.5)
    assert result["is_arbitrage"] is True
    assert result["arbitrage_percentage"] == pytest.approx(20.0, abs=0.01)
    assert result["roi_percentage"] == pytest.approx(25.0, abs=0.01)


def test_equal_odds_boundary_is_not_arbitrage():
    result = calculate_arbitrage(2.0, 2.0)
    assert result["is_arbitrage"] is False
    assert result["arbitrage_percentage"] == pytest.approx(0.0, abs=0.01)


def test_no_arbitrage_case():
    result = calculate_arbitrage(1.5, 1.5)
    assert result["is_arbitrage"] is False
    assert result["arbitrage_percentage"] < 0


def test_rejects_odds_at_or_below_one():
    with pytest.raises(ValueError):
        calculate_arbitrage(1.0, 2.0)
    with pytest.raises(ValueError):
        calculate_arbitrage(2.0, 0.5)
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/test_calculator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'arbitrage.calculator'`

- [ ] **Step 7: Implement `arbitrage/calculator.py`**

```python
def calculate_arbitrage(odds_a: float, odds_b: float) -> dict:
    if odds_a <= 1 or odds_b <= 1:
        raise ValueError("Odds must be greater than 1.0")

    implied_a = 1 / odds_a
    implied_b = 1 / odds_b
    total_implied = implied_a + implied_b

    is_arbitrage = total_implied < 1
    arbitrage_percentage = round((1 - total_implied) * 100, 2)
    roi_percentage = round(((1 / total_implied) - 1) * 100, 2)

    return {
        "is_arbitrage": is_arbitrage,
        "total_implied_probability": round(total_implied, 4),
        "arbitrage_percentage": arbitrage_percentage,
        "roi_percentage": roi_percentage,
    }
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_calculator.py -v`
Expected: PASS (5 tests)

- [ ] **Step 9: Commit**

```bash
git add requirements.txt pytest.ini arbitrage/__init__.py tests/__init__.py arbitrage/calculator.py tests/test_calculator.py
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: add arbitrage calculator"
```

---

### Task 2: Stake calculator

**Files:**
- Create: `arbitrage/stakes.py`
- Test: `tests/test_stakes.py`

**Interfaces:**
- Consumes: nothing from Task 1 directly (independent pure function, same math as `calculator.py`).
- Produces: `calculate_stakes(bankroll: float, odds_a: float, odds_b: float) -> dict` with keys `stake_a: float`, `stake_b: float`, `guaranteed_return: float`, `profit: float`. Raises `ValueError` if `bankroll <= 0` or either odds value is `<= 1`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_stakes.py`:

```python
import pytest

from arbitrage.stakes import calculate_stakes


def test_clean_stake_split():
    result = calculate_stakes(1000, 2.0, 3.0)
    assert result["stake_a"] == pytest.approx(600.0, abs=0.01)
    assert result["stake_b"] == pytest.approx(400.0, abs=0.01)
    assert result["guaranteed_return"] == pytest.approx(1200.0, abs=0.01)
    assert result["profit"] == pytest.approx(200.0, abs=0.01)


def test_stakes_sum_to_bankroll():
    result = calculate_stakes(750, 2.15, 4.20)
    assert result["stake_a"] + result["stake_b"] == pytest.approx(750, abs=0.02)


def test_payout_equal_on_both_outcomes():
    result = calculate_stakes(1000, 2.15, 4.20)
    return_a = result["stake_a"] * 2.15
    return_b = result["stake_b"] * 4.20
    assert return_a == pytest.approx(return_b, abs=0.5)


def test_rejects_non_positive_bankroll():
    with pytest.raises(ValueError):
        calculate_stakes(0, 2.0, 3.0)
    with pytest.raises(ValueError):
        calculate_stakes(-100, 2.0, 3.0)


def test_rejects_odds_at_or_below_one():
    with pytest.raises(ValueError):
        calculate_stakes(1000, 1.0, 2.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_stakes.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'arbitrage.stakes'`

- [ ] **Step 3: Implement `arbitrage/stakes.py`**

```python
def calculate_stakes(bankroll: float, odds_a: float, odds_b: float) -> dict:
    if bankroll <= 0:
        raise ValueError("Bankroll must be positive")
    if odds_a <= 1 or odds_b <= 1:
        raise ValueError("Odds must be greater than 1.0")

    implied_a = 1 / odds_a
    implied_b = 1 / odds_b
    total_implied = implied_a + implied_b

    stake_a = round(bankroll * implied_a / total_implied, 2)
    stake_b = round(bankroll * implied_b / total_implied, 2)
    guaranteed_return = round(min(stake_a * odds_a, stake_b * odds_b), 2)
    profit = round(guaranteed_return - bankroll, 2)

    return {
        "stake_a": stake_a,
        "stake_b": stake_b,
        "guaranteed_return": guaranteed_return,
        "profit": profit,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_stakes.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add arbitrage/stakes.py tests/test_stakes.py
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: add stake calculator"
```

---

### Task 3: NBA team name matcher

**Files:**
- Create: `matcher/__init__.py` (empty)
- Create: `matcher/matcher.py`
- Test: `tests/test_matcher.py`

**Interfaces:**
- Produces: `NBA_TEAMS: list[str]` (30 official team names), `normalize_team_name(name: str) -> str | None`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_matcher.py`:

```python
from matcher.matcher import normalize_team_name, NBA_TEAMS


def test_official_name_passes_through():
    assert normalize_team_name("Los Angeles Lakers") == "Los Angeles Lakers"


def test_known_alias_lakers():
    assert normalize_team_name("LA Lakers") == "Los Angeles Lakers"
    assert normalize_team_name("Lakers") == "Los Angeles Lakers"


def test_known_alias_thunder():
    assert normalize_team_name("OKC Thunder") == "Oklahoma City Thunder"
    assert normalize_team_name("OKC") == "Oklahoma City Thunder"


def test_known_alias_knicks():
    assert normalize_team_name("NY Knicks") == "New York Knicks"


def test_fuzzy_fallback_for_typo():
    assert normalize_team_name("Bostn Celtics") == "Boston Celtics"


def test_unknown_team_returns_none():
    assert normalize_team_name("Springfield Isotopes") is None


def test_all_teams_present():
    assert len(NBA_TEAMS) == 30
    assert "Boston Celtics" in NBA_TEAMS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_matcher.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'matcher'`

- [ ] **Step 3: Implement `matcher/matcher.py`**

```python
import difflib

NBA_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans",
    "New York Knicks", "Oklahoma City Thunder", "Orlando Magic",
    "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
    "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz",
    "Washington Wizards",
]

TEAM_ALIASES = {
    "lakers": "Los Angeles Lakers", "la lakers": "Los Angeles Lakers",
    "celtics": "Boston Celtics",
    "warriors": "Golden State Warriors", "gs warriors": "Golden State Warriors",
    "heat": "Miami Heat",
    "thunder": "Oklahoma City Thunder", "okc thunder": "Oklahoma City Thunder", "okc": "Oklahoma City Thunder",
    "nuggets": "Denver Nuggets",
    "bucks": "Milwaukee Bucks",
    "suns": "Phoenix Suns",
    "mavericks": "Dallas Mavericks", "mavs": "Dallas Mavericks",
    "knicks": "New York Knicks", "ny knicks": "New York Knicks",
    "clippers": "LA Clippers", "la clippers": "LA Clippers",
    "hawks": "Atlanta Hawks",
    "nets": "Brooklyn Nets",
    "hornets": "Charlotte Hornets",
    "bulls": "Chicago Bulls",
    "cavaliers": "Cleveland Cavaliers", "cavs": "Cleveland Cavaliers",
    "pistons": "Detroit Pistons",
    "rockets": "Houston Rockets",
    "pacers": "Indiana Pacers",
    "grizzlies": "Memphis Grizzlies",
    "timberwolves": "Minnesota Timberwolves", "wolves": "Minnesota Timberwolves",
    "pelicans": "New Orleans Pelicans",
    "magic": "Orlando Magic",
    "76ers": "Philadelphia 76ers", "sixers": "Philadelphia 76ers",
    "trail blazers": "Portland Trail Blazers", "blazers": "Portland Trail Blazers",
    "kings": "Sacramento Kings",
    "spurs": "San Antonio Spurs",
    "raptors": "Toronto Raptors",
    "jazz": "Utah Jazz",
    "wizards": "Washington Wizards",
}


def normalize_team_name(name: str) -> str | None:
    key = name.strip().lower()
    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key]

    matches = difflib.get_close_matches(name.strip(), NBA_TEAMS, n=1, cutoff=0.6)
    if matches:
        return matches[0]

    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_matcher.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add matcher/__init__.py matcher/matcher.py tests/test_matcher.py
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: add NBA team name matcher"
```

---

### Task 4: Collector interface + mock collectors

**Files:**
- Create: `collectors/__init__.py` (empty)
- Create: `collectors/base.py`
- Create: `collectors/mock_data.py`
- Create: `collectors/mock_sportsbet.py`
- Create: `collectors/mock_tab.py`
- Test: `tests/test_collectors.py`

**Interfaces:**
- Produces: `SportsbookCollector` (ABC with `sportsbook_name: str` and `async fetch_odds(self) -> list[dict]`), each normalized odds dict has keys `event, market, selection, odds, sportsbook, timestamp`. `MockSportsbetCollector`, `MockTabCollector` — both `SportsbookCollector` subclasses. `GAMES: list[dict]` and `SEEDED_ARB_ODDS: dict` in `collectors/mock_data.py`, used by Task 5.

- [ ] **Step 1: Write the failing test**

Create `tests/test_collectors.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_collectors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'collectors'`

- [ ] **Step 3: Implement `collectors/base.py`**

```python
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class SportsbookCollector(ABC):
    sportsbook_name: str

    @abstractmethod
    async def fetch_odds(self) -> list[dict]:
        """Return normalized odds dicts, one per (game, selection)."""

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize(self, event: str, selection: str, odds: float) -> dict:
        return {
            "event": event,
            "market": "moneyline",
            "selection": selection,
            "odds": odds,
            "sportsbook": self.sportsbook_name,
            "timestamp": self._timestamp(),
        }
```

- [ ] **Step 4: Implement `collectors/mock_data.py`**

```python
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
```

- [ ] **Step 5: Implement `collectors/mock_sportsbet.py`**

```python
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
```

- [ ] **Step 6: Implement `collectors/mock_tab.py`**

```python
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
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_collectors.py -v`
Expected: PASS (3 tests)

- [ ] **Step 8: Commit**

```bash
git add collectors/
git add tests/test_collectors.py
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: add collector interface and mock sportsbook collectors"
```

---

### Task 5: Arbitrage scanner (orchestration)

**Files:**
- Create: `arbitrage/scanner.py`
- Test: `tests/test_scanner.py`

**Interfaces:**
- Consumes: `MockSportsbetCollector`, `MockTabCollector` (Task 4), `normalize_team_name` (Task 3), `calculate_arbitrage` (Task 1), `calculate_stakes` (Task 2).
- Produces: `async run_scan(bankroll: float) -> list[dict]`, `get_latest_odds() -> list[dict]`, `get_latest_opportunities() -> list[dict]`, `get_latest_games() -> list[str]`. Each opportunity dict has keys: `game, market, sportsbook_a, selection_a, odds_a, stake_a, sportsbook_b, selection_b, odds_b, stake_b, arbitrage_percentage, roi_percentage, guaranteed_return, guaranteed_profit, timestamp`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_scanner.py`:

```python
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
async def test_unmatched_team_names_are_dropped_not_crashed():
    # Sanity: scanning twice in a row doesn't error even though random
    # games (1-4) rarely produce arbitrage.
    result_1 = await scanner.run_scan(bankroll=1000)
    result_2 = await scanner.run_scan(bankroll=1000)
    assert isinstance(result_1, list)
    assert isinstance(result_2, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner.py -v`
Expected: FAIL with `AttributeError: module 'arbitrage.scanner' has no attribute 'run_scan'` (or `ModuleNotFoundError` if the file doesn't exist yet)

- [ ] **Step 3: Implement `arbitrage/scanner.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add arbitrage/scanner.py tests/test_scanner.py
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: add arbitrage scanner orchestration"
```

---

### Task 6: FastAPI backend

**Files:**
- Create: `api/__init__.py` (empty)
- Create: `api/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `arbitrage.scanner.run_scan`, `get_latest_odds`, `get_latest_opportunities`, `get_latest_games` (Task 5).
- Produces: FastAPI app at `api.main:app` with routes `GET /health`, `POST /scan`, `GET /games`, `GET /odds`, `GET /arbitrage`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_then_arbitrage_and_games():
    scan_response = client.post("/scan", params={"bankroll": 1000})
    assert scan_response.status_code == 200
    opportunities = scan_response.json()
    assert any(o["game"] == "Los Angeles Lakers vs Boston Celtics" for o in opportunities)

    arb_response = client.get("/arbitrage")
    assert arb_response.status_code == 200
    assert arb_response.json() == opportunities

    games_response = client.get("/games")
    assert games_response.status_code == 200
    assert "Los Angeles Lakers vs Boston Celtics" in games_response.json()

    odds_response = client.get("/odds")
    assert odds_response.status_code == 200
    assert len(odds_response.json()) > 0


def test_scan_defaults_bankroll_when_not_provided():
    response = client.post("/scan")
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'api'`

- [ ] **Step 3: Implement `api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from arbitrage import scanner

app = FastAPI(title="NBA Arbitrage Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OddsOut(BaseModel):
    event: str
    market: str
    selection: str
    odds: float
    sportsbook: str
    timestamp: str


class OpportunityOut(BaseModel):
    game: str
    market: str
    sportsbook_a: str
    selection_a: str
    odds_a: float
    stake_a: float
    sportsbook_b: str
    selection_b: str
    odds_b: float
    stake_b: float
    arbitrage_percentage: float
    roi_percentage: float
    guaranteed_return: float
    guaranteed_profit: float
    timestamp: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/scan", response_model=list[OpportunityOut])
async def scan(bankroll: float = 1000.0) -> list[dict]:
    return await scanner.run_scan(bankroll)


@app.get("/games", response_model=list[str])
async def games() -> list[str]:
    return scanner.get_latest_games()


@app.get("/odds", response_model=list[OddsOut])
async def odds() -> list[dict]:
    return scanner.get_latest_odds()


@app.get("/arbitrage", response_model=list[OpportunityOut])
async def arbitrage() -> list[dict]:
    return scanner.get_latest_opportunities()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add api/ tests/test_api.py
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: add FastAPI backend"
```

---

### Task 7: React dashboard scaffold + API client

**Files:**
- Create: `dashboard/` (via Vite scaffold)
- Create: `dashboard/src/types.ts`
- Create: `dashboard/src/api.ts`
- Modify: `dashboard/tailwind.config.js`, `dashboard/src/index.css`

**Interfaces:**
- Produces: `Opportunity` TS type matching `OpportunityOut` from Task 6. `scanNow(bankroll: number): Promise<Opportunity[]>`, `fetchArbitrage(): Promise<Opportunity[]>` in `src/api.ts`.

- [ ] **Step 1: Scaffold the Vite project**

Run from repo root:
```bash
npm create vite@latest dashboard -- --template react-ts
cd dashboard
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
cd ..
```

- [ ] **Step 2: Configure Tailwind content paths**

Edit `dashboard/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 3: Add Tailwind directives**

Replace the contents of `dashboard/src/index.css` with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: Create `dashboard/src/types.ts`**

```typescript
export interface Opportunity {
  game: string;
  market: string;
  sportsbook_a: string;
  selection_a: string;
  odds_a: number;
  stake_a: number;
  sportsbook_b: string;
  selection_b: string;
  odds_b: number;
  stake_b: number;
  arbitrage_percentage: number;
  roi_percentage: number;
  guaranteed_return: number;
  guaranteed_profit: number;
  timestamp: string;
}
```

- [ ] **Step 5: Create `dashboard/src/api.ts`**

```typescript
import type { Opportunity } from "./types";

const BASE_URL = "http://localhost:8000";

export async function scanNow(bankroll: number): Promise<Opportunity[]> {
  const response = await fetch(`${BASE_URL}/scan?bankroll=${bankroll}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Scan failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchArbitrage(): Promise<Opportunity[]> {
  const response = await fetch(`${BASE_URL}/arbitrage`);
  if (!response.ok) {
    throw new Error(`Failed to fetch arbitrage: ${response.status}`);
  }
  return response.json();
}
```

- [ ] **Step 6: Verify the scaffold builds**

Run:
```bash
cd dashboard
npm run build
cd ..
```
Expected: build succeeds with no TypeScript errors.

- [ ] **Step 7: Commit**

```bash
git add dashboard/
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: scaffold React dashboard with Tailwind and API client"
```

---

### Task 8: Dashboard UI (bankroll input, scan, opportunity cards)

**Files:**
- Create: `dashboard/src/components/OpportunityCard.tsx`
- Modify: `dashboard/src/App.tsx`

**Interfaces:**
- Consumes: `Opportunity` (Task 7 `types.ts`), `scanNow`, `fetchArbitrage` (Task 7 `api.ts`).
- Produces: `OpportunityCard` component taking `{ opportunity: Opportunity }` props; `App` renders bankroll input, Scan Now button, sorted/filtered card list.

- [ ] **Step 1: Create `dashboard/src/components/OpportunityCard.tsx`**

```tsx
import type { Opportunity } from "../types";

function oddsAgeLabel(timestamp: string): string {
  const ageSeconds = (Date.now() - new Date(timestamp).getTime()) / 1000;
  if (ageSeconds < 60) return `${Math.floor(ageSeconds)}s ago`;
  return `${Math.floor(ageSeconds / 60)}m ago`;
}

export function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const isStrong = opportunity.roi_percentage >= 3;

  return (
    <div className={`rounded-lg border p-4 shadow-sm ${isStrong ? "border-green-400 bg-green-50" : "border-gray-200 bg-white"}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🏀 {opportunity.game}</h3>
        <span className="text-sm text-gray-500">{oddsAgeLabel(opportunity.timestamp)}</span>
      </div>

      <div className="mt-1 flex gap-4 text-sm">
        <span className="font-medium text-green-700">ROI {opportunity.roi_percentage.toFixed(1)}%</span>
        <span className="text-gray-600">Guaranteed profit ${opportunity.guaranteed_profit.toFixed(2)}</span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded border border-gray-100 p-2">
          <div className="font-semibold">{opportunity.sportsbook_a}</div>
          <div>{opportunity.selection_a}</div>
          <div>Odds: {opportunity.odds_a}</div>
          <div>Stake: ${opportunity.stake_a.toFixed(2)}</div>
        </div>
        <div className="rounded border border-gray-100 p-2">
          <div className="font-semibold">{opportunity.sportsbook_b}</div>
          <div>{opportunity.selection_b}</div>
          <div>Odds: {opportunity.odds_b}</div>
          <div>Stake: ${opportunity.stake_b.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Replace `dashboard/src/App.tsx`**

```tsx
import { useMemo, useState } from "react";
import { scanNow } from "./api";
import type { Opportunity } from "./types";
import { OpportunityCard } from "./components/OpportunityCard";

function App() {
  const [bankroll, setBankroll] = useState(1000);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [minProfit, setMinProfit] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleScan() {
    setLoading(true);
    setError(null);
    try {
      const results = await scanNow(bankroll);
      setOpportunities(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  const visibleOpportunities = useMemo(() => {
    return opportunities
      .filter((o) => o.roi_percentage >= minProfit)
      .sort((a, b) => b.roi_percentage - a.roi_percentage);
  }, [opportunities, minProfit]);

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-bold">NBA Arbitrage Scanner</h1>

      <div className="mt-4 flex flex-wrap items-end gap-4">
        <label className="flex flex-col text-sm">
          Bankroll
          <input
            type="number"
            className="mt-1 w-32 rounded border border-gray-300 p-2"
            value={bankroll}
            onChange={(e) => setBankroll(Number(e.target.value))}
          />
        </label>

        <label className="flex flex-col text-sm">
          Min profit %
          <input
            type="number"
            className="mt-1 w-32 rounded border border-gray-300 p-2"
            value={minProfit}
            onChange={(e) => setMinProfit(Number(e.target.value))}
          />
        </label>

        <button
          onClick={handleScan}
          disabled={loading}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? "Scanning..." : "Scan Now"}
        </button>
      </div>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      <h2 className="mt-8 text-lg font-semibold">Active Opportunities</h2>
      <div className="mt-3 flex flex-col gap-3">
        {visibleOpportunities.length === 0 && (
          <p className="text-gray-500">No opportunities yet — click Scan Now.</p>
        )}
        {visibleOpportunities.map((o) => (
          <OpportunityCard key={`${o.game}-${o.sportsbook_a}-${o.sportsbook_b}`} opportunity={o} />
        ))}
      </div>
    </div>
  );
}

export default App;
```

- [ ] **Step 3: Run the backend and frontend together, verify in browser**

Run in one terminal:
```bash
source .venv/bin/activate
uvicorn api.main:app --reload
```

Run in another terminal:
```bash
cd dashboard
npm run dev
```

Open the printed dashboard URL (typically `http://localhost:5173`). Enter a bankroll, click "Scan Now", and confirm:
- The "Los Angeles Lakers vs Boston Celtics" card appears with Sportsbet/TAB odds and stakes.
- Changing "Min profit %" filters cards.
- Cards are sorted by ROI descending.

- [ ] **Step 4: Commit**

```bash
git add dashboard/src/App.tsx dashboard/src/components/OpportunityCard.tsx
git -c user.email="danvir.bhargava1@gmail.com" commit -m "feat: build dashboard UI with scan, sort, and filter"
```

---

### Task 9: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write run instructions**

Replace `README.md` contents:

```markdown
# NBA Arbitrage Scanner (MVP)

Local NBA arbitrage betting scanner. Detects arbitrage opportunities across
mock sportsbook odds and displays recommended stakes. **This app never
places bets** — it's a read-only dashboard for manual decision-making.

## Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

API docs: http://localhost:8000/docs

## Frontend

```bash
cd dashboard
npm install
npm run dev
```

Dashboard: http://localhost:5173

## Tests

```bash
source .venv/bin/activate
pytest -v
```

## Scope

This is the MVP slice: 2 mock sportsbooks, in-memory state, moneyline
market only, on-demand scanning. See `docs/superpowers/specs/` for the full
design and the project's phased roadmap (real collectors, Postgres,
Docker).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git -c user.email="danvir.bhargava1@gmail.com" commit -m "docs: add setup and run instructions"
```
