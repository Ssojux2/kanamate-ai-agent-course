"""Week 4 KanaMate Python practice and Gradio UI."""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sqlite3
import threading
from typing import Any

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
# 4주차는 이 파일이 client/UI이고, week04_mcp_server.py가 별도 MCP server다.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_WEEK04_DB_PATH = PROJECT_ROOT / "tmp" / "week04_calendar.sqlite3"
DEFAULT_WEEK04_MCP_HOST = "127.0.0.1"
DEFAULT_WEEK04_MCP_PORT = 8004
WEEK04_MCP_URL = f"http://{DEFAULT_WEEK04_MCP_HOST}:{DEFAULT_WEEK04_MCP_PORT}/mcp"
WEEK04_MCP_SERVER_PATH = PROJECT_ROOT / "week04_mcp_server.py"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load the repo-root .env next to this weekly script."""
    # client 쪽 환경 변수와 서버 쪽 환경 변수를 같은 repo .env에서 읽는다.
    load_dotenv(ENV_PATH, override=True)


def openai_model_name() -> str:
    # MCP tool을 고르는 agent가 사용할 chat 모델 이름이다.
    load_project_env()
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def openai_embedding_model_name() -> str:
    # 4주차에서는 직접 쓰지 않지만 공통 helper를 유지해 주차 간 차이를 줄인다.
    load_project_env()
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)


def require_openai_api_key() -> str:
    # MCP 서버 호출은 로컬이지만, 어떤 MCP tool을 부를지는 OpenAI 모델이 판단한다.
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    return api_key


def make_model(max_tokens: int = 500) -> ChatOpenAI:
    # temperature=0으로 두면 같은 입력에서 tool 선택이 비교적 안정적이다.
    require_openai_api_key()
    return ChatOpenAI(
        model=openai_model_name(),
        temperature=0,
        max_completion_tokens=max_tokens,
    )


def show_json(value: Any) -> None:
    # MCP payload와 SQLite row를 사람이 비교하기 쉬운 JSON 형태로 출력한다.
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def final_text(agent_result: dict[str, Any]) -> str:
    # 학생 발표에서는 최종 문장보다 아래 trace/payload를 더 중요하게 본다.
    return agent_result["messages"][-1].content


def extract_tool_trace(agent_result: dict[str, Any]) -> list[dict[str, Any]]:
    # MCP tool도 LangChain agent 안에서는 일반 tool_call/tool_result처럼 관찰된다.
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
# Week 4. Real MCP tool call
# ---------------------------------------------------------------------------


def week04_mcp_host() -> str:
    # 포트 충돌이 나면 .env나 shell 환경 변수로 host/port를 바꿀 수 있다.
    load_project_env()
    return os.getenv("KANAMATE_WEEK04_MCP_HOST", DEFAULT_WEEK04_MCP_HOST)


def week04_mcp_port() -> int:
    load_project_env()
    raw_port = os.getenv("KANAMATE_WEEK04_MCP_PORT", str(DEFAULT_WEEK04_MCP_PORT))
    try:
        # 환경 변수는 문자열이므로 HTTP client/server에 쓰기 전에 정수로 바꾼다.
        return int(raw_port)
    except ValueError as exc:
        raise RuntimeError("KANAMATE_WEEK04_MCP_PORT는 정수여야 합니다.") from exc


def week04_mcp_url() -> str:
    # MultiServerMCPClient가 접속할 streamable-http endpoint 주소다.
    return f"http://{week04_mcp_host()}:{week04_mcp_port()}/mcp"


def resolve_calendar_db_path(db_path: str | pathlib.Path | None = None) -> pathlib.Path:
    # client와 server가 같은 DB path를 봐야 payload와 SQLite row를 비교할 수 있다.
    load_project_env()
    configured_path = db_path or os.getenv("KANAMATE_WEEK04_DB_PATH") or DEFAULT_WEEK04_DB_PATH
    return pathlib.Path(configured_path).resolve()


def initialize_calendar_db(db_path: str | pathlib.Path | None = None, reset: bool = False) -> pathlib.Path:
    """Create the teaching SQLite calendar table and optionally clear old rows."""
    target_path = resolve_calendar_db_path(db_path)
    # tmp 폴더가 아직 없어도 SQLite 파일을 만들 수 있게 부모 폴더를 먼저 만든다.
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target_path) as conn:
        # event_id를 unique로 두어 같은 날짜/시간 실습을 다시 실행해도 row가 중복되지 않는다.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                members_json TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        if reset:
            # reset=True는 실습을 처음부터 다시 보기 위해 기존 row를 지우는 옵션이다.
            conn.execute("DELETE FROM calendar_events")
        conn.commit()
    return target_path


def load_saved_calendar_events(db_path: str | pathlib.Path | None = None) -> list[dict[str, Any]]:
    """Return saved SQLite calendar rows in a JSON-friendly shape."""
    # MCP 서버가 저장한 결과를 학생이 바로 비교할 수 있도록 dict 리스트로 변환한다.
    target_path = initialize_calendar_db(db_path)
    with sqlite3.connect(target_path) as conn:
        # sqlite3.Row를 쓰면 row["event_id"]처럼 컬럼명으로 읽을 수 있다.
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT event_id, title, date, start_time, members_json, status
            FROM calendar_events
            ORDER BY id
            """
        ).fetchall()
    return [
        {
            "event_id": row["event_id"],
            "title": row["title"],
            "date": row["date"],
            "start_time": row["start_time"],
            "members_json": row["members_json"],
            # DB에는 문자열로 저장하지만, UI에서는 list로도 바로 보이게 역직렬화한다.
            "members": json.loads(row["members_json"]),
            "status": row["status"],
        }
        for row in rows
    ]


def run_async(coro):
    """Run an async MCP call from both notebooks and plain Python."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # 일반 Python 스크립트에서는 실행 중인 event loop가 없으므로 바로 asyncio.run을 쓴다.
        return asyncio.run(coro)

    box: dict[str, Any] = {}

    def runner() -> None:
        # Jupyter는 이미 event loop가 있어 새 thread에서 async MCP 호출을 실행한다.
        # 같은 thread에서 asyncio.run을 다시 호출하면 오류가 나므로 thread를 분리한다.
        try:
            box["value"] = asyncio.run(coro)
        except Exception as exc:
            box["error"] = exc

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["value"]


def write_calendar_mcp_server(
    include_create_event: bool = False,
    db_path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """Prepare local storage and return the standalone MCP server path.

    Kept for older notebook/import compatibility. The server itself now lives in
    week04_mcp_server.py and must be started in a separate terminal.
    """
    # 예전 수업 코드의 함수명은 유지하되, 이제는 "서버 파일 생성" 대신 DB 준비만 한다.
    initialize_calendar_db(db_path, reset=include_create_event)
    return WEEK04_MCP_SERVER_PATH


def make_calendar_mcp_client(server_url: str | None = None) -> MultiServerMCPClient:
    # stdio가 아니라 이미 실행 중인 HTTP MCP endpoint에 연결한다.
    target_url = server_url or week04_mcp_url()
    return MultiServerMCPClient(
        {
            "calendar": {
                # "calendar"는 이 client 안에서 서버를 구분하는 별칭이다.
                "url": target_url,
                "transport": "streamable_http",
            }
        }
    )


def load_calendar_mcp_tools(server_url: str | None = None) -> list[Any]:
    # get_tools도 async API라 run_async로 감싸 plain Python/Jupyter 모두에서 쓰게 한다.
    target_url = server_url or week04_mcp_url()
    client = make_calendar_mcp_client(target_url)
    try:
        # 서버에서 노출한 calendar_check_availability/calendar_create_event tool을 읽는다.
        return run_async(client.get_tools(server_name="calendar"))
    except Exception as exc:
        raise RuntimeError(
            "4주차 MCP 서버에 연결할 수 없습니다. 먼저 다른 터미널에서 "
            f"`python week04_mcp_server.py`를 실행하세요. MCP URL: {target_url}"
        ) from exc


def mcp_tool_by_name(tools: list[Any], name: str) -> Any:
    # 수업 코드에서는 tool 이름으로 꺼내는 편이 trace와 비교하기 쉽다.
    for tool_item in tools:
        if getattr(tool_item, "name", None) == name:
            return tool_item
    raise KeyError(f"MCP tool을 찾을 수 없습니다: {name}")


def parse_mcp_tool_result(content: Any) -> dict[str, Any]:
    """Convert MCP content blocks or JSON strings into a dict payload."""
    # MCP adapter/버전에 따라 결과가 dict, JSON string, content block으로 올 수 있다.
    if isinstance(content, dict):
        # 이미 dict이면 추가 변환 없이 그대로 payload로 사용한다.
        return content
    if isinstance(content, list):
        # content block 리스트인 경우 text block을 찾아 JSON으로 읽는다.
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return json.loads(item["text"])
            if hasattr(item, "text"):
                return json.loads(item.text)
        raise ValueError(f"MCP text content를 찾지 못했습니다: {content}")
    if isinstance(content, str):
        # 일부 adapter는 tool 결과를 JSON 문자열로 바로 넘긴다.
        return json.loads(content)
    raise TypeError(f"지원하지 않는 MCP tool result 형식입니다: {type(content)}")


def run_mcp_event_request(
    request: str,
    agent: Any | None = None,
    mcp_tools: list[Any] | None = None,
    db_path: str | pathlib.Path | None = None,
) -> dict[str, Any]:
    """Run a schedule creation request through the real local MCP server."""
    # 핵심 흐름: MCP tool 로드 -> agent async 실행 -> MCP payload 파싱 -> SQLite row 비교.
    # TODO 문제 2: 실행 중인 MCP 서버에서 tool 목록을 로드한다.
    # 모범 답안 2:
    if agent is None:
        # include_create_event=True는 DB를 초기화해 같은 실습을 반복하기 쉽게 한다.
        write_calendar_mcp_server(include_create_event=True, db_path=db_path)
        mcp_tools = mcp_tools or load_calendar_mcp_tools()

    # TODO 문제 3: MCP tool로 agent를 만들고 async request를 실행한다.
    # 모범 답안 3:
    mcp_agent = agent or create_agent(
        model=make_model(700),
        tools=mcp_tools or [],
        system_prompt=(
            "가능 시간 조회는 calendar_check_availability를, 일정 생성이나 확정 요청은 "
            "calendar_create_event MCP 도구를 호출한 뒤 답한다."
        ),
    )
    # MCP StructuredTool은 sync invoke를 지원하지 않으므로 agent도 ainvoke로 실행한다.
    result = run_async(mcp_agent.ainvoke({"messages": [{"role": "user", "content": request}]}))
    trace = extract_tool_trace(result)

    # TODO 문제 4: trace에서 MCP 서버 payload를 꺼낸다.
    # 모범 답안 4:
    created_event = None
    for event in trace:
        # 일정 생성 여부는 tool_call이 아니라 서버가 돌려준 tool_result payload로 확인한다.
        if event.get("event") == "tool_result" and event.get("tool_name") == "calendar_create_event":
            created_event = parse_mcp_tool_result(event["content"])
            break

    # TODO 문제 5: 같은 요청이 SQLite row에도 저장됐는지 함께 보여준다.
    # 모범 답안 5:
    return {
        # created_event는 MCP 응답, saved_events는 DB에서 다시 읽은 검증 결과다.
        "answer": final_text(result),
        "trace": trace,
        "created_event": created_event,
        "saved_events": load_saved_calendar_events(db_path),
    }


def run_ui(request: str):
    # UI에서는 답변, MCP payload, SQLite row, trace를 한 화면에서 비교한다.
    try:
        result = run_mcp_event_request(request)
        return result["answer"], result["created_event"], result["saved_events"], result["trace"]
    except Exception as exc:
        return str(exc), {}, [], []


def append_user_message(request: str, history: list[dict[str, str]] | None):
    # 빠른 callback: MCP 서버/agent 실행 전에 사용자 메시지를 먼저 화면에 올린다.
    history = list(history or [])
    cleaned_request = request.strip()
    if not cleaned_request:
        return history, history, ""
    history.append({"role": "user", "content": cleaned_request})
    return history, history, ""


def run_chat_response(history: list[dict[str, str]] | None):
    # 느린 callback: 마지막 사용자 메시지로 MCP 요청을 처리하고 assistant 답변을 붙인다.
    history = list(history or [])
    if not history or history[-1].get("role") != "user":
        return history, history, {}, [], []

    request = history[-1]["content"]
    answer, created_event, saved_events, trace = run_ui(request)
    history.append({"role": "assistant", "content": answer})
    return history, history, created_event, saved_events, trace


def clear_chat():
    return [], [], "", {}, [], []


def create_demo() -> gr.Blocks:
    # 서버 연결은 버튼을 누를 때만 일어나므로 create_demo 자체는 가볍게 import된다.
    with gr.Blocks(title="KanaMate Week 4", fill_width=True, fill_height=True) as demo:
        with gr.Column(scale=1, min_width=0):
            gr.Markdown("# KanaMate Week 4")
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
                    value="민수와 지아의 발표 리허설을 2026-04-24 15:00 일정으로 생성해줘",
                    scale=8,
                    min_width=0,
                )
                run_button = gr.Button("전송", variant="primary", scale=1, min_width=96)
                clear_button = gr.Button("초기화", scale=1, min_width=96)
            with gr.Accordion("실행 상세", open=False):
                event_json = gr.JSON(label="MCP 서버 생성 payload")
                saved_json = gr.JSON(label="SQLite 저장 row")
                trace_json = gr.JSON(label="MCP Tool Trace")

        chat_outputs = [chatbot, history_state, request, event_json, saved_json, trace_json]
        user_outputs = [chatbot, history_state, request]
        response_outputs = [chatbot, history_state, event_json, saved_json, trace_json]
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
