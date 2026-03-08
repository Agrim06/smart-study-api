import redis 
import json
from app.schemas import StudyResponse

redis_client = redis.Redis(
    host = "localhost",
    port = 6379,
    decode_responses= True
)

CACHE_TTL = 3600

def get_cached_notes(key:str):
    cached = redis_client.get(key)

    if not cached:
        return None

    data = json.loads(cached)
    return StudyResponse(**data)

def set_cached_notes(key: str , value: StudyResponse):
    redis_client.setex(
        key,
        CACHE_TTL,
        value.model_dump_json()
    )