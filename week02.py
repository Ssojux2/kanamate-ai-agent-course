"""Week 2 KanaMate assignment and Gradio UI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

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
# Week 2. Structured output / Pydantic
# ---------------------------------------------------------------------------


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


def build_week02_agent(max_tokens: int = 500):
    return create_agent(
        model=make_model(max_tokens),
        tools=[],
        response_format=PracticeExtractionResult,
        system_prompt=(
            "오늘은 2026-04-23이다. 사용자 요청을 schedule, todo, reminder, unknown 중 하나로 구조화한다. "
            "'N분 전에 알려줘' 같은 요청은 reminder로 분류하고 offset_minutes에는 N을 정수로 넣는다."
        ),
    )


def run_student_structured_request(request: str, agent: Any | None = None) -> PracticeExtractionResult:
    """Run the extended structured-output agent and return its Pydantic response."""
    practice_extract_agent = agent or build_week02_agent()

    # TODO 1: practice_extract_agent.invoke로 request를 실행한다.
    # 모범 답안 1(강의자료 테스트용)
    result = practice_extract_agent.invoke({"messages": [{"role": "user", "content": request}]})

    # TODO 2: result에서 structured_response를 꺼낸다.
    # 모범 답안 2(강의자료 테스트용)
    response = result["structured_response"]

    # TODO 3: UI와 자동 점검에서 재사용할 Pydantic 객체를 돌려준다.
    # 모범 답안 3(강의자료 테스트용)
    return response


def run_ui(request: str):
    try:
        return run_student_structured_request(request).model_dump()
    except Exception as exc:
        return {"error": str(exc)}


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 2") as demo:
        gr.Markdown("# Week 2 - Structured Output")
        request = gr.Textbox(label="요청", value="발표 30분 전에 알려줘")
        run_button = gr.Button("구조화 실행", variant="primary")
        result_json = gr.JSON(label="Pydantic Response")
        run_button.click(run_ui, inputs=request, outputs=result_json)
    return demo


if __name__ == "__main__":
    create_demo().launch()
