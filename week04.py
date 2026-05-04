"""Week 4 KanaMate assignment and Gradio UI."""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys
import tempfile
import textwrap
import threading
from typing import Any

import gradio as gr
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
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
# Week 4. Real MCP tool call
# ---------------------------------------------------------------------------


mcp_server_path = pathlib.Path(tempfile.gettempdir()) / "kanamate_calendar_mcp_server.py"


def run_async(coro):
    """Run an async MCP call from both notebooks and plain Python."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    box: dict[str, Any] = {}

    def runner() -> None:
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


def write_calendar_mcp_server(include_create_event: bool = False) -> pathlib.Path:
    """Write a small real MCP server that exposes calendar tools over stdio."""
    create_event_tool = (
        '''

@mcp.tool()
def calendar_create_event(title: str, date: str, start_time: str, members: list[str]) -> dict:
    '그룹 일정을 생성한다.'
    return {
        'server': 'kanamate-calendar',
        'tool': 'calendar.create_event',
        'arguments': {'title': title, 'date': date, 'start_time': start_time, 'members': members},
        'event_id': f"event-{date}-{start_time}".replace(':', ''),
        'status': 'created',
    }
'''
        if include_create_event
        else ""
    )

    server_code = r'''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('kanamate-calendar')

@mcp.tool()
def calendar_check_availability(members: list[str], date: str) -> dict:
    '그룹 멤버의 가능한 시간을 조회한다.'
    return {
        'server': 'kanamate-calendar',
        'tool': 'calendar.check_availability',
        'arguments': {'members': members, 'date': date},
        'available_slots': [f'{date} 10:00', f'{date} 15:00'],
    }
# CREATE_EVENT_TOOL

if __name__ == '__main__':
    mcp.run(transport='stdio')
'''.replace("# CREATE_EVENT_TOOL", create_event_tool)
    mcp_server_path.write_text(textwrap.dedent(server_code).lstrip(), encoding="utf-8")
    return mcp_server_path


def make_calendar_mcp_client(server_path: pathlib.Path) -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "calendar": {
                "command": sys.executable,
                "args": [str(server_path)],
                "transport": "stdio",
            }
        }
    )


def load_calendar_mcp_tools() -> list[Any]:
    client = make_calendar_mcp_client(mcp_server_path)
    return run_async(client.get_tools(server_name="calendar"))


def parse_mcp_tool_result(content: Any) -> dict[str, Any]:
    """Convert MCP content blocks or JSON strings into a dict payload."""
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return json.loads(item["text"])
            if hasattr(item, "text"):
                return json.loads(item.text)
        raise ValueError(f"MCP text content를 찾지 못했습니다: {content}")
    if isinstance(content, str):
        return json.loads(content)
    raise TypeError(f"지원하지 않는 MCP tool result 형식입니다: {type(content)}")


def build_week04_agent(mcp_tools: list[Any], max_tokens: int = 700):
    return create_agent(
        model=make_model(max_tokens),
        tools=mcp_tools,
        system_prompt=(
            "가능 시간 조회는 calendar_check_availability를, 일정 생성이나 확정 요청은 "
            "calendar_create_event MCP 도구를 호출한 뒤 답한다."
        ),
    )


def run_mcp_event_request(
    request: str,
    agent: Any | None = None,
    mcp_tools: list[Any] | None = None,
) -> dict[str, Any]:
    """Run a schedule creation request through the real local MCP server."""
    # TODO 1: calendar_create_event가 포함된 MCP 서버 파일을 쓰고 tool 목록을 로드한다.
    # 모범 답안 1(강의자료 테스트용)
    if agent is None:
        write_calendar_mcp_server(include_create_event=True)
        mcp_tools = mcp_tools or load_calendar_mcp_tools()

    # TODO 2: MCP 서버에서 로드한 tool로 agent를 만들고 request를 실행한다.
    # 모범 답안 2(강의자료 테스트용)
    mcp_agent = agent or build_week04_agent(mcp_tools or [])
    result = mcp_agent.invoke({"messages": [{"role": "user", "content": request}]})
    trace = extract_tool_trace(result)

    # TODO 3: trace에서 calendar_create_event MCP tool result를 찾아 payload로 파싱한다.
    # 모범 답안 3(강의자료 테스트용)
    created_event = None
    for event in trace:
        if event.get("event") == "tool_result" and event.get("tool_name") == "calendar_create_event":
            created_event = parse_mcp_tool_result(event["content"])

    return {"answer": final_text(result), "trace": trace, "created_event": created_event}


def run_ui(request: str):
    try:
        result = run_mcp_event_request(request)
        return result["answer"], result["created_event"], result["trace"]
    except Exception as exc:
        return str(exc), {}, []


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 4") as demo:
        gr.Markdown("# Week 4 - Real MCP Server")
        request = gr.Textbox(label="요청", value="민수와 지아의 발표 리허설을 2026-04-24 15:00 일정으로 생성해줘")
        run_button = gr.Button("실행", variant="primary")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        event_json = gr.JSON(label="MCP 서버 생성 payload")
        trace_json = gr.JSON(label="MCP Tool Trace")
        run_button.click(run_ui, inputs=request, outputs=[answer, event_json, trace_json])
    return demo


if __name__ == "__main__":
    create_demo().launch()
