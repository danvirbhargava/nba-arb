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
