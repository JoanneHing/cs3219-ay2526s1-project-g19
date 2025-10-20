import json
import logging
import logging.config
from fastapi import APIRouter, FastAPI
import uvicorn
from config import settings


with open("log_config.json", "r") as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    redirect_slashes=False
)
app = FastAPI(redirect_slashes=False)

@router.get("/test")
async def test(msg: str):
    logger.info(settings.pg_url)
    return f"hi {msg}"

app.include_router(router=router)

if __name__=="__main__":
    logger.info("Starting session service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "dev"
    )
    logger.info("Stopping session service...")
