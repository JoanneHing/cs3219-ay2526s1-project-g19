import asyncio
from contextlib import asynccontextmanager
import json
import logging.config
from pathlib import Path
from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
import uvicorn
import logging
from service.django_question_service import django_question_service
from schemas.matching import VALID_LANGUAGE_LIST, MatchUserRequestSchema
from service.redis_controller import redis_controller
from service.matching import matching_service
from service.websocket import websocket_service
from uuid import UUID
from config import settings

with open("log_config.json", "r") as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Running events on start...")
    await django_question_service.setup()
    expiry_event_listener = asyncio.create_task(redis_controller.start_expiry_listener())  # run listener concurrently
    yield
    logger.info("Cleaning up events on shutdown...")
    expiry_event_listener.cancel()


router = APIRouter(
    prefix="/api"
)
app = FastAPI(lifespan=lifespan)


@app.get("/test_ws")
async def get():
    html_file = Path("ws_test/ws_test_screen.html")
    html_content = html_file.read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)


@router.post("/match", status_code=status.HTTP_202_ACCEPTED, responses={
    202: {"description": "Accepted"},
    409: {"description": "User already in queue"}
})
async def match_users(data: MatchUserRequestSchema):
    # check if ws connection is set up
    if not websocket_service.check_ws_connection(user_id=data.user_id):
        return "Error: connect to websocket first"
    res = await matching_service.match_user(
        user_id=data.user_id,
        criteria=data.criteria
    )
    return res


@router.post("/match/cancel")
async def cancel_matching(user_id: UUID):
    await websocket_service.close_ws_connection(user_id=user_id)
    return f"Matching for user {user_id} cancelled"


@router.get("/languages", response_model=list[str])
async def get_languages():
    return VALID_LANGUAGE_LIST


@router.get("/debug/show")
async def debug_show():
    return await matching_service.debug_show()


@router.websocket("/ws")
async def websocket_endpoint(user_id: UUID, websocket: WebSocket):
    logger.info(f"Connecting ws for {user_id}")
    websocket_service.record_ws_connection(user_id=user_id, websocket=websocket)
    await websocket.accept()
    try:
        while True:
            try:
                await websocket.receive_text()
            except (WebSocketDisconnect, RuntimeError):
                break
    finally:
        await redis_controller.remove_from_queue(user_id=user_id)
        await websocket_service.close_ws_connection(user_id=user_id)


@router.post("/flush")
async def flush():
    return await matching_service.clear_redis()


app.include_router(router)


if __name__=="__main__":
    logger.info("Starting matching service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "dev"
    )
    logger.info("Stopping matching service...")
