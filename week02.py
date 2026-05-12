"""Week 2 KanaMate Python practice and Gradio UI."""

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
# 주차별 스크립트는 실행 위치와 상관없이 repo 루트 설정을 읽는다.
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
    # structured output도 결국 ChatOpenAI 모델 호출 위에서 동작한다.
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
    # 2주차는 tool을 쓰지 않지만, 공통 helper 모양을 유지해 주차 간 비교를 쉽게 한다.
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
    # TODO 문제 1: 일정 요청을 앱에서 쓰기 쉬운 Pydantic 필드로 정의한다.
    # 모범 답안 1:
    # 일정 요청이 구조화되면 앱이나 DB에 넣기 쉬운 필드가 된다.
    title: str = Field(description="일정 제목")
    date: str = Field(description="YYYY-MM-DD")
    start_time: str = Field(description="HH:MM")
    attendees: list[str] = Field(default_factory=list)


class TodoCreate(BaseModel):
    # TODO 문제 2: 할 일 요청을 title, due_date, priority 필드로 구조화한다.
    # 모범 답안 2:
    # 할 일은 일정과 다르게 시간이 없어도 되므로 due_date를 선택값으로 둔다.
    title: str
    due_date: str | None = Field(default=None, description="YYYY-MM-DD")
    priority: Literal["low", "medium", "high"] = "medium"


class ReminderCreate(BaseModel):
    # TODO 문제 3: 알림 요청에서 기준 사건과 몇 분 전인지 숫자로 분리한다.
    # 모범 답안 3:
    # 알림은 "무엇을 기준으로 몇 분 전인가"를 숫자로 꺼내는 연습이다.
    title: str = Field(description="알림 제목")
    related_event: str | None = Field(default=None, description="알림이 연결된 일정이나 사건")
    offset_minutes: int = Field(description="기준 사건 몇 분 전에 알릴지")


class PracticeExtractionResult(BaseModel):
    # TODO 문제 4: kind에 따라 schedule/todo/reminder/question 중 필요한 결과를 담는다.
    # 모범 답안 4:
    # kind는 어느 세부 객체를 읽어야 하는지 알려주는 라벨 역할을 한다.
    kind: Literal["schedule", "todo", "reminder", "unknown"]
    schedule: ScheduleCreate | None = None
    todo: TodoCreate | None = None
    reminder: ReminderCreate | None = None
    question: str | None = None


def build_week02_agent(max_tokens: int = 500):
    # response_format을 지정하면 최종 답변 대신 Pydantic 객체를 받을 수 있다.
    return create_agent(
        model=make_model(max_tokens),
        tools=[],
        # TODO 문제 5: response_format에 Pydantic 결과 모델을 지정한다.
        # 모범 답안 5:
        response_format=PracticeExtractionResult,
        system_prompt=(
            "오늘은 2026-04-23이다. 사용자 요청을 schedule, todo, reminder, unknown 중 하나로 구조화한다. "
            "'N분 전에 알려줘' 같은 요청은 reminder로 분류하고 offset_minutes에는 N을 정수로 넣는다."
        ),
    )


def run_student_structured_request(request: str, agent: Any | None = None) -> PracticeExtractionResult:
    """Run the extended structured-output agent and return its Pydantic response."""
    # 핵심 흐름: 자연어 요청 -> agent 실행 -> structured_response만 꺼내기.
    practice_extract_agent = agent or build_week02_agent()

    # 실행 흐름: 자연어 요청을 structured-output agent에게 보낸다.
    result = practice_extract_agent.invoke({"messages": [{"role": "user", "content": request}]})

    # 관찰 흐름: LangChain 결과 dict에서 Pydantic 객체만 꺼낸다.
    response = result["structured_response"]

    # UI와 자동 점검에서 같은 객체를 재사용하게 돌려준다.
    return response


def run_ui(request: str):
    try:
        # Gradio JSON 컴포넌트는 Pydantic 객체보다 dict를 바로 보여주기 좋다.
        return run_student_structured_request(request).model_dump()
    except Exception as exc:
        return {"error": str(exc)}


def create_demo() -> gr.Blocks:
    # UI 선언은 모델 호출 없이 만들어져야 검증 명령에서 안전하게 import할 수 있다.
    with gr.Blocks(title="KanaMate Week 2") as demo:
        gr.Markdown("# Week 2 - Structured Output")
        request = gr.Textbox(label="요청", lines=3, value="10시 졸업작품 발표가 있어. 발표 30분 전에 알려줘")
        run_button = gr.Button("구조화 실행", variant="primary")
        result_json = gr.JSON(label="Pydantic Response")
        run_button.click(run_ui, inputs=request, outputs=result_json)
    return demo


if __name__ == "__main__":
    create_demo().launch()
