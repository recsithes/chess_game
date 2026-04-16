import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.game import router as game_router
from app.api.system import router as system_router
from app.db import SessionLocal, init_db
from app.services.bot_service import BotService
from app.services.chess_service import ChessService


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine_path = os.getenv("STOCKFISH_PATH")
    model_path = os.getenv("ML_MODEL_PATH")
    try:
        ml_confidence_threshold = float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.2"))
    except ValueError:
        ml_confidence_threshold = 0.2

    init_db()
    app.state.chess_service = ChessService(session_factory=SessionLocal)
    app.state.bot_service = BotService(
        engine_path=engine_path,
        model_path=model_path,
        ml_confidence_threshold=ml_confidence_threshold,
    )
    yield


app = FastAPI(title="Chess ML Backend", version="0.1.0", lifespan=lifespan)

cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080",
)
allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
allow_all_origins = "*" in allowed_origins
local_origin_regex = None if allow_all_origins else r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allowed_origins,
    allow_origin_regex=local_origin_regex,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(system_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
