import logging
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

    async def shutdown(self):
        self.client.aclose()
        return

    async def get_topics(self) -> list[str]:
        resp = await self.client.get(f"{settings.question_service_url}{self.get_topics_path}")
        data: dict = resp.json()
        topics = data.get("topics") or []
        logger.info(f"Topic list retrieved from question service: {topics}")
        return topics

    async def get_difficulty(self) -> list[str]:
        # dummy data
        return ["Easy", "Medium", "Hard"]
        resp = await self.client.get(f"{settings.question_service_url}{self.get_difficulty_path}")
        data: dict = resp.json()
        difficulty = data.get("difficulty") or []
        logger.info(f"Difficulty list retrieved from question service: {difficulty}")
        return difficulty


django_question_service = DjangoQuestionService()
