"""Week 1 KanaMate Python practice and Gradio UI."""

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
# 모든 주차 파일은 repo 루트의 .env를 기준으로 실행되게 맞춘다.
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load the repo-root .env next to this weekly script."""
    # override=True라 노트북/터미널에 남아 있는 예전 환경 변수보다 repo .env를 우선한다.
    load_dotenv(ENV_PATH, override=True)


def openai_model_name() -> str:
    # 모델 이름을 코드에 박아두지 않고 .env에서 바꾸게 해 실습 환경 차이를 줄인다.
    load_project_env()
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def openai_embedding_model_name() -> str:
    # 1주차에서는 embedding을 쓰지 않지만, 모든 주차 공통 helper 모양을 맞춰둔다.
    load_project_env()
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)


def require_openai_api_key() -> str:
    # API key가 없으면 모델 호출 지점까지 가지 않고, 바로 이해하기 쉬운 오류를 낸다.
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    return api_key


def make_model(max_tokens: int = 500) -> ChatOpenAI:
    # 수업 예제는 같은 모델 설정을 반복해서 쓰므로 factory로 한 곳에 모은다.
    require_openai_api_key()
    return ChatOpenAI(
        model=openai_model_name(),
        temperature=0,
        max_completion_tokens=max_tokens,
    )


def show_json(value: Any) -> None:
    # ensure_ascii=False 덕분에 한글 payload가 \uXXXX 형태로 깨져 보이지 않는다.
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def final_text(agent_result: dict[str, Any]) -> str:
    # LangChain agent 결과의 마지막 message가 사용자에게 보이는 최종 답변이다.
    return agent_result["messages"][-1].content


def extract_tool_trace(agent_result: dict[str, Any]) -> list[dict[str, Any]]:
    # LangChain 메시지 객체에서 학생이 볼 핵심만 꺼낸다:
    # 1) 모델이 어떤 tool을 호출했는지, 2) tool이 어떤 결과를 돌려줬는지.
    trace: list[dict[str, Any]] = []
    for message in agent_result.get("messages", []):
        # AIMessage에는 모델이 요청한 tool_calls가 들어 있다.
        for call in getattr(message, "tool_calls", []) or []:
            trace.append(
                {
                    "event": "tool_call",
                    "tool_name": call.get("name"),
                    "arguments": call.get("args", {}),
                }
            )
        # ToolMessage에는 실제 Python tool이 실행된 뒤 반환한 content가 들어 있다.
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
next_schedule_number = 1


def reset_schedules() -> None:
    # Gradio UI에서 이전 실습 결과를 지우고 다시 시작할 때 사용한다.
    # list 자체를 새로 만들지 않고 clear해야 tool 함수들이 같은 list를 계속 바라본다.
    global next_schedule_number
    schedules.clear()
    next_schedule_number = 1


def offline_mode_enabled() -> bool:
    # API quota가 없을 때도 1주차 tool trace 모양을 관찰할 수 있게 하는 옵션이다.
    return os.getenv("KANAMATE_OFFLINE", "").lower() in {"1", "true", "yes", "on"}


def is_quota_error(exc: Exception) -> bool:
    # OpenAI quota 오류는 수업 중 자주 만나는 실패라 1주차만 fallback으로 넘긴다.
    message = str(exc)
    return "insufficient_quota" in message or "Error code: 429" in message


def simple_offline_arguments(request: str) -> dict[str, Any]:
    # 오프라인 모드는 LLM 대신 아주 단순한 규칙으로 tool arguments를 만든다.
    # 정확한 자연어 처리가 목적이 아니라, tool_call payload 모양을 보여주는 용도다.
    attendees = [name for name in ["민수", "지아", "준호"] if name in request]
    start_time = "10:00"
    if "14시" in request or "오후 2시" in request:
        start_time = "14:00"
    elif "15시" in request or "오후 3시" in request:
        start_time = "15:00"
    elif "9시" in request or "오전 9시" in request:
        start_time = "09:00"

    date = "2026-04-24" if "내일" in request else "2026-04-27"
    return {
        "title": request,
        "date": date,
        "start_time": start_time,
        "attendees": attendees,
    }


def simple_offline_schedule_id(request: str) -> str:
    # 오프라인 모드에서 "schedule-1 삭제"처럼 입력하면 해당 id를 간단히 뽑는다.
    for schedule in schedules:
        if schedule["id"] in request:
            return schedule["id"]
    return schedules[-1]["id"] if schedules else "schedule-1"


def run_offline_schedule_request(request: str, reason: str = "") -> dict[str, Any]:
    # 실제 agent 결과와 같은 모양의 dict를 만들어 UI와 테스트 흐름을 유지한다.
    global next_schedule_number
    if any(keyword in request for keyword in ["삭제", "지워", "취소"]):
        schedule_id = simple_offline_schedule_id(request)
        deleted_schedule = None
        for index, schedule in enumerate(schedules):
            if schedule["id"] == schedule_id:
                deleted_schedule = schedules.pop(index)
                break
        delete_content = json.dumps(
            {"ok": deleted_schedule is not None, "deleted_schedule": deleted_schedule, "schedule_id": schedule_id},
            ensure_ascii=False,
        )
        list_content = json.dumps({"ok": True, "schedules": schedules}, ensure_ascii=False)
        notice = "OpenAI API quota 문제로 로컬 오프라인 모드 결과를 표시합니다."
        if reason:
            notice = f"{notice} ({reason})"
        answer = (
            f"[오프라인 모드] {schedule_id} 일정을 삭제했습니다. {notice}"
            if deleted_schedule
            else f"[오프라인 모드] {schedule_id} 일정을 찾지 못했습니다. {notice}"
        )
        return {
            "answer": answer,
            "list_answer": "[오프라인 모드] 현재 일정 목록을 조회했습니다.",
            "trace": [
                {"event": "tool_call", "tool_name": "delete_schedule", "arguments": {"schedule_id": schedule_id}},
                {"event": "tool_result", "tool_name": "delete_schedule", "content": delete_content},
            ],
            "list_trace": [
                {"event": "tool_call", "tool_name": "list_schedules", "arguments": {}},
                {"event": "tool_result", "tool_name": "list_schedules", "content": list_content},
            ],
            "created_schedule": None,
            "deleted_schedule": deleted_schedule,
            "schedules": list(schedules),
        }

    arguments = simple_offline_arguments(request)
    created_schedule = {
        "id": f"schedule-{next_schedule_number}",
        "title": arguments["title"],
        "date": arguments["date"],
        "start_time": arguments["start_time"],
        "attendees": arguments["attendees"],
    }
    next_schedule_number += 1
    schedules.append(created_schedule)
    # tool_result content는 실제 LangChain 실행 때처럼 JSON 문자열로 맞춘다.
    create_content = json.dumps({"ok": True, "schedule": created_schedule}, ensure_ascii=False)
    list_content = json.dumps({"ok": True, "schedules": schedules}, ensure_ascii=False)

    notice = "OpenAI API quota 문제로 로컬 오프라인 모드 결과를 표시합니다."
    if reason:
        notice = f"{notice} ({reason})"

    return {
        "answer": f"[오프라인 모드] 일정을 생성했습니다. {notice}",
        "list_answer": "[오프라인 모드] 현재 일정 목록을 조회했습니다.",
        "trace": [
            {"event": "tool_call", "tool_name": "create_schedule", "arguments": arguments},
            {"event": "tool_result", "tool_name": "create_schedule", "content": create_content},
        ],
        "list_trace": [
            {"event": "tool_call", "tool_name": "list_schedules", "arguments": {}},
            {"event": "tool_result", "tool_name": "list_schedules", "content": list_content},
        ],
        "created_schedule": created_schedule,
        "deleted_schedule": None,
        "schedules": list(schedules),
    }


# TODO 문제 1: `@tool` 데코레이터로 개인 일정 생성 tool을 등록한다.
# 모범 답안 1:
@tool("create_schedule", description="개인 일정을 생성한다. date는 YYYY-MM-DD, start_time은 HH:MM 형식이다.")
def create_schedule(title: str, date: str, start_time: str, attendees: list[str] | None = None) -> str:
    """Create a personal schedule."""
    # TODO 문제 2: tool 입력값으로 일정을 저장하고 JSON 문자열 payload를 반환한다.
    # 모범 답안 2:
    # LangChain tool은 문자열 반환이 안전하므로 JSON 문자열로 payload를 돌려준다.
    # title/date/start_time/attendees는 모델이 자연어에서 뽑아낸 tool 인자다.
    global next_schedule_number
    schedule = {
        "id": f"schedule-{next_schedule_number}",
        "title": title,
        "date": date,
        "start_time": start_time,
        "attendees": attendees or [],
    }
    next_schedule_number += 1
    schedules.append(schedule)
    return json.dumps({"ok": True, "schedule": schedule}, ensure_ascii=False)


# TODO 문제 3: `@tool` 데코레이터로 현재 일정 목록 조회 tool을 등록한다.
# 모범 답안 3:
@tool("list_schedules", description="현재 생성된 개인 일정 목록을 조회한다.")
def list_schedules() -> str:
    """List personal schedules."""
    # TODO 문제 4: 메모리에 저장된 일정 목록을 JSON 문자열 payload로 반환한다.
    # 모범 답안 4:
    # 생성 tool이 바꾼 schedules 상태를 조회 tool이 그대로 읽는지 확인한다.
    return json.dumps({"ok": True, "schedules": schedules}, ensure_ascii=False)


# TODO 문제 6: `@tool` 데코레이터로 등록된 개인 일정 삭제 tool을 등록한다.
# 모범 답안 6:
@tool("delete_schedule", description="schedule_id와 일치하는 개인 일정을 삭제한다. 예: schedule-1")
def delete_schedule(schedule_id: str) -> str:
    """Delete a personal schedule by id."""
    # TODO 문제 7: schedule_id로 일정을 삭제하고 성공 여부를 JSON 문자열 payload로 반환한다.
    # 모범 답안 7:
    # 삭제에 성공하면 deleted_schedule에 삭제된 dict가 들어가고, 실패하면 None이 들어간다.
    deleted_schedule = None
    for index, schedule in enumerate(schedules):
        if schedule["id"] == schedule_id:
            deleted_schedule = schedules.pop(index)
            break
    return json.dumps(
        {
            "ok": deleted_schedule is not None,
            "deleted_schedule": deleted_schedule,
            "schedule_id": schedule_id,
        },
        ensure_ascii=False,
    )


def build_week01_agent(max_tokens: int = 500):
    # Agent는 모델 + 사용할 수 있는 tool 목록 + 역할 지시문으로 구성된다.
    return create_agent(
        model=make_model(max_tokens),
        # TODO 문제 8: agent가 사용할 수 있는 tool 목록에 생성/조회/삭제 tool을 모두 넣는다.
        # 모범 답안 8:
        tools=[create_schedule, list_schedules, delete_schedule],
        system_prompt=(
            "너는 개인 일정 메이트 나나다. 오늘은 2026-04-23이다. "
            "상대 날짜는 이 날짜 기준으로 YYYY-MM-DD로 바꾼다. "
            "일정 생성, 조회, 삭제가 필요하면 반드시 알맞은 도구를 호출한 뒤 짧게 답한다. "
            "삭제 요청은 먼저 사용자가 말한 schedule_id를 delete_schedule 도구에 전달한다."
        ),
    )


def run_student_schedule_request(request: str, agent: Any | None = None) -> dict[str, Any]:
    """Run Nana with one schedule request, then list schedules for the UI."""
    # 이 함수가 1주차 핵심 흐름이다:
    # 요청 실행 -> 생성 tool trace 파싱 -> 목록 조회 tool 실행 -> UI용 결과 반환.
    if agent is None and offline_mode_enabled():
        return run_offline_schedule_request(request, "KANAMATE_OFFLINE=1")

    nana_agent = agent or build_week01_agent()

    # 실행 흐름: 사용자의 일정 생성 요청을 agent에게 보낸다.
    try:
        result = nana_agent.invoke({"messages": [{"role": "user", "content": request}]})
    except Exception as exc:
        # 사용자가 직접 agent를 주입한 테스트에서는 fallback하지 않고 원래 오류를 보존한다.
        if agent is None and is_quota_error(exc):
            return run_offline_schedule_request(request, "insufficient_quota")
        raise

    # 관찰 흐름: agent 실행 결과에서 tool trace와 생성된 일정을 읽는다.
    trace = extract_tool_trace(result)
    created_schedule = None
    deleted_schedule = None
    for event in trace:
        if event.get("event") != "tool_result":
            continue
        if event.get("tool_name") == "create_schedule":
            created_schedule = json.loads(event["content"]).get("schedule")
        elif event.get("tool_name") == "delete_schedule":
            deleted_schedule = json.loads(event["content"]).get("deleted_schedule")

    # 관찰 흐름: 생성/삭제/조회 요청 직후 목록 조회를 다시 실행해 상태 변화를 확인한다.
    list_result = nana_agent.invoke({"messages": [{"role": "user", "content": "현재 일정 목록 보여줘"}]})
    list_trace = extract_tool_trace(list_result)
    schedule_snapshot = []
    for event in list_trace:
        if event.get("event") == "tool_result" and event.get("tool_name") == "list_schedules":
            schedule_snapshot = json.loads(event["content"]).get("schedules", [])
            break

    return {
        # UI는 이 dict를 받아 답변, payload, trace 영역으로 나눠 보여준다.
        "answer": final_text(result),
        "list_answer": final_text(list_result),
        "trace": trace,
        "list_trace": list_trace,
        "created_schedule": created_schedule,
        "deleted_schedule": deleted_schedule,
        "schedules": schedule_snapshot,
    }


def run_ui(request: str):
    # Gradio callback은 화면 컴포넌트 개수에 맞춰 tuple을 반환한다.
    try:
        result = run_student_schedule_request(request)
        return (
            # 첫 번째 출력: 학생이 읽는 자연어 답변.
            f"{result['answer']}\n\n{result['list_answer']}",
            # 두 번째 출력: 생성/삭제된 일정과 현재 목록을 JSON으로 확인한다.
            {
                "created_schedule": result["created_schedule"],
                "deleted_schedule": result["deleted_schedule"],
                "schedules": result["schedules"],
            },
            # 세 번째 출력: 모델이 실제로 어떤 tool을 호출했는지 확인한다.
            {"create_trace": result["trace"], "list_trace": result["list_trace"]},
        )
    except Exception as exc:
        return str(exc), {}, {}


def append_user_message(request: str, history: list[dict[str, str]] | None):
    # 빠른 callback: 모델 호출 전에 사용자 메시지를 먼저 화면에 올린다.
    history = list(history or [])
    cleaned_request = request.strip()
    if not cleaned_request:
        return history, history, ""
    history.append({"role": "user", "content": cleaned_request})
    return history, history, ""


def run_chat_response(history: list[dict[str, str]] | None):
    # 느린 callback: 마지막 사용자 메시지를 읽어 agent/tool 실행 후 assistant 답변을 붙인다.
    history = list(history or [])
    if not history or history[-1].get("role") != "user":
        return history, history, {}, {}

    request = history[-1]["content"]
    try:
        result = run_student_schedule_request(request)
        assistant_message = f"{result['answer']}\n\n{result['list_answer']}"
        details = {
            "created_schedule": result["created_schedule"],
            "deleted_schedule": result["deleted_schedule"],
            "schedules": result["schedules"],
        }
        trace = {"create_trace": result["trace"], "list_trace": result["list_trace"]}
    except Exception as exc:
        assistant_message = f"오류가 발생했습니다.\n\n{exc}"
        details = {}
        trace = {}

    history.append({"role": "assistant", "content": assistant_message})
    return history, history, details, trace


def clear_chat():
    # 채팅 화면과 1주차 메모리 일정 상태를 함께 초기화한다.
    reset_schedules()
    return [], [], "", {}, {}


def create_demo() -> gr.Blocks:
    # create_demo는 import만 해도 API를 호출하지 않도록 UI 선언만 담당한다.
    with gr.Blocks(title="KanaMate Week 1", fill_width=True, fill_height=True) as demo:
        with gr.Column(scale=1, min_width=0):
            gr.Markdown("# KanaMate Week 1")
            history_state = gr.State([])
            chatbot = gr.Chatbot(
                label="KanaMate",
                show_label=False,
                layout="bubble",
                height=560,
                scale=1,
                min_width=0,
                placeholder="",
            )
            with gr.Row(equal_height=True):
                request = gr.Textbox(
                    label="메시지",
                    show_label=False,
                    value="내일 10시에 민수와 회의 일정 잡아줘",
                    scale=8,
                    min_width=0,
                )
                run_button = gr.Button("전송", variant="primary", scale=1, min_width=96)
                clear_button = gr.Button("초기화", scale=1, min_width=96)
            with gr.Accordion("실행 상세", open=False):
                result_json = gr.JSON(label="완성 결과")
                trace_json = gr.JSON(label="Tool Trace")

        chat_outputs = [chatbot, history_state, request, result_json, trace_json]
        user_outputs = [chatbot, history_state, request]
        response_outputs = [chatbot, history_state, result_json, trace_json]
        run_button.click(
            append_user_message,
            inputs=[request, history_state],
            outputs=user_outputs,
            queue=False,
            show_progress="hidden",
        ).then(run_chat_response, inputs=history_state, outputs=response_outputs)
        request.submit(
            append_user_message,
            inputs=[request, history_state],
            outputs=user_outputs,
            queue=False,
            show_progress="hidden",
        ).then(run_chat_response, inputs=history_state, outputs=response_outputs)
        clear_button.click(clear_chat, outputs=chat_outputs)
    return demo


if __name__ == "__main__":
    create_demo().launch()
