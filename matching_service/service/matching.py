import json
import logging
import os
from uuid import UUID
from dotenv import load_dotenv
from fastapi import HTTPException, status
import redis
import time
from datetime import datetime
from constants.matching import MatchingCriteriaEnum
from schemas.matching import MatchingCriteriaSchema
from service.redis_controller import redis_controller

load_dotenv()
logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self):
        self.redis_controller = redis_controller

    async def match_user(
        self,
        user_id: UUID,
        criteria: MatchingCriteriaSchema,
    ) -> UUID | None:
        logger.info(f"Matching user {user_id} with criteria {criteria}")
        self.redis_controller.add_to_queue(
            user_id=user_id,
            criteria=criteria
        )
        # logger.info(f"{self.redis_controller.debug_show()}")
        # find eligible matches
        matched_user_id = self.redis_controller.find_match(user_id=user_id)
        if matched_user_id:
            self.redis_controller.remove_from_queue(user_id=user_id)
            self.redis_controller.remove_from_queue(user_id=matched_user_id)
        # logger.info(f"{self.redis_controller.debug_show()}")
        return matched_user_id

    def debug_show(self) -> dict:
        return self.redis_controller.debug_show()

    def clear_redis(self) -> None:
        self.redis_controller.clear_redis()
        return


matching_service = MatchingService()
