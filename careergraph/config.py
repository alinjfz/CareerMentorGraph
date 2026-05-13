"""Configuration helpers for local demo and optional integrations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    username: str
    password: str
    database: str | None = None


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model: str


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def bool_from_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_neo4j_config() -> Neo4jConfig | None:
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE") or None

    if not uri or not username or not password:
        return None

    return Neo4jConfig(uri=uri, username=username, password=password, database=database)


def get_llm_config(model_override: str | None = None) -> LLMConfig | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    return LLMConfig(
        api_key=api_key,
        model=model_override or os.getenv("OPENAI_MODEL", "gpt-5.2"),
    )
