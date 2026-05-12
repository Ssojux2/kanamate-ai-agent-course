"""Week 5 KanaMate Python practice and Gradio UI."""

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
# 5주차는 "supervisor -> sub-agent -> 내부 tool"의 2단계 trace를 관찰한다.
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load the repo-root .env next to this weekly script."""
    load_dotenv(ENV_PATH, override=True)


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
    # 여러 agent가 같은 모델 설정을 쓰도록 factory로 통일한다.
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
    # supervisor trace와 sub-agent trace를 같은 모양으로 비교하기 위한 helper다.
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
    # TODO 문제 1: Nana sub-agent가 사용할 개인 일정 생성 tool payload를 만든다.
    # 모범 답안 1:
    # sub-agent 내부 tool도 학생이 읽기 쉽도록 JSON 문자열 payload를 반환한다.
    return json.dumps(
        {"ok": True, "schedule": {"title": title, "date": date, "start_time": start_time}},
        ensure_ascii=False,
    )


def _group_confirm_slot(topic: str, selected_slot: str, members: list[str], reason: str) -> str:
    """Confirm a group schedule slot."""
    # TODO 문제 2: Kana sub-agent가 사용할 그룹 일정 확정 tool payload를 만든다.
    # 모범 답안 2:
    # 카나 sub-agent가 그룹 일정 확정에 성공했음을 보여주는 최소 payload다.
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


# TODO 문제 3: 일반 Python 함수를 Nana가 사용할 LangChain tool로 감싼다.
# 모범 답안 3:
personal_create_schedule_tool = tool(
    "personal_create_schedule",
    description="개인 일정을 생성한다.",
)(_personal_create_schedule)
# 아래 tool 객체들이 실제 agent에게 전달되는 LangChain tool이다.
# TODO 문제 4: 일반 Python 함수를 Kana가 사용할 LangChain tool로 감싼다.
# 모범 답안 4:
group_confirm_slot_tool = tool(
    "group_confirm_slot",
    description="그룹 일정 시간을 확정한다.",
)(_group_confirm_slot)
memory_save_tool = tool(
    "memory_save",
    description="사용자 메모를 저장한다.",
)(_memory_save)

def build_week05_nana_agent(max_tokens: int = 600):
    # Nana는 개인 일정 tool만 가진다. 그래서 개인 요청만 처리할 수 있다.
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
    # Kana는 그룹 일정 확정 tool만 가진다. 역할을 분리해 trace를 명확히 본다.
    return create_agent(
        model=make_model(max_tokens),
        tools=[group_confirm_slot_tool],
        system_prompt="너는 그룹 메이트 카나다. 멤버 응답에서 모두 가능한 시간을 찾으면 group_confirm_slot 도구를 호출한다.",
    )


def _week05_delegate_to_nana(request: str) -> str:
    """Delegate a personal request to Nana sub-agent."""
    # TODO 문제 5: supervisor가 호출할 Nana 위임 tool의 내부 실행 흐름을 만든다.
    # 모범 답안 5:
    # supervisor 입장에서는 이 함수 전체가 하나의 tool 호출처럼 보인다.
    agent_result = build_week05_nana_agent().invoke({"messages": [{"role": "user", "content": request}]})
    return json.dumps(
        {"agent": "nana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


def _week05_delegate_to_kana(request: str, member_replies: str) -> str:
    """Delegate a group coordination request to Kana sub-agent."""
    # TODO 문제 6: supervisor가 호출할 Kana 위임 tool의 내부 실행 흐름을 만든다.
    # 모범 답안 6:
    # 그룹 요청은 원래 요청과 멤버 응답을 함께 sub-agent에게 넘겨야 한다.
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
# supervisor가 볼 수 있는 tool은 업무 tool이 아니라 sub-agent 위임 tool이다.
week05_delegate_to_kana = tool(
    "kana_agent",
    description="그룹 일정 조율 요청과 멤버 응답을 카나 sub-agent에게 위임한다.",
)(_week05_delegate_to_kana)


def build_week05_supervisor(max_tokens: int = 900):
    # supervisor는 직접 일정을 만들지 않고 어떤 sub-agent를 부를지 결정한다.
    return create_agent(
        model=make_model(max_tokens),
        # TODO 문제 7: supervisor에게 업무 tool이 아니라 sub-agent 위임 tool을 제공한다.
        # 모범 답안 7:
        tools=[week05_delegate_to_nana, week05_delegate_to_kana],
        system_prompt=(
            "너는 카나메이트 supervisor다. 개인 일정 요청은 nana_agent tool을 호출하고, "
            "그룹 일정 조율 요청은 kana_agent tool을 호출한다. 직접 처리하지 말고 반드시 "
            "적절한 sub-agent tool을 호출한 뒤 그 결과를 수강생에게 요약한다."
        ),
    )


def delegated_agent_from_trace(agent_result: dict[str, Any]) -> str:
    # supervisor tool_call 이름을 보면 어떤 sub-agent가 선택됐는지 알 수 있다.
    for event in extract_tool_trace(agent_result):
        if event.get("event") == "tool_call" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return event["tool_name"].replace("_agent", "")
    return "unknown"


def delegated_payload_from_trace(agent_result: dict[str, Any]) -> dict[str, Any]:
    # sub-agent의 답변과 내부 trace는 supervisor tool_result 안에 JSON으로 들어 있다.
    for event in extract_tool_trace(agent_result):
        if event.get("event") == "tool_result" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return json.loads(event["content"])
    return {}


def supervisor_content_from_case(case: dict[str, Any]) -> str:
    # 검증 helper: 멤버 응답이 있으면 supervisor가 그룹 요청 맥락까지 함께 보게 한다.
    if case.get("member_replies"):
        return f"요청: {case['request']}\n멤버 응답:\n{case['member_replies']}"
    return case["request"]


def inner_tool_names_from_payload(payload: dict[str, Any]) -> list[str]:
    # 검증 helper: sub-agent 내부 trace에서 실제 업무 tool 이름만 모은다.
    return [
        event["tool_name"]
        for event in payload.get("trace", [])
        if event.get("event") == "tool_call"
    ]


golden_cases = [
    # Golden case는 "이 입력이면 이 agent/tool이 나와야 한다"는 반복 가능한 기준이다.
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
    # 핵심 흐름: 입력 만들기 -> supervisor 실행 -> 선택 agent 파악 -> 내부 tool 확인.
    # 검증 흐름 1: case dict에서 supervisor에게 보낼 메시지를 만든다.
    content = supervisor_content_from_case(case)

    # 검증 흐름 2: supervisor를 실행하고 trace에서 선택 agent를 읽는다.
    supervisor = supervisor_agent or build_week05_supervisor()
    result = supervisor.invoke({"messages": [{"role": "user", "content": content}]})
    selected_agent = delegated_agent_from_trace(result)
    delegate_payload = delegated_payload_from_trace(result)

    # 검증 흐름 3: sub-agent 내부 trace에서 실제 업무 tool 이름을 모은다.
    # delegate_payload["trace"]는 supervisor 바깥이 아니라 sub-agent 내부에서 생긴 trace다.
    inner_tool_names = inner_tool_names_from_payload(delegate_payload)

    # 검증 흐름 4: 기대 agent/tool과 실제 결과를 비교해 통과 여부가 포함된 report를 만든다.
    return {
        "name": case["name"],
        "expected_agent": case["expected_agent"],
        "selected_agent": selected_agent,
        "expected_inner_tool": case["expected_inner_tool"],
        "inner_tool_names": inner_tool_names,
        "passed": (
            case["expected_agent"] == selected_agent
            and case["expected_inner_tool"] in inner_tool_names
        ),
        "answer": final_text(result),
        "trace": extract_tool_trace(result),
        "delegate_payload": delegate_payload,
    }


def run_ui(request: str, member_replies: str):
    try:
        # UI에서는 멤버 응답이 있으면 그룹 요청, 없으면 개인 요청으로 기대값을 단순화한다.
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
    # 화면에는 최종 답변보다 selected_agent와 inner_tool_names가 더 중요한 관찰값이다.
    with gr.Blocks(title="KanaMate Week 5") as demo:
        gr.Markdown("# Week 5 - Supervisor Harness")
        request = gr.Textbox(label="요청", lines=3, value="팀 회의 시간을 조율해줘")
        member_replies = gr.Textbox(label="멤버 응답", lines=4, value="민수: 2026-04-24 10:00 가능\n지아: 2026-04-24 10:00 가능")
        run_button = gr.Button("실행", variant="primary")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        selected_json = gr.JSON(label="선택된 Agent와 내부 Tool")
        trace_json = gr.JSON(label="Supervisor/Sub-Agent Tool Trace")
        run_button.click(run_ui, inputs=[request, member_replies], outputs=[answer, selected_json, trace_json])
    return demo


if __name__ == "__main__":
    create_demo().launch()
