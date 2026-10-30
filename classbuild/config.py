import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_TIMEOUT_SECONDS = 60

@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    request_timeout_seconds: int



def get_settings() -> Settings:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    timeout_value = os.getenv(
        "GROQ_TIMEOUT_SECONDS",
        str(DEFAULT_TIMEOUT_SECONDS)
    ).strip()

    try:
        timeout = int(timeout_value)
    except ValueError:
        timeout = DEFAULT_TIMEOUT_SECONDS

    return Settings(
        groq_api_key=api_key,
        groq_model=model,
        request_timeout_seconds=timeout,
    )
