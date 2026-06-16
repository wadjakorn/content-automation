from __future__ import annotations

from typing import TypeVar

import anthropic
from anthropic.types import ToolParam
from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class ClaudeClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text"
        )

    def judge(self, prompt: str, schema: type[M]) -> M:
        tool: ToolParam = {
            "name": "verdict",
            "description": "Return the structured verdict.",
            "input_schema": schema.model_json_schema(),
        }
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            tools=[tool],
            tool_choice={"type": "tool", "name": "verdict"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in resp.content:
            if getattr(block, "type", "") == "tool_use":
                return schema.model_validate(block.input)  # type: ignore[union-attr]
        raise ValueError("no tool_use block in Claude response")
