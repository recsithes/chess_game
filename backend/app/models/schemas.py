from typing import Literal

from pydantic import BaseModel, Field


Color = Literal["white", "black"]
BotMode = Literal["engine", "ml"]


class GameCreateRequest(BaseModel):
    player_color: Color = "white"
    bot_mode: BotMode = "engine"
    bot_level: int = Field(default=5, ge=0, le=50)


class MoveRequest(BaseModel):
    uci: str = Field(min_length=4, max_length=5)


class MoveResponse(BaseModel):
    player_move: str
    bot_move: str | None
    bot_source: str | None = None
    bot_confidence: float | None = None


class GameStateResponse(BaseModel):
    game_id: str
    player_color: Color
    bot_color: Color
    bot_mode: BotMode
    bot_level: int
    fen: str
    moves: list[str]
    san_moves: list[str]
    last_move: str | None
    last_move_san: str | None
    status: str
    result: str | None
    termination: str | None
    winner: Color | None
    turn: Color
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    checked_king_square: str | None
    legal_moves: list[str]


class PgnResponse(BaseModel):
    game_id: str
    pgn: str


class RecommendationResponse(BaseModel):
    game_id: str
    mode: BotMode
    source: str
    recommended_move: str | None
    confidence: float | None


class BotHealthResponse(BaseModel):
    engine_available: bool
    ml_model_loaded: bool
    ml_confidence_threshold: float
    engine_path_configured: str | None
    ml_model_path_configured: str | None
