import json
import logging.config
import os
from fastapi import APIRouter, FastAPI
import uvicorn
import logging
from schemas.matching import MatchUserRequestSchema
from service.matching import matching_service
from uuid import UUID

with open("log_config.json", "r") as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api"
)
app = FastAPI()


@router.post("/match")
def match_users(data: MatchUserRequestSchema):
    res = matching_service.match_user(
        user_id=data.user_id,
        topics=data.topics
    )
    return res


@router.get("/debug/show")
def debug_show():
    return matching_service.debug_show()


app.include_router(router)

if __name__=="__main__":
    logger.info("Starting matching service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENV", "prd") == "dev"
    )
    logger.info("Stopping matching service...")
