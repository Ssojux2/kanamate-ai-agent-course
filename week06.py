"""Week 6 KanaMate Python practice and Gradio UI."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Callable

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
# 6주차는 앞 주차 개념을 합쳐 "설명 가능한 최종 데모"로 만든다.
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_WEEK06_DB_PATH = PROJECT_ROOT / "tmp" / "week06_memory.sqlite3"
SAVED_MEMORIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS saved_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL
)
"""


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load the repo-root .env next to this weekly script."""
    # 최종 데모에서도 week01-week05와 같은 방식으로 환경 변수를 읽는다.
    load_dotenv(ENV_PATH, override=True)


def openai_model_name() -> str:
    # supervisor와 Nana/Kana sub-agent가 사용할 기본 chat 모델이다.
    load_project_env()
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def openai_embedding_model_name() -> str:
    # 6주차 파일에서는 직접 쓰지 않지만, 공통 구조를 유지해 확장 여지를 남긴다.
    load_project_env()
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)


def require_openai_api_key() -> str:
    # 최종 데모는 여러 agent를 호출하므로 시작 전에 API key 누락을 명확히 알려준다.
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    return api_key


def make_model(max_tokens: int = 500) -> ChatOpenAI:
    # supervisor와 sub-agent가 같은 .env 모델 설정을 공유한다.
    require_openai_api_key()
    return ChatOpenAI(
        model=openai_model_name(),
        temperature=0,
        max_completion_tokens=max_tokens,
    )


def show_json(value: Any) -> None:
    # selected_agent, delegate_payload, trace를 발표용으로 읽기 좋게 출력한다.
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def load_saved_memories(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return saved Week 6 memory rows in a JSON-friendly shape."""
    load_project_env()
    target_path = Path(db_path or os.getenv("KANAMATE_WEEK06_DB_PATH") or DEFAULT_WEEK06_DB_PATH).resolve()
    if not target_path.exists():
        return []
    with sqlite3.connect(target_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(SAVED_MEMORIES_TABLE_SQL)
        rows = conn.execute(
            """
            SELECT memory_id, title, content, source, status
            FROM saved_memories
            ORDER BY id
            """
        ).fetchall()
    return [
        {
            "memory_id": row["memory_id"],
            "title": row["title"],
            "content": row["content"],
            "source": row["source"],
            "status": row["status"],
            "sqlite_path": str(target_path),
        }
        for row in rows
    ]


def final_text(agent_result: dict[str, Any]) -> str:
    # agent_result 안에는 중간 message가 많으므로 마지막 message만 답변으로 사용한다.
    return agent_result["messages"][-1].content


def extract_tool_trace(agent_result: dict[str, Any]) -> list[dict[str, Any]]:
    # 최종 데모에서도 trace가 있어야 선택 agent와 내부 tool을 설명할 수 있다.
    trace: list[dict[str, Any]] = []
    for message in agent_result.get("messages", []):
        # supervisor 단계와 sub-agent 단계를 같은 포맷으로 모아 UI에서 재사용한다.
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


@tool("personal_create_schedule", description="개인 일정을 생성한다.")
def personal_create_schedule(title: str, date: str, start_time: str) -> str:
    """Create a personal schedule."""
    # Nana가 개인 일정을 처리했음을 보여주는 최소 payload다.
    # 실제 DB 저장 대신 payload 모양에 집중하는 최종 데모용 tool을 바로 실행한다.
    return json.dumps(
        {"ok": True, "schedule": {"title": title, "date": date, "start_time": start_time}},
        ensure_ascii=False,
    )


@tool("group_confirm_slot", description="그룹 일정 시간을 확정한다.")
def group_confirm_slot(topic: str, selected_slot: str, members: list[str], reason: str) -> str:
    """Confirm a group schedule slot."""
    # Kana가 그룹 시간 확정을 처리했음을 보여주는 최소 payload다.
    # selected_slot과 reason을 함께 남겨 "왜 이 시간이 선택됐는지" 설명할 수 있게 한다.
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


@tool("memory_save", description="사용자 메모를 저장한다.")
def memory_save(title: str, content: str) -> str:
    """Save a user memory."""
    # TODO 문제 1: 6주차 Nana가 사용할 메모 저장 tool payload를 만든다.
    # 모범 답안 1:
    # tool 자체가 구조화된 입력을 SQLite row로 남기고, 저장된 row를 payload로 돌려준다.
    load_dotenv(ENV_PATH, override=True)
    target_path = Path(os.getenv("KANAMATE_WEEK06_DB_PATH") or DEFAULT_WEEK06_DB_PATH).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    memory_text = f"{title}\n{content}"
    memory_id = f"memory-{hashlib.sha256(memory_text.encode('utf-8')).hexdigest()[:12]}"
    saved_memory = {
        "memory_id": memory_id,
        "title": title,
        "content": content,
        "source": "week06.memory_save",
        "status": "saved",
        "sqlite_path": str(target_path),
    }
    with sqlite3.connect(target_path) as conn:
        conn.execute(SAVED_MEMORIES_TABLE_SQL)
        conn.execute(
            """
            INSERT INTO saved_memories
                (memory_id, title, content, source, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET
                title = excluded.title,
                content = excluded.content,
                source = excluded.source,
                status = excluded.status
            """,
            (
                saved_memory["memory_id"],
                saved_memory["title"],
                saved_memory["content"],
                saved_memory["source"],
                saved_memory["status"],
            ),
        )
        conn.commit()
    return json.dumps({"ok": True, "memory": saved_memory}, ensure_ascii=False)


def delegated_agent_from_trace(agent_result: dict[str, Any]) -> str:
    # supervisor가 호출한 위임 tool 이름에서 선택된 agent를 읽는다.
    for event in extract_tool_trace(agent_result):
        # nana_agent/kana_agent가 보이면 supervisor 라우팅은 일단 수행된 것이다.
        if event.get("event") == "tool_call" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return event["tool_name"].replace("_agent", "")
    return "unknown"


def delegated_payload_from_trace(agent_result: dict[str, Any]) -> dict[str, Any]:
    # 위임 tool_result 안에는 sub-agent의 최종 답변과 내부 trace가 들어 있다.
    for event in extract_tool_trace(agent_result):
        # JSON 문자열을 dict로 바꿔야 UI와 검증 코드에서 key로 접근할 수 있다.
        if event.get("event") == "tool_result" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return json.loads(event["content"])
    return {}


def inner_tool_names_from_payload(payload: dict[str, Any]) -> list[str]:
    # 검증 helper: sub-agent 내부 trace에서 실제 업무 tool 이름만 모은다.
    return [
        event["tool_name"]
        for event in payload.get("trace", [])
        if event.get("event") == "tool_call"
    ]


@tool("nana_agent", description="개인 일정이나 메모 요청을 나나 sub-agent에게 위임한다.")
def week06_delegate_to_nana(request: str) -> str:
    """Delegate a personal request to Nana sub-agent."""
    # TODO 문제 2: Nana 위임 tool 안에서 개인 일정/메모 tool을 가진 sub-agent를 바로 실행한다.
    # 모범 답안 2:
    # supervisor가 Nana에게 위임하면, Nana 내부 tool trace까지 payload로 되돌린다.
    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    nana_agent = create_agent(
        model=ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            temperature=0,
            max_completion_tokens=700,
        ),
        tools=[personal_create_schedule, memory_save],
        system_prompt=(
            "너는 나나다. 오늘은 2026-04-23이다. 상대 날짜는 이 날짜 기준으로 YYYY-MM-DD로 바꾼다. "
            "개인 일정은 personal_create_schedule 도구를 호출한다. "
            "사용자가 기억, 메모, 저장을 요청하거나 중요한 장소/선호/프로젝트 정보를 알려주면 "
            "memory_save 도구를 호출한다."
        ),
    )
    agent_result = nana_agent.invoke({"messages": [{"role": "user", "content": request}]})
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
    return json.dumps(
        # 이 payload가 supervisor tool_result content로 들어간다.
        {"agent": "nana", "answer": agent_result["messages"][-1].content, "trace": trace},
        ensure_ascii=False,
    )


@tool("kana_agent", description="그룹 일정 조율 요청과 멤버 응답을 카나 sub-agent에게 위임한다.")
def week06_delegate_to_kana(request: str, member_replies: str) -> str:
    """Delegate a group coordination request to Kana sub-agent."""
    # TODO 문제 3: Kana 위임 tool 안에서 그룹 일정 확정 tool을 가진 sub-agent를 바로 실행한다.
    # 모범 답안 3:
    # 그룹 모드에서는 멤버 응답이 빠지면 Kana가 판단할 근거가 부족하다.
    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    message = f"요청: {request}\n그룹 응답:\n{member_replies}"
    kana_agent = create_agent(
        model=ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            temperature=0,
            max_completion_tokens=800,
        ),
        tools=[group_confirm_slot],
        system_prompt="너는 카나다. 그룹 응답에서 공통 가능 시간을 찾으면 group_confirm_slot 도구를 호출한다.",
    )
    agent_result = kana_agent.invoke({"messages": [{"role": "user", "content": message}]})
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
    return json.dumps(
        # request와 member_replies를 합친 입력으로 Kana가 어떤 tool을 불렀는지 trace에 남긴다.
        {"agent": "kana", "answer": agent_result["messages"][-1].content, "trace": trace},
        ensure_ascii=False,
    )


def make_supervisor(mode: str = "auto"):
    # mode는 UI에서 사용자가 라우팅을 고정하거나 auto 판단을 실험하는 장치다.
    if mode == "personal":
        # TODO 문제 4: personal 모드에서는 Nana 위임 tool만 supervisor에게 제공한다.
        # 모범 답안 4:
        tools = [week06_delegate_to_nana]
        prompt = "너는 카나메이트 supervisor다. 사용자가 personal 모드를 선택했으므로 nana_agent tool을 호출한다."
    elif mode == "group":
        # TODO 문제 5: group 모드에서는 Kana 위임 tool만 supervisor에게 제공한다.
        # 모범 답안 5:
        tools = [week06_delegate_to_kana]
        prompt = "너는 카나메이트 supervisor다. 사용자가 group 모드를 선택했으므로 kana_agent tool을 호출한다."
    else:
        # auto 모드에서는 supervisor가 요청 내용을 보고 Nana/Kana 중 하나를 고른다.
        # TODO 문제 6: auto 모드에서는 Nana/Kana 위임 tool을 모두 제공한다.
        # 모범 답안 6:
        tools = [week06_delegate_to_nana, week06_delegate_to_kana]
        prompt = (
            "너는 카나메이트 supervisor다. 개인 일정/메모 저장 요청은 nana_agent tool을 호출하고, "
            "그룹 일정 조율 요청은 kana_agent tool을 호출한다. 직접 처리하지 말고 반드시 "
            "적절한 sub-agent tool을 호출한다."
        )
    return create_agent(model=make_model(1000), tools=tools, system_prompt=prompt)


def run_live_flow(student_request: str, member_replies: str = "", mode: str = "auto") -> dict[str, Any]:
    # Live Flow는 UI 한 번 실행에 필요한 전체 supervisor 흐름을 감싼다.
    # TODO 문제 7: UI 모드에 맞는 supervisor를 만들고 사용자 입력을 실행한다.
    # 모범 답안 7:
    supervisor = make_supervisor(mode)
    content = (
        # auto/group에서는 멤버 응답까지 supervisor에게 보여줘야 Kana 위임 판단이 가능하다.
        f"요청: {student_request}\n그룹 응답:\n{member_replies}"
        if mode in {"auto", "group"}
        else student_request
    )
    supervisor_result = supervisor.invoke({"messages": [{"role": "user", "content": content}]})
    # TODO 문제 8: 발표에 필요한 selected_agent, answer, trace, delegate_payload를 반환한다.
    # 모범 답안 8:
    return {
        # 발표 때는 아래 네 값을 순서대로 설명하면 된다.
        # selected_agent -> supervisor 선택, trace -> supervisor 근거,
        # delegate_payload -> sub-agent 답변/내부 tool 근거다.
        "selected_agent": delegated_agent_from_trace(supervisor_result),
        "answer": final_text(supervisor_result),
        "trace": extract_tool_trace(supervisor_result),
        "delegate_payload": delegated_payload_from_trace(supervisor_result),
        "saved_memories": load_saved_memories(),
    }


practice_cases = [
    # 최종 점검용 시나리오: 개인 일정, 메모 저장, 그룹 일정 확정을 하나씩 검증한다.
    {
        "name": "personal_schedule",
        "mode": "personal",
        "request": "내일 11시에 민수와 1:1 일정 잡아줘",
        "member_replies": "",
        "expected_agent": "nana",
        "expected_inner_tool": "personal_create_schedule",
    },
    {
        "name": "memory_save",
        "mode": "personal",
        "request": "프로젝트 발표 장소는 3층 세미나실이라고 메모해줘",
        "member_replies": "",
        "expected_agent": "nana",
        "expected_inner_tool": "memory_save",
    },
    {
        "name": "group_slot",
        "mode": "group",
        "request": "팀 멤버들과 발표 리허설 시간을 조율해줘",
        "member_replies": "민수: 2026-04-24 15:00 가능\n지아: 2026-04-24 15:00 가능",
        "expected_agent": "kana",
        "expected_inner_tool": "group_confirm_slot",
    },
]


def run_practice_suite(
    cases: list[dict[str, Any]],
    runner: Callable[[str, str, str], dict[str, Any]] = run_live_flow,
) -> list[dict[str, Any]]:
    """Run Week 6 golden scenarios and return compact reports."""
    reports = []
    for case in cases:
        # 각 case는 입력과 기대 결과가 함께 들어 있는 작은 테스트 한 개다.
        # 검증 흐름 1: case의 mode/request/member_replies로 전체 흐름을 실행한다.
        result = runner(case["request"], case.get("member_replies", ""), case.get("mode", "auto"))

        # 검증 흐름 2: delegate_payload 내부 trace에서 실제 sub-agent tool 이름을 모은다.
        # 내부 tool 이름을 봐야 "agent 선택"뿐 아니라 "실제 업무 처리"까지 확인된다.
        inner_tool_names = inner_tool_names_from_payload(result["delegate_payload"])
        saved_memory_ids = []
        for event in result["delegate_payload"].get("trace", []):
            if event.get("event") != "tool_result" or event.get("tool_name") != "memory_save":
                continue
            try:
                tool_payload = json.loads(event.get("content", "{}"))
            except json.JSONDecodeError:
                continue
            memory_id = tool_payload.get("memory", {}).get("memory_id")
            if memory_id:
                saved_memory_ids.append(memory_id)
        sqlite_memory_ids = {
            memory["memory_id"]
            for memory in result.get("saved_memories", [])
        }
        memory_saved_to_sqlite = (
            bool(saved_memory_ids)
            and all(memory_id in sqlite_memory_ids for memory_id in saved_memory_ids)
            if case["expected_inner_tool"] == "memory_save"
            else True
        )

        # 검증 흐름 3: 기대 agent/tool과 실제 결과를 한 report에 담는다.
        reports.append(
            {
                "name": case["name"],
                "expected_agent": case["expected_agent"],
                "selected_agent": result["selected_agent"],
                "expected_inner_tool": case["expected_inner_tool"],
                "inner_tool_names": inner_tool_names,
                "saved_memory_ids": saved_memory_ids,
                "memory_saved_to_sqlite": memory_saved_to_sqlite,
                "passed": (
                    case["expected_agent"] == result["selected_agent"]
                    and case["expected_inner_tool"] in inner_tool_names
                    and memory_saved_to_sqlite
                ),
                "answer": result["answer"],
                "trace": result["trace"],
                "delegate_payload": result["delegate_payload"],
                "saved_memories": result.get("saved_memories", []),
            }
        )
    return reports


def run_live_ui(student_request: str, member_replies: str, mode: str):
    # Gradio 채팅 화면에서 최종 실행 결과를 만드는 callback이다.
    try:
        result = run_live_flow(student_request, member_replies, mode)
        return (
            # 화면 출력 순서: 자연어 답변, 내부 payload, supervisor trace.
            result["answer"],
            {
                "selected_agent": result["selected_agent"],
                "delegate_payload": result["delegate_payload"],
                "saved_memories": result["saved_memories"],
            },
            result["trace"],
        )
    except Exception as exc:
        return str(exc), {}, []


def append_user_message(student_request: str, history: list[dict[str, str]] | None):
    # 빠른 callback: 최종 supervisor 실행 전에 사용자 메시지를 먼저 보여준다.
    history = list(history or [])
    cleaned_request = student_request.strip()
    if not cleaned_request:
        return history, history, ""
    history.append({"role": "user", "content": cleaned_request})
    return history, history, ""


def run_live_chat_response(
    history: list[dict[str, str]] | None,
    member_replies: str,
    mode: str,
):
    # 느린 callback: 마지막 사용자 메시지를 Nana/Kana supervisor 흐름으로 처리한다.
    history = list(history or [])
    if not history or history[-1].get("role") != "user":
        return history, history, {}, []

    student_request = history[-1]["content"]
    answer, payload, trace = run_live_ui(student_request, member_replies, mode)
    history.append({"role": "assistant", "content": answer})
    return history, history, payload, trace


def clear_chat():
    return [], [], "", {}, []


def run_suite_ui():
    # 시나리오 점검용 callback이다. 현재 기본 UI에서는 사용하지 않지만 수업 점검용으로 남겨둔다.
    try:
        return [
            {
                "name": report["name"],
                "expected_agent": report["expected_agent"],
                "selected_agent": report["selected_agent"],
                "expected_inner_tool": report["expected_inner_tool"],
                "inner_tool_names": report["inner_tool_names"],
                "saved_memory_ids": report["saved_memory_ids"],
                "memory_saved_to_sqlite": report["memory_saved_to_sqlite"],
                "passed": report["passed"],
            }
            for report in run_practice_suite(practice_cases)
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def create_demo() -> gr.Blocks:
    # 최종 UI는 채팅 흐름만 바로 보이게 단순하게 구성한다.
    with gr.Blocks(title="KanaMate Week 6", fill_width=True, fill_height=True) as demo:
        with gr.Column(scale=1, min_width=0):
            gr.Markdown("# KanaMate Week 6")
            history_state = gr.State([])
            chatbot = gr.Chatbot(
                label="KanaMate",
                show_label=False,
                layout="bubble",
                height=540,
                scale=1,
                min_width=0,
                placeholder="",
            )
            with gr.Accordion("실행 옵션", open=False):
                # auto는 supervisor 판단을 보고, personal/group은 라우팅을 고정해 비교한다.
                mode = gr.Radio(["auto", "personal", "group"], value="auto", label="모드")
                member_replies = gr.Textbox(
                    label="멤버 응답",
                    lines=5,
                    min_width=0,
                    value="민수: 2026-04-24 15:00 가능\n지아: 2026-04-24 15:00 가능",
                )
            with gr.Row(equal_height=True):
                request = gr.Textbox(
                    label="메시지",
                    show_label=False,
                    value="팀 멤버들과 발표 리허설 시간을 조율해줘",
                    scale=8,
                    min_width=0,
                )
                run_button = gr.Button("전송", variant="primary", scale=1, min_width=96)
                clear_button = gr.Button("초기화", scale=1, min_width=96)
            with gr.Accordion("실행 상세", open=False):
                payload_json = gr.JSON(label="선택된 Agent, delegate payload, SQLite 저장 메모")
                trace_json = gr.JSON(label="Supervisor Trace")

        chat_outputs = [chatbot, history_state, request, payload_json, trace_json]
        user_outputs = [chatbot, history_state, request]
        response_outputs = [chatbot, history_state, payload_json, trace_json]
        run_button.click(
            append_user_message,
            inputs=[request, history_state],
            outputs=user_outputs,
            queue=False,
            show_progress="hidden",
        ).then(run_live_chat_response, inputs=[history_state, member_replies, mode], outputs=response_outputs)
        request.submit(
            append_user_message,
            inputs=[request, history_state],
            outputs=user_outputs,
            queue=False,
            show_progress="hidden",
        ).then(run_live_chat_response, inputs=[history_state, member_replies, mode], outputs=response_outputs)
        clear_button.click(clear_chat, outputs=chat_outputs)
    return demo


if __name__ == "__main__":
    create_demo().launch()
