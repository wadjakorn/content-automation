from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class LLMClient(Protocol):
    """Two call sites only: generate (free text) and judge (validated verdict).

    Local MLX/Ollama impl slots behind this at phase 2 without touching callers.
    """

    def generate(self, prompt: str) -> str: ...

    def judge(self, prompt: str, schema: type[M]) -> M: ...
