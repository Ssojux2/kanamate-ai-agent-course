"""Week 5 sub-agent runtime."""

from __future__ import annotations

import json
from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool

from kanamate_runtime.common import extract_tool_trace, final_text, make_model


@tool("personal_create_schedule", description="나나가 개인 일정 초안을 만든다.")
def personal_create_schedule(title: str, date: str, start_time: str) -> str:
    """Create a personal schedule."""
    return json.dumps(
        {"ok": True, "schedule": {"title": title, "date": date, "start_time": start_time}},
        ensure_ascii=False,
    )


@tool("group_confirm_slot", description="카나가 멤버 응답을 근거로 그룹 시간을 확정한다.")
def group_confirm_slot(topic: str, selected_slot: str, members: list[str], reason: str) -> str:
    """Confirm a group slot from member replies."""
    return json.dumps(
        {
            "ok": True,
            "topic": topic,
            "selected_slot": selected_slot,
            "members": members,
            "reason": reason,
        },
        ensure_ascii=False,
    )


def build_nana_agent(max_tokens: int = 600):
    return create_agent(
        model=make_model(max_tokens),
        tools=[personal_create_schedule],
        system_prompt=(
            "너는 개인 메이트 나나다. 오늘은 2026-04-23이다. "
            "상대 날짜는 이 날짜 기준으로 YYYY-MM-DD로 바꾼다. "
            "개인 일정 요청은 personal_create_schedule 도구를 호출한다."
        ),
    )


def build_kana_agent(max_tokens: int = 700):
    return create_agent(
        model=make_model(max_tokens),
        tools=[group_confirm_slot],
        system_prompt="너는 그룹 메이트 카나다. 멤버 응답에서 모두 가능한 시간을 찾으면 group_confirm_slot 도구를 호출한다.",
    )


@tool("nana_agent", description="개인 일정 요청을 나나 sub-agent에게 위임한다.")
def delegate_to_nana(request: str) -> str:
    """Delegate a personal request to Nana sub-agent."""
    agent_result = build_nana_agent().invoke({"messages": [{"role": "user", "content": request}]})
    return json.dumps(
        {"agent": "nana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


@tool("kana_agent", description="그룹 일정 조율 요청과 멤버 응답을 카나 sub-agent에게 위임한다.")
def delegate_to_kana(request: str, member_replies: str) -> str:
    """Delegate a group coordination request to Kana sub-agent."""
    message = f"요청: {request}\n멤버 응답:\n{member_replies}"
    agent_result = build_kana_agent().invoke({"messages": [{"role": "user", "content": message}]})
    return json.dumps(
        {"agent": "kana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


def build_supervisor(max_tokens: int = 900):
    return create_agent(
        model=make_model(max_tokens),
        tools=[delegate_to_nana, delegate_to_kana],
        system_prompt=(
            "너는 카나메이트 supervisor다. 개인 일정 요청은 nana_agent tool을 호출하고, "
            "그룹 일정 조율 요청은 kana_agent tool을 호출한다. 직접 처리하지 말고 반드시 "
            "적절한 sub-agent tool을 호출한 뒤 그 결과를 학생에게 요약한다."
        ),
    )


def delegated_agent_from_trace(agent_result: dict[str, Any]) -> str:
    for event in extract_tool_trace(agent_result):
        if event.get("event") == "tool_call" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return event["tool_name"].replace("_agent", "")
    return "unknown"


def delegated_payload_from_trace(agent_result: dict[str, Any]) -> dict[str, Any]:
    for event in extract_tool_trace(agent_result):
        if event.get("event") == "tool_result" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return json.loads(event["content"])
    return {}

