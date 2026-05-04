"""Week 5 practice: supervisor routing harness."""

from __future__ import annotations

from typing import Any

from kanamate_runtime.common import extract_tool_trace, final_text
from kanamate_runtime.week05 import (
    build_supervisor,
    delegated_agent_from_trace,
    delegated_payload_from_trace,
)

golden_cases = [
    {
        "name": "personal_schedule",
        "request": "내일 9시에 민수와 1:1 일정 잡아줘",
        "member_replies": "",
        "expected_agent": "nana",
        "expected_inner_tool": "personal_create_schedule",
    },
    {
        "name": "group_slot",
        "request": "팀 회의 시간을 조율해줘",
        "member_replies": "민수: 2026-04-25 15:00 가능\n지아: 2026-04-25 15:00 가능",
        "expected_agent": "kana",
        "expected_inner_tool": "group_confirm_slot",
    },
]


def run_supervisor_case(
    case: dict[str, Any],
    supervisor_agent: Any | None = None,
) -> dict[str, Any]:
    """Run one routing golden case and return a compact report."""
    # TODO 1: member_replies가 있으면 요청과 멤버 응답을 함께 보낸다.
    # 모범 답안 1(강의자료 테스트용)
    content = case["request"]
    if case.get("member_replies"):
        content = f"요청: {case['request']}\n멤버 응답:\n{case['member_replies']}"

    # TODO 2: supervisor trace에서 선택된 agent를 읽는다.
    # 모범 답안 2(강의자료 테스트용)
    supervisor = supervisor_agent or build_supervisor()
    result = supervisor.invoke({"messages": [{"role": "user", "content": content}]})
    selected_agent = delegated_agent_from_trace(result)
    delegate_payload = delegated_payload_from_trace(result)

    # TODO 3: sub-agent 내부 trace의 tool 이름 목록을 만든다.
    # 모범 답안 3(강의자료 테스트용)
    inner_tool_names = [
        event["tool_name"]
        for event in delegate_payload.get("trace", [])
        if event.get("event") == "tool_call"
    ]

    return {
        "name": case["name"],
        "expected_agent": case["expected_agent"],
        "selected_agent": selected_agent,
        "expected_inner_tool": case["expected_inner_tool"],
        "inner_tool_names": inner_tool_names,
        "answer": final_text(result),
        "trace": extract_tool_trace(result),
        "delegate_payload": delegate_payload,
    }

