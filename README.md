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
