"""Test helpers for fake LangChain-style agent results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeMessage:
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    type: str | None = None
    name: str | None = None


class SequenceAgent:
    def __init__(self, results: list[dict[str, Any]]):
        self.results = list(results)
        self.requests: list[dict[str, Any]] = []

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.requests.append(payload)
        if not self.results:
            raise AssertionError("No fake agent result left")
        return self.results.pop(0)


def agent_result(tool_name: str, payload: dict[str, Any], answer: str = "done") -> dict[str, Any]:
    return {
        "messages": [
            FakeMessage(tool_calls=[{"name": tool_name, "args": {}}]),
            FakeMessage(content=json.dumps(payload, ensure_ascii=False), type="tool", name=tool_name),
            FakeMessage(content=answer),
        ]
    }

