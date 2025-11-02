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

    async def shutdown(self):
        await self.client.aclose()
        return

    def update_topics(self, topics: list[str]) -> None:
        logging.info(f"Topics retrieved from message: {topics}")
        self.topics = topics
        return

    def update_difficulties(self, difficulties: list[str]) -> None:
        logging.info(f"Difficulties retrieved from message: {difficulties}")
        self.difficulty = difficulties
        return

    def get_topics(self) -> list[str]:
        return self.topics

    def get_difficulty(self) -> list[str]:
        return self.difficulty


django_question_service = DjangoQuestionService()
