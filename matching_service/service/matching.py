import logging
from uuid import UUID
from schemas.matching import MatchingCriteriaSchema
from service.redis_controller import redis_controller

logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self):
        self.redis_controller = redis_controller

    async def match_user(
        self,
        user_id: UUID,
        criteria: MatchingCriteriaSchema,
    ) -> str:
        logger.info(f"Added user {user_id} to queue with criteria {criteria}")
        await self.redis_controller.add_to_queue(
            user_id=user_id,
            criteria=criteria
        )
        logger.info(f"{await self.redis_controller.debug_show()}")
        # find eligible matches
        await self.redis_controller.find_match(user_id=user_id)
        return f"User {user_id} joined queue"

    async def debug_show(self) -> dict:
        return await self.redis_controller.debug_show()

    async def clear_redis(self) -> None:
        await self.redis_controller.clear_redis()
        return


matching_service = MatchingService()
