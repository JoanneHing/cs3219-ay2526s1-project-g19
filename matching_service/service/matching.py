import logging
import os
from uuid import UUID, uuid4
from dotenv import load_dotenv
import redis
import time

from constants.matching import MatchingCriteriaEnum

load_dotenv()
logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        self.matching_redis = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
            db=0,
            decode_responses=True
        )
        self.queued_str = "queued"

    def match_user(
        self,
        user_id: UUID,
        topics: list[str],
        difficulty: list = [],
        primary_lang: None = None,
        secondary_lang: list = [],
        proficiency: int = 0
    ) -> list[UUID]:
        logger.info(f"Adding {user_id} to matching queue")
        time_joined = time.time()
        for key in self._get_redis_key(MatchingCriteriaEnum.TOPIC, keys=topics):
            self.matching_redis.zadd(key, {str(user_id): time_joined})
        self._add_to_queued_status(user_id=user_id)
        return self._show_queue(topics=topics)

    def _add_to_queued_status(self, user_id: UUID):
        self.matching_redis.sadd(self.queued_str, str(user_id))

    def _show_queue(self, topics: list[str] = []) -> list[UUID]:
        res = []
        for key in self._get_redis_key(criteria=MatchingCriteriaEnum.TOPIC, keys=topics):
            curr = self.matching_redis.zrange(key, 0, -1)
            res += [UUID(id) for id in curr]
        return res

    def _get_redis_key(
        self,
        criteria: MatchingCriteriaEnum,
        keys: list[str]
    ) -> list[str]:
        return [f"queue:{criteria.value}:{key}" for key in keys]

    def debug_show(self) -> str:
        r = self.matching_redis
        output = []

        keys = r.keys('*')
        if not keys:
            return "Redis is empty."

        for key in keys:
            key_type = r.type(key)
            output.append(f"Key: {key} (Type: {key_type})")

            try:
                if key_type == 'set':
                    values = r.smembers(key)
                    output.append(f"  Values: {{ {', '.join(values)} }}")
                elif key_type == 'zset':
                    values = r.zrange(key, 0, -1, withscores=True)
                    values_str = ', '.join(f"{v}:{int(score)}" for v, score in values)
                    output.append(f"  Values: {{ {values_str} }}")
                elif key_type == 'list':
                    values = r.lrange(key, 0, -1)
                    output.append(f"  Values: [ {', '.join(values)} ]")
                elif key_type == 'hash':
                    values = r.hgetall(key)
                    values_str = ', '.join(f"{k}:{v}" for k, v in values.items())
                    output.append(f"  Values: {{ {values_str} }}")
                else:  # string
                    value = r.get(key)
                    output.append(f"  Value: {value}")
            except Exception as e:
                output.append(f"  Error reading key: {e}")

        return '\n'.join(output)


matching_service = MatchingService()

if __name__=="__main__":
    pass
