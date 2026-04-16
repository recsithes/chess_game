from fastapi import APIRouter, Request

from app.models.schemas import BotHealthResponse

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/bot-health", response_model=BotHealthResponse)
def bot_health(request: Request) -> BotHealthResponse:
    bot_service = request.app.state.bot_service
    return BotHealthResponse(**bot_service.health())
