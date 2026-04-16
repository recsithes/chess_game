from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import (
    GameCreateRequest,
    GameStateResponse,
    MoveRequest,
    MoveResponse,
    PgnResponse,
    RecommendationResponse,
)

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post("", response_model=GameStateResponse)
def create_game(payload: GameCreateRequest, request: Request) -> GameStateResponse:
    chess_service = request.app.state.chess_service
    bot_service = request.app.state.bot_service

    session = chess_service.create_game(
        player_color=payload.player_color,
        bot_mode=payload.bot_mode,
        bot_level=payload.bot_level,
    )

    # If the player picks black, bot opens as white.
    if payload.player_color == "black":
        bot_move = bot_service.choose_move(session.board, session.bot_level, session.bot_mode)
        if bot_move:
            chess_service.apply_move(session, bot_move)

    return GameStateResponse(**chess_service.to_payload(session))


@router.get("/{game_id}", response_model=GameStateResponse)
def get_game(game_id: str, request: Request) -> GameStateResponse:
    chess_service = request.app.state.chess_service
    session = chess_service.get_game(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameStateResponse(**chess_service.to_payload(session))


@router.post("/{game_id}/move", response_model=MoveResponse)
def play_move(game_id: str, payload: MoveRequest, request: Request) -> MoveResponse:
    chess_service = request.app.state.chess_service
    bot_service = request.app.state.bot_service

    session = chess_service.get_game(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")

    status, _ = chess_service.get_status(session)
    if status != "active":
        raise HTTPException(status_code=400, detail="Game already finished")

    if not chess_service.is_player_turn(session):
        raise HTTPException(status_code=409, detail="Not player turn")

    try:
        chess_service.apply_move(session, payload.uci)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    bot_move = None
    bot_source = None
    bot_confidence = None
    status, _ = chess_service.get_status(session)
    if status == "active":
        recommendation = bot_service.recommend_move(
            board=session.board,
            level=session.bot_level,
            mode=session.bot_mode,
        )
        bot_move = recommendation.get("move")
        bot_source = recommendation.get("source")
        bot_confidence = recommendation.get("confidence")
        if bot_move:
            chess_service.apply_move(session, str(bot_move))

    return MoveResponse(
        player_move=payload.uci,
        bot_move=str(bot_move) if bot_move is not None else None,
        bot_source=str(bot_source) if bot_source is not None else None,
        bot_confidence=float(bot_confidence) if bot_confidence is not None else None,
    )


@router.get("/{game_id}/pgn", response_model=PgnResponse)
def get_pgn(game_id: str, request: Request) -> PgnResponse:
    chess_service = request.app.state.chess_service
    session = chess_service.get_game(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return PgnResponse(game_id=game_id, pgn=chess_service.to_pgn(session))


@router.get("/{game_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(game_id: str, request: Request) -> RecommendationResponse:
    chess_service = request.app.state.chess_service
    bot_service = request.app.state.bot_service

    session = chess_service.get_game(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")

    recommendation = bot_service.recommend_move(
        board=session.board,
        level=session.bot_level,
        mode=session.bot_mode,
    )

    return RecommendationResponse(
        game_id=game_id,
        mode=session.bot_mode,
        source=str(recommendation.get("source") or "none"),
        recommended_move=str(recommendation.get("move")) if recommendation.get("move") is not None else None,
        confidence=float(recommendation.get("confidence")) if recommendation.get("confidence") is not None else None,
    )
