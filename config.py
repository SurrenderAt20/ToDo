import os
from pathlib import Path

from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).parent / ".env"


def load_config() -> None:
    load_dotenv(ENV_PATH)


def get_api_key() -> str:
    return os.getenv("CLAUDE_API_KEY", "")


def save_api_key(key: str) -> None:
    ENV_PATH.touch(exist_ok=True)
    set_key(str(ENV_PATH), "CLAUDE_API_KEY", key)
    os.environ["CLAUDE_API_KEY"] = key
