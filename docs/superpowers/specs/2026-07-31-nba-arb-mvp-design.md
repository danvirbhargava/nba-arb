# NBA Arbitrage Scanner — MVP Design

## Goal

Local NBA-only arbitrage betting scanner. User manually places bets — the app
never places bets, it only detects and displays opportunities. This spec
covers the MVP slice: mock odds → team matching → arbitrage detection →
FastAPI backend → React dashboard. Real sportsbook collectors, Postgres
persistence, and Docker packaging are explicitly deferred to later phases.

## Scope

In scope for MVP:
- Mock collectors for 2 sportsbooks (Sportsbet, TAB) generating realistic
  odds for ~5 NBA games, moneyline market only.
- Deterministic + fuzzy team name matcher to official NBA team names.
- Arbitrage calculator + stake calculator (pure functions, bankroll passed
  in as an argument).
- FastAPI backend with in-memory state (no database).
- React + TypeScript + Tailwind dashboard.
- Tests for calculator, stakes, and matcher edge cases.

Out of scope (later phases per the project's phased plan):
- Real sportsbook collectors (betr, neds, ladbrokes, pointsbet, live
  sportsbet/tab scraping or API integration).
- Postgres/SQLAlchemy persistence, migrations.
- Docker Compose.
- Background/scheduled scanning (MVP is on-demand only, via button/API).
- Multi-outcome markets (spreads, totals) — moneyline (2-outcome) only.

## Architecture

```
nba-arb/
├── collectors/
│   ├── base.py            # SportsbookCollector interface + normalized odds shape
│   ├── mock_sportsbet.py
│   └── mock_tab.py
├── matcher/
│   └── matcher.py         # NBA_TEAMS alias dict + difflib fallback
├── arbitrage/
│   ├── calculator.py      # arbitrage %, ROI
│   ├── stakes.py          # stake split for a given bankroll
│   └── scanner.py         # orchestrates collectors -> matcher -> calculator,
│                           # holds latest results in memory
├── api/
│   └── main.py            # FastAPI: /games /odds /arbitrage /scan /health
├── dashboard/              # React + TypeScript + Tailwind
├── tests/
├── requirements.txt
└── README.md
```

No `database/` or `docker-compose.yml` in this slice — added when Phase 2 /
Docker packaging is tackled.

## Data flow

1. `POST /scan` triggers `scanner.run_scan(bankroll)`.
2. Each collector's `fetch_odds()` returns a list of normalized odds dicts:
   ```python
   {
       "event": "Los Angeles Lakers vs Boston Celtics",
       "market": "moneyline",
       "selection": "Los Angeles Lakers",
       "odds": 2.15,
       "sportsbook": "Sportsbet",
       "timestamp": "2026-07-31T12:00:00Z",
   }
   ```
3. `matcher.py` normalizes team names in each `event`/`selection` to the
   official NBA team name, so odds from different books referring to the
   same game are grouped together. Matching strategy: check a static alias
   dict first (`NBA_TEAMS`, e.g. "OKC Thunder" / "Oklahoma City Thunder" /
   "Thunder" → "Oklahoma City Thunder"); if no alias hits, fall back to
   `difflib.get_close_matches` against the list of 30 official team names.
   No new dependency — stdlib only.
4. `arbitrage/scanner.py` groups matched odds by game + market, and for each
   game with exactly two selections, calls `calculator.py`:
   - `1/odds_a + 1/odds_b < 1` → arbitrage exists.
   - Computes arbitrage percentage and ROI.
   - Calls `stakes.py` to split the given bankroll into `stake_a`/`stake_b`
     such that payout is equal regardless of outcome, and to compute
     guaranteed return/profit.
5. Results are stored in an in-memory list on the scanner (module-level
   state, single-process — fine for a local single-user app). `GET /games`,
   `GET /odds`, `GET /arbitrage` read from that state; they do not trigger a
   new scan.

## API

- `POST /scan?bankroll=1000` — runs a scan, returns the list of arbitrage
  opportunities found (also updates in-memory state for subsequent GETs).
- `GET /games` — games seen in the last scan.
- `GET /odds` — raw normalized odds from the last scan.
- `GET /arbitrage` — arbitrage opportunities from the last scan.
- `GET /health` — liveness check.
- All responses validated via Pydantic models. No scan yet run → empty
  lists, not an error.

## Frontend

- Bankroll input (defaults to $1000) + "Scan Now" button: calls
  `POST /scan` with the bankroll, then re-fetches `/arbitrage`.
- Opportunity cards: game, market, both sportsbooks/selections/odds/stakes,
  guaranteed profit, ROI %, odds age (computed client-side from timestamp).
- Sort by ROI descending (default); client-side filter by minimum profit %.
- Plain Tailwind styling, no charts, no animations, responsive grid of
  cards.

## Testing

- `arbitrage/calculator.py`: known-arb case, no-arb case, equal odds,
  negative/zero profit edge case.
- `arbitrage/stakes.py`: bankroll split correctness (stakes sum to
  bankroll, payouts equal on both outcomes) across a few bankroll sizes.
- `matcher/matcher.py`: alias-dict hits ("LA Lakers", "OKC Thunder"),
  difflib fallback for an unlisted variant, no-match case.
- `api/main.py`: smoke test — `/health` returns 200, `/scan` then
  `/arbitrage` returns a non-error response shaped per the Pydantic model.

## Risks / assumptions

- Mock odds are randomized within realistic NBA moneyline ranges each scan;
  at least one game's odds are seeded so a scan reliably produces an arb hit
  for demo/testing purposes.
- In-memory state means results are lost on server restart and won't work
  across multiple worker processes — acceptable for a local single-user MVP.
- difflib fuzzy matching is a heuristic; it's adequate for a fixed 30-team
  vocabulary but would need revisiting if non-NBA or malformed event strings
  ever reach the matcher.
