import os

from dotenv import load_dotenv

load_dotenv()


def get_env_var(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Environment variable {key} not set.")
    return value
