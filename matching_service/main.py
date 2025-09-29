import json
import logging.config
import os
from fastapi import FastAPI
import uvicorn
import logging

with open("log_config.json", "r") as f:
    config = json.load(f)
logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def root():
    return "Matching Service"


if __name__=="__main__":
    logger.info("Starting matching service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENV", "prd") == "dev"
    )
    logger.info("Stopping matching service...")
