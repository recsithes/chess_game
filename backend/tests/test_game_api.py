from fastapi.testclient import TestClient

from app.main import app


def test_create_game_and_play_move() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/games",
            json={"player_color": "white", "bot_mode": "engine", "bot_level": 1},
        )
        assert create_response.status_code == 200

        game = create_response.json()
        game_id = game["game_id"]
        assert game["bot_mode"] == "engine"
        assert isinstance(game["san_moves"], list)
        assert game["last_move"] is None
        assert game["last_move_san"] is None
        assert isinstance(game["is_check"], bool)
        assert isinstance(game["is_checkmate"], bool)
        assert isinstance(game["is_stalemate"], bool)

        move_response = client.post(f"/api/games/{game_id}/move", json={"uci": "e2e4"})
        assert move_response.status_code == 200

        move_payload = move_response.json()
        assert move_payload["player_move"] == "e2e4"

        state_response = client.get(f"/api/games/{game_id}")
        assert state_response.status_code == 200

        state = state_response.json()
        assert len(state["moves"]) >= 1
        assert len(state["san_moves"]) >= 1
        assert state["last_move"] is not None
        assert state["last_move_san"] is not None


def test_reject_illegal_move() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/games",
            json={"player_color": "white", "bot_mode": "engine", "bot_level": 1},
        )
        game_id = create_response.json()["game_id"]

        move_response = client.post(f"/api/games/{game_id}/move", json={"uci": "e2e5"})
        assert move_response.status_code == 400
        assert "Illegal move" in move_response.json()["detail"]


def test_recommendation_endpoint() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/games",
            json={"player_color": "white", "bot_mode": "ml", "bot_level": 1},
        )
        assert create_response.status_code == 200
        game_id = create_response.json()["game_id"]

        recommendation_response = client.get(f"/api/games/{game_id}/recommendation")
        assert recommendation_response.status_code == 200

        payload = recommendation_response.json()
        assert payload["mode"] == "ml"
        assert payload["source"] in {"ml", "engine", "random", "none"}


def test_cors_preflight_for_games_endpoint() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/games",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_bot_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/system/bot-health")
        assert response.status_code == 200

        payload = response.json()
        assert isinstance(payload["engine_available"], bool)
        assert isinstance(payload["ml_model_loaded"], bool)
        assert isinstance(payload["ml_confidence_threshold"], (int, float))
