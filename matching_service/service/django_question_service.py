import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)


class DjangoQuestionService:
    def __init__(self):
        self.topics: list[str] | None = None
        self.difficulty: list[str] | None = None
        self.languages: list[str] | None = None

    async def setup(self):
        async with httpx.AsyncClient() as client:
            # get topic list
            resp = await client.get(f"{settings.question_service_url}/api/topics")
            data: dict = resp.json()
            self.topics = data.get("topics") or []
            logger.info(f"Topic list retrieved from question service: {self.topics}")
            # get difficulty list
            # resp = await client.get(f"{settings.question_service_url}/api/difficulty")
            # data: dict = resp.json()
            # self.difficulty = data.get("difficulty") or []
            # dummy data
            self.difficulty = ["Easy", "Medium", "Hard"]
            logger.info(f"Difficulty list retrieved from question service: {self.difficulty}")
            # resp = await client.get(f"{settings.question_service_url}/api/languages")
            # data: dict = resp.json()
            # self.topics = data.get("topics") or []
            # dummy data
            self.languages = ["python", "java", "c", "javascript"]
            logger.info(f"Language list retrieved from question service: {self.languages}")

    def get_topics(self):
        assert self.topics != None
        return self.topics

    def get_difficulty(self):
        assert self.difficulty != None
        return self.difficulty

    def get_languages(self):
        assert self.languages != None
        return self.languages


django_question_service = DjangoQuestionService()
