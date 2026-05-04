"""Week 1 KanaMate schedule tools."""

from __future__ import annotations

import json
from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool

from kanamate_runtime.common import make_model

schedules: list[dict[str, Any]] = []


def reset_schedules() -> None:
    schedules.clear()


@tool("create_schedule", description="개인 일정을 생성한다. date는 YYYY-MM-DD, start_time은 HH:MM 형식이다.")
def create_schedule(
    title: str,
    date: str,
    start_time: str,
    attendees: list[str] | None = None,
) -> str:
    """Create a personal schedule."""
    schedule = {
        "id": f"schedule-{len(schedules) + 1}",
        "title": title,
        "date": date,
        "start_time": start_time,
        "attendees": attendees or [],
    }
    schedules.append(schedule)
    return json.dumps({"ok": True, "schedule": schedule}, ensure_ascii=False)


@tool("list_schedules", description="현재 생성된 개인 일정 목록을 조회한다.")
def list_schedules() -> str:
    """List personal schedules."""
    return json.dumps({"ok": True, "schedules": schedules}, ensure_ascii=False)


def build_nana_agent(max_tokens: int = 500):
    return create_agent(
        model=make_model(max_tokens),
        tools=[create_schedule, list_schedules],
        system_prompt=(
            "너는 개인 일정 메이트 나나다. 오늘은 2026-04-23이다. "
            "상대 날짜는 이 날짜 기준으로 YYYY-MM-DD로 바꾼다. "
            "일정 생성이나 조회가 필요하면 반드시 알맞은 도구를 호출한 뒤 짧게 답한다."
        ),
    )

