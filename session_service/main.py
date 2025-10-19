import logging
from fastapi import APIRouter, FastAPI
import uvicorn
from config import settings


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    redirect_slashes=False
)
app = FastAPI(redirect_slashes=False)

@router.get("/test")
async def test(msg: str):
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
