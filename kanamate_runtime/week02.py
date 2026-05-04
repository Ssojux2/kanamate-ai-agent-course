"""Week 2 structured-output schemas and agent factory."""

from __future__ import annotations

from typing import Literal

from langchain.agents import create_agent
from pydantic import BaseModel, Field

from kanamate_runtime.common import make_model


class ScheduleCreate(BaseModel):
    title: str = Field(description="일정 제목")
    date: str = Field(description="YYYY-MM-DD")
    start_time: str = Field(description="HH:MM")
    attendees: list[str] = Field(default_factory=list)


class TodoCreate(BaseModel):
    title: str
    due_date: str | None = Field(default=None, description="YYYY-MM-DD")
    priority: Literal["low", "medium", "high"] = "medium"


class ReminderCreate(BaseModel):
    title: str = Field(description="알림 제목")
    related_event: str | None = Field(default=None, description="알림이 연결된 일정이나 사건")
    offset_minutes: int = Field(description="기준 사건 몇 분 전에 알릴지")


class PracticeExtractionResult(BaseModel):
    kind: Literal["schedule", "todo", "reminder", "unknown"]
    schedule: ScheduleCreate | None = None
    todo: TodoCreate | None = None
    reminder: ReminderCreate | None = None
    question: str | None = None


def build_practice_extract_agent(max_tokens: int = 500):
    return create_agent(
        model=make_model(max_tokens),
        tools=[],
        response_format=PracticeExtractionResult,
        system_prompt=(
            "오늘은 2026-04-23이다. 사용자 요청을 schedule, todo, reminder, unknown 중 하나로 구조화한다. "
            "'N분 전에 알려줘' 같은 요청은 reminder로 분류하고 offset_minutes에는 N을 정수로 넣는다."
        ),
    )

