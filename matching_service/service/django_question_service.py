from functools import wraps
import logging
from fastapi import HTTPException, status
import httpx
from config import settings

logger = logging.getLogger(__name__)


class DjangoQuestionService:
    def __init__(self):
        self.topics: list[str] | None = None
        self.difficulty: list[str] | None = None
        self.client = httpx.AsyncClient()
        self.get_topics_path = "/api/topics"
        self.get_difficulty_path = "/api/difficulty"
        self._fallback_to_http = True  # Flag to fallback to HTTP if Kafka data not available

    async def shutdown(self):
        await self.client.aclose()
        return

    def safe_http_call(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                logger.error(f"Cannot connect to question service: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Cannot connect to question service"
                )
            except httpx.HTTPStatusError as e:
                logger.error(f"Question service returned HTTP error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Question service returned error"
                )
            except (httpx.DecodingError, ValueError) as e:
                logger.error(f"Invalid JSON from question service: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Invalid response from question service"
                )
        return wrapper

    @safe_http_call
    async def get_topics(self) -> list[str]:
        # Try to use cached data first (from Kafka)
        if self.topics is not None:
            logger.info(f"Using cached topics: {self.topics}")
            return self.topics
        
        # Fallback to HTTP if no cached data
        if self._fallback_to_http:
            logger.info("No cached topics available, fetching from HTTP endpoint")
            resp = await self.client.get(f"{settings.question_service_url}{self.get_topics_path}")
            data: dict = resp.json()
            topics = data.get("topics") or []
            logger.info(f"Topic list retrieved from question service: {topics}")
            return topics
        
        # If no fallback and no cached data, return empty list
        logger.warning("No topics available from cache or HTTP")
        return []

    @safe_http_call
    async def get_difficulty(self) -> list[str]:
        # Try to use cached data first (from Kafka)
        if self.difficulty is not None:
            logger.info(f"Using cached difficulties: {self.difficulty}")
            return self.difficulty
        
        # Fallback to HTTP if no cached data
        if self._fallback_to_http:
            logger.info("No cached difficulties available, fetching from HTTP endpoint")
            resp = await self.client.get(f"{settings.question_service_url}{self.get_difficulty_path}")
            data: dict = resp.json()
            difficulty = data.get("difficulties") or []
            logger.info(f"Difficulty list retrieved from question service: {difficulty}")
            return difficulty
        
        # If no fallback and no cached data, return default difficulties
        logger.warning("No difficulties available from cache or HTTP, using defaults")
        return ["easy", "medium", "hard"]


django_question_service = DjangoQuestionService()
