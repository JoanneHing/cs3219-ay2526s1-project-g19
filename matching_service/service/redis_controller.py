import asyncio
import json
import logging
import os
from dotenv import load_dotenv
import redis.asyncio as redis
from constants.matching import MatchingCriteriaEnum
from uuid import UUID
from fastapi import HTTPException, status
import time
from datetime import datetime
from constants.matching import MatchingCriteriaEnum, EXPIRATION_DURATION
from schemas.matching import MatchedCriteriaSchema, MatchingCriteriaSchema
from service.websocket import websocket_service


load_dotenv()
logger = logging.getLogger(__name__)


class RedisController:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
            db=0,
            decode_responses=True
        )
        self.general_queue_key="gen_queue:"
        self.pubsub = self.redis.pubsub()
        self.websocket_service = websocket_service

        ## Add operations

    async def add_to_queue(
        self,
        user_id: UUID,
        criteria: MatchingCriteriaSchema
    ):
        # add to general queue with timestamp for fifo deconflict
        await self.add_to_general_queue(user_id=user_id)
        await self.store_user_criteria_map(
            user_id=user_id,
            topics=criteria.topics,
            difficulty=criteria.difficulty
        )
        await self.add_to_criteria_set(
            criteria=MatchingCriteriaEnum.TOPIC,
            keys=criteria.topics,
            user_id=user_id
        )
        await self.add_to_criteria_set(
            criteria=MatchingCriteriaEnum.DIFFICULTY,
            keys=criteria.difficulty,
            user_id=user_id
        )
        await self.set_expiry(user_id=user_id)

    async def find_match(self, user_id: UUID) -> None:
        # store all criteria internal unions
        await self.store_union_set(criteria=MatchingCriteriaEnum.TOPIC, user_id=user_id)
        await self.store_union_set(criteria=MatchingCriteriaEnum.DIFFICULTY, user_id=user_id)
        # get intersection of criteria internal unions
        await self.store_inter_set(user_id=user_id)
        # deconflict with joined time
        matched_user_id = await self.get_earliest_user(user_id=user_id)
        if matched_user_id:
            matched_criteria = await self.get_matched_criteria(
                user_id=user_id,
                matched_user_id=matched_user_id
            )
            logger.info(f"User {user_id} matched with user {matched_user_id}")
            await self.websocket_service.send_match_success(
                user_a=user_id,
                user_b=matched_user_id,
                criteria=matched_criteria
            )
            await self.websocket_service.close_ws_connection(user_id=user_id)
            await self.websocket_service.close_ws_connection(user_id=matched_user_id)
            logger.info(f"Removing user {user_id} from queue")
            await self.remove_from_queue(user_id=user_id)
            logger.info(f"Removing user {matched_user_id} from queue")
            await self.remove_from_queue(user_id=matched_user_id)
        logger.info(f"{await self.debug_show()}")
        return

    async def remove_from_queue(self, user_id: UUID):
        await self.remove_from_general_queue(user_id=user_id)
        await self.remove_from_criteria_set(
            user_id=user_id,
            criteria=MatchingCriteriaEnum.TOPIC
        )
        await self.remove_from_criteria_set(
            user_id=user_id,
            criteria=MatchingCriteriaEnum.DIFFICULTY
        )
        # remove user criteria map
        await self.redis.delete(self._get_user_meta_key(user_id=user_id))
        return

    async def get_matched_criteria(
        self,
        user_id: UUID,
        matched_user_id: UUID
    ) -> MatchedCriteriaSchema:
        user_topic_criteria_set = set(await self.get_criteria_list(criteria=MatchingCriteriaEnum.TOPIC, user_id=user_id))
        matched_user_topic_criteria_set = set(await self.get_criteria_list(criteria=MatchingCriteriaEnum.TOPIC, user_id=matched_user_id))
        topic_set =  user_topic_criteria_set & matched_user_topic_criteria_set
        user_difficulty_criteria_set = set(await self.get_criteria_list(criteria=MatchingCriteriaEnum.DIFFICULTY, user_id=user_id))
        matched_user_difficulty_criteria_set = set(await self.get_criteria_list(criteria=MatchingCriteriaEnum.DIFFICULTY, user_id=matched_user_id))
        difficulty_set = user_difficulty_criteria_set & matched_user_difficulty_criteria_set
        return MatchedCriteriaSchema(
            topic=topic_set.pop(),
            difficulty=difficulty_set.pop()
        )

    async def start_expiry_listener(self):
        await self.pubsub.psubscribe("__keyevent@0__:expired")
        logger.info("Subscribed to key expiry events")

        try:
            while True:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=None
                )
                if message is not None:
                    expired_key = message["data"]
                    logger.info(f"Key expired: {expired_key}")
                    # Run expiry handler asynchronously so slow handlers don't block listening
                    asyncio.create_task(self.handle_expiry(expired_key))
                # Small sleep prevents a busy loop if Redis is quiet
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("Expiry event listener cancelled — shutting down")
        finally:
            await self.pubsub.close()
            await self.redis.close()

    async def handle_expiry(self, expiry_key: str):
        user_id = UUID(expiry_key.split(":")[1])
        logger.info(f"User {user_id} expired. Removing from queue...")
        await self.websocket_service.send_timeout(user_id=user_id)
        await self.websocket_service.close_ws_connection(user_id=user_id)
        await self.remove_from_queue(user_id=user_id)
        return

    ## Add operations

    async def add_to_general_queue(self, user_id: UUID) -> None:
        time_joined = time.time()
        logger.info(f"Adding user {user_id} to queue at {datetime.fromtimestamp(time_joined).strftime("%Y-%m-%d %H:%M:%S")}")
        added = await self.redis.zadd(self.general_queue_key, {str(user_id): time_joined}, nx=True)
        # check if user was already in queue
        if not added:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User {user_id} already in queue")
        return

    async def store_user_criteria_map(
        self,
        user_id: UUID,
        topics: list[str],
        difficulty: list[str]
    ):
        meta_key = self._get_user_meta_key(user_id=user_id)
        await self.redis.hset(
            name=meta_key,
            mapping={
                MatchingCriteriaEnum.TOPIC.value: json.dumps(topics),
                MatchingCriteriaEnum.DIFFICULTY.value: json.dumps(difficulty)
            },
        )
        return

    async def add_to_criteria_set(
        self,
        criteria: MatchingCriteriaEnum,
        keys: list[str],
        user_id: UUID
    ):
        redis_key_list = self._get_criteria_key_list(criteria=criteria, criteria_list=keys)
        for key in redis_key_list:
            await self.redis.sadd(key, str(user_id))
        return

    async def set_expiry(self, user_id: UUID):
        user_expiry_key = f"user_expiry:{user_id}"
        await self.redis.set(user_expiry_key, "1", ex=EXPIRATION_DURATION)
        return

    ## Query operations

    async def store_union_set(
        self,
        criteria: MatchingCriteriaEnum,
        user_id: UUID
    ) -> None:
        criteria_list = await self.get_criteria_list(criteria=criteria, user_id=user_id)
        redis_key_list = self._get_criteria_key_list(criteria=criteria, criteria_list=criteria_list)
        if redis_key_list:
            await self.redis.sunionstore(
                self._get_union_set_key(criteria=criteria, user_id=user_id),
                *redis_key_list
            )
        return

    async def store_inter_set(
        self,
        user_id: UUID
    ) -> None:
        intersection_key = self._get_intersection_key(user_id=user_id)
        keys = [
            self._get_union_set_key(criteria=MatchingCriteriaEnum.TOPIC, user_id=user_id),
            self._get_union_set_key(criteria=MatchingCriteriaEnum.DIFFICULTY, user_id=user_id)
        ]
        await self.redis.sinterstore(
            dest=intersection_key,
            keys=keys
        )
        # remove self
        await self.redis.srem(
            intersection_key,
            str(user_id)
        )
        # clean up union sets
        await self.redis.delete(*keys)
        return

    async def get_criteria_list(
        self,
        criteria: MatchingCriteriaEnum,
        user_id: UUID
    ) -> list[str]:
        meta_key = self._get_user_meta_key(user_id=user_id)
        return json.loads(await self.redis.hget(name=meta_key, key=criteria.value))

    async def get_earliest_user(self, user_id: UUID) -> UUID | None:
        intersection_key = self._get_intersection_key(user_id=user_id)
        inter_set_length = await self.redis.scard(intersection_key)
        if inter_set_length == 0:
            return None
        if inter_set_length == 1:
            return UUID(await self.redis.spop(intersection_key))
        temp_set_key = f"sortedset:match:user:{str(user_id)}"
        await self.redis.zinterstore(
            temp_set_key,
            {self.general_queue_key: 1, intersection_key: 0},  # keep sorted set scores (timestamp)
            aggregate="SUM"
        )
        assert await self.redis.zcard(temp_set_key) > 0
        earliest_user = await self.redis.zpopmin(temp_set_key, 1)[0][0]
        await self.redis.delete(intersection_key, temp_set_key)
        return UUID(earliest_user)

    ## Remove operations

    async def remove_from_general_queue(self, user_id: UUID) -> None:
        await self.redis.zrem(self.general_queue_key, str(user_id))
        return

    async def remove_from_criteria_set(
        self,
        user_id: UUID,
        criteria: MatchingCriteriaEnum
    ) -> None:
        criteria_list = await self.get_criteria_list(criteria=criteria, user_id=user_id)
        key_list = self._get_criteria_key_list(criteria=criteria, criteria_list=criteria_list)
        for key in key_list:
            await self.redis.srem(key, str(user_id))
        return

    ## Helper methods

    def _get_criteria_key_list(
        self,
        criteria: MatchingCriteriaEnum,
        criteria_list: list[str]
    ) -> list[str]:
        return [f"queue:{criteria.value}:{key}" for key in criteria_list]

    def _get_union_set_key(
        self,
        criteria: MatchingCriteriaEnum,
        user_id: UUID
    ) -> str:
        return f"set:union:{criteria.value}:user:{str(user_id)}"

    def _get_intersection_key(
        self,
        user_id: UUID
    ) -> str:
        return f"set:intersection:user:{str(user_id)}"

    def _get_user_meta_key(self, user_id: UUID) -> str:
        return f"user:{user_id}:meta"

    ## Debug

    async def debug_show(self) -> dict:
        r = self.redis
        result = {}

        keys = await r.keys('*')
        if not keys:
            return {"message": "Redis is empty."}

        for key in sorted(keys):
            key_type = await r.type(key)
            entry = {"type": key_type, "values": None}

            try:
                if key_type == 'set':
                    values = await r.smembers(key)
                    entry["values"] = sorted(values)

                elif key_type == 'zset':
                    values = await r.zrange(key, 0, -1, withscores=True)
                    entry["values"] = [{"member": member, "score": int(score)} for member, score in values]

                elif key_type == 'list':
                    values = await r.lrange(key, 0, -1)
                    entry["values"] = values

                elif key_type == 'hash':
                    values = await r.hgetall(key)
                    entry["values"] = values

                else:  # string
                    value = await r.get(key)
                    entry["values"] = value

            except Exception as e:
                entry["error"] = str(e)

            result[key] = entry

        return result

    async def clear_redis(self) -> None:
        await self.redis.flushdb()
        return


redis_controller = RedisController()
