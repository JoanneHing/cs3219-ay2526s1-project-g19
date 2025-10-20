import json
import logging
import logging.config
import os
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config import settings
from middleware.fixed_prefix import FixedPrefixMiddleware


with open("log_config.json", "r") as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)

SERVICE_PREFIX = os.getenv("SERVICE_PREFIX", "/matching-service-api")
if SERVICE_PREFIX and not SERVICE_PREFIX.startswith("/"):
    SERVICE_PREFIX = "/" + SERVICE_PREFIX
SERVICE_PREFIX = SERVICE_PREFIX.rstrip("/")

router = APIRouter(
    prefix="/api",
    redirect_slashes=False
)
app = FastAPI(redirect_slashes=False)
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if SERVICE_PREFIX:
    app.add_middleware(FixedPrefixMiddleware, prefix=SERVICE_PREFIX)


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
