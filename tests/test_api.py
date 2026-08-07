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


def test_scan_rejects_non_positive_bankroll():
    response = client.post("/scan", params={"bankroll": 0})
    assert response.status_code == 422
