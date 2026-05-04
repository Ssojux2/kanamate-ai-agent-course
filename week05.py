"""Week 5 KanaMate assignment and Gradio UI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load the repo-root .env next to this weekly script."""
    load_dotenv(ENV_PATH, override=False)


def openai_model_name() -> str:
    load_project_env()
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def openai_embedding_model_name() -> str:
    load_project_env()
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)


def require_openai_api_key() -> str:
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    return api_key


def make_model(max_tokens: int = 500) -> ChatOpenAI:
    require_openai_api_key()
    return ChatOpenAI(
        model=openai_model_name(),
        temperature=0,
        max_completion_tokens=max_tokens,
    )


def show_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def final_text(agent_result: dict[str, Any]) -> str:
    return agent_result["messages"][-1].content


def extract_tool_trace(agent_result: dict[str, Any]) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for message in agent_result.get("messages", []):
        for call in getattr(message, "tool_calls", []) or []:
            trace.append(
                {
                    "event": "tool_call",
                    "tool_name": call.get("name"),
                    "arguments": call.get("args", {}),
                }
            )
        if getattr(message, "type", None) == "tool":
            trace.append(
                {
                    "event": "tool_result",
                    "tool_name": getattr(message, "name", None),
                    "content": message.content,
                }
            )
    return trace

# ---------------------------------------------------------------------------
# Week 5-6. Sub-agent tools and harnesses
# ---------------------------------------------------------------------------


def _personal_create_schedule(title: str, date: str, start_time: str) -> str:
    """Create a personal schedule."""
    return json.dumps(
        {"ok": True, "schedule": {"title": title, "date": date, "start_time": start_time}},
        ensure_ascii=False,
    )


def _group_confirm_slot(topic: str, selected_slot: str, members: list[str], reason: str) -> str:
    """Confirm a group schedule slot."""
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


def _memory_save(title: str, content: str) -> str:
    """Save a user memory."""
    return json.dumps({"ok": True, "memory": {"title": title, "content": content}}, ensure_ascii=False)


personal_create_schedule_tool = tool(
    "personal_create_schedule",
    description="개인 일정을 생성한다.",
)(_personal_create_schedule)
group_confirm_slot_tool = tool(
    "group_confirm_slot",
    description="그룹 일정 시간을 확정한다.",
)(_group_confirm_slot)
memory_save_tool = tool(
    "memory_save",
    description="사용자 메모를 저장한다.",
)(_memory_save)

def build_week05_nana_agent(max_tokens: int = 600):
    return create_agent(
        model=make_model(max_tokens),
        tools=[personal_create_schedule_tool],
        system_prompt=(
            "너는 개인 메이트 나나다. 오늘은 2026-04-23이다. "
            "상대 날짜는 이 날짜 기준으로 YYYY-MM-DD로 바꾼다. "
            "개인 일정 요청은 personal_create_schedule 도구를 호출한다."
        ),
    )


def build_week05_kana_agent(max_tokens: int = 700):
    return create_agent(
        model=make_model(max_tokens),
        tools=[group_confirm_slot_tool],
        system_prompt="너는 그룹 메이트 카나다. 멤버 응답에서 모두 가능한 시간을 찾으면 group_confirm_slot 도구를 호출한다.",
    )


def _week05_delegate_to_nana(request: str) -> str:
    """Delegate a personal request to Nana sub-agent."""
    agent_result = build_week05_nana_agent().invoke({"messages": [{"role": "user", "content": request}]})
    return json.dumps(
        {"agent": "nana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


def _week05_delegate_to_kana(request: str, member_replies: str) -> str:
    """Delegate a group coordination request to Kana sub-agent."""
    message = f"요청: {request}\n멤버 응답:\n{member_replies}"
    agent_result = build_week05_kana_agent().invoke({"messages": [{"role": "user", "content": message}]})
    return json.dumps(
        {"agent": "kana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


week05_delegate_to_nana = tool(
    "nana_agent",
    description="개인 일정 요청을 나나 sub-agent에게 위임한다.",
)(_week05_delegate_to_nana)
week05_delegate_to_kana = tool(
    "kana_agent",
    description="그룹 일정 조율 요청과 멤버 응답을 카나 sub-agent에게 위임한다.",
)(_week05_delegate_to_kana)


def build_week05_supervisor(max_tokens: int = 900):
    return create_agent(
        model=make_model(max_tokens),
        tools=[week05_delegate_to_nana, week05_delegate_to_kana],
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


def run_supervisor_case(case: dict[str, Any], supervisor_agent: Any | None = None) -> dict[str, Any]:
    """Run one routing golden case and return a compact report."""
    # TODO 1: member_replies가 있으면 요청과 멤버 응답을 함께 보낸다.
    # 모범 답안 1(강의자료 테스트용)
    content = case["request"]
    if case.get("member_replies"):
        content = f"요청: {case['request']}\n멤버 응답:\n{case['member_replies']}"

    # TODO 2: supervisor trace에서 선택된 agent를 읽는다.
    # 모범 답안 2(강의자료 테스트용)
    supervisor = supervisor_agent or build_week05_supervisor()
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


def run_ui(request: str, member_replies: str):
    try:
        expected_agent = "kana" if member_replies.strip() else "nana"
        expected_inner_tool = "group_confirm_slot" if expected_agent == "kana" else "personal_create_schedule"
        report = run_supervisor_case(
            {
                "name": "ui_case",
                "request": request,
                "member_replies": member_replies,
                "expected_agent": expected_agent,
                "expected_inner_tool": expected_inner_tool,
            }
        )
        return (
            report["answer"],
            {"selected_agent": report["selected_agent"], "inner_tool_names": report["inner_tool_names"]},
            {"delegate_payload": report["delegate_payload"], "supervisor_trace": report["trace"]},
        )
    except Exception as exc:
        return str(exc), {}, {}


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 5") as demo:
        gr.Markdown("# Week 5 - Supervisor Harness")
        request = gr.Textbox(label="요청", value="팀 회의 시간을 조율해줘")
        member_replies = gr.Textbox(label="멤버 응답", lines=4, value="민수: 2026-04-24 10:00 가능\n지아: 2026-04-24 10:00 가능")
        run_button = gr.Button("실행", variant="primary")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        selected_json = gr.JSON(label="선택된 Agent와 내부 Tool")
        trace_json = gr.JSON(label="Supervisor/Sub-Agent Tool Trace")
        run_button.click(run_ui, inputs=[request, member_replies], outputs=[answer, selected_json, trace_json])
    return demo


if __name__ == "__main__":
    create_demo().launch()
