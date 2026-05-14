from functools import lru_cache
from openai import AsyncOpenAI
import instructor
from core.config import get_settings

@lru_cache()
def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key)

@lru_cache()
def get_instructor_client():
    return instructor.from_openai(get_openai_client())
