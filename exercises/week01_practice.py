"""Week 1 practice: schedule creation plus list lookup."""

from __future__ import annotations

import json
from typing import Any

from kanamate_runtime.common import extract_tool_trace, final_text
from kanamate_runtime.week01 import build_nana_agent


def run_student_schedule_request(request: str, agent: Any | None = None) -> dict[str, Any]:
    """Run Nana with one schedule request, then list schedules for the UI."""
    nana_agent = agent or build_nana_agent()

    # TODO 1: nana_agent.invoke로 request를 실행한다.
    # 모범 답안 1(강의자료 테스트용)
    result = nana_agent.invoke({"messages": [{"role": "user", "content": request}]})

    # TODO 2: trace에서 create_schedule tool_result를 찾아 JSON으로 읽는다.
    # 모범 답안 2(강의자료 테스트용)
    trace = extract_tool_trace(result)
    created_schedule = None
    for event in trace:
        if event.get("event") == "tool_result" and event.get("tool_name") == "create_schedule":
            created_schedule = json.loads(event["content"])["schedule"]

    # TODO 3: 생성 직후 list_schedules도 실행해 UI에 띄울 목록을 만든다.
    # 모범 답안 3(강의자료 테스트용)
    list_result = nana_agent.invoke({"messages": [{"role": "user", "content": "현재 일정 목록 보여줘"}]})
    list_trace = extract_tool_trace(list_result)
    schedule_snapshot = []
    for event in list_trace:
        if event.get("event") == "tool_result" and event.get("tool_name") == "list_schedules":
            schedule_snapshot = json.loads(event["content"])["schedules"]

    return {
        "answer": final_text(result),
        "list_answer": final_text(list_result),
        "trace": trace,
        "list_trace": list_trace,
        "created_schedule": created_schedule,
        "schedules": schedule_snapshot,
    }

