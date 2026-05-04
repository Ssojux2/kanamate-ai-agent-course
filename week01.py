"""Week 1 KanaMate assignment and Gradio UI."""

from __future__ import annotations

import json
import os
from typing import Any

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load .env from the current working tree without hard-coded paths."""
    load_dotenv()


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
# Week 1. Function call / tool call
# ---------------------------------------------------------------------------


schedules: list[dict[str, Any]] = []


def reset_schedules() -> None:
    schedules.clear()


@tool("create_schedule", description="개인 일정을 생성한다. date는 YYYY-MM-DD, start_time은 HH:MM 형식이다.")
def create_schedule(title: str, date: str, start_time: str, attendees: list[str] | None = None) -> str:
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


def build_week01_agent(max_tokens: int = 500):
    return create_agent(
        model=make_model(max_tokens),
        tools=[create_schedule, list_schedules],
        system_prompt=(
            "너는 개인 일정 메이트 나나다. 오늘은 2026-04-23이다. "
            "상대 날짜는 이 날짜 기준으로 YYYY-MM-DD로 바꾼다. "
            "일정 생성이나 조회가 필요하면 반드시 알맞은 도구를 호출한 뒤 짧게 답한다."
        ),
    )


def run_student_schedule_request(request: str, agent: Any | None = None) -> dict[str, Any]:
    """Run Nana with one schedule request, then list schedules for the UI."""
    nana_agent = agent or build_week01_agent()

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


def run_ui(request: str):
    try:
        result = run_student_schedule_request(request)
        return (
            f"{result['answer']}\n\n{result['list_answer']}",
            {"created_schedule": result["created_schedule"], "schedules": result["schedules"]},
            {"create_trace": result["trace"], "list_trace": result["list_trace"]},
        )
    except Exception as exc:
        return str(exc), {}, {}


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 1") as demo:
        gr.Markdown("# Week 1 - Schedule Tool Flow")
        request = gr.Textbox(label="요청", value="내일 10시에 민수와 회의 일정 잡아줘")
        run_button = gr.Button("실행", variant="primary")
        clear_button = gr.Button("일정 초기화")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        result_json = gr.JSON(label="완성 결과")
        trace_json = gr.JSON(label="Tool Trace")
        run_button.click(run_ui, inputs=request, outputs=[answer, result_json, trace_json])
        clear_button.click(lambda: (reset_schedules(), "일정을 초기화했습니다.")[1], outputs=answer)
    return demo


if __name__ == "__main__":
    create_demo().launch()
