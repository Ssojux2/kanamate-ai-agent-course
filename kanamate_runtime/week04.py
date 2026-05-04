"""Week 4 MCP server and client helpers."""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import tempfile
import textwrap
import threading
from typing import Any

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from kanamate_runtime.common import make_model

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
        except Exception as exc:  # pragma: no cover - re-raised in caller
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


def build_mcp_event_agent(mcp_tools: list[Any], max_tokens: int = 700):
    return create_agent(
        model=make_model(max_tokens),
        tools=mcp_tools,
        system_prompt=(
            "가능 시간 조회는 calendar_check_availability를, 일정 생성이나 확정 요청은 "
            "calendar_create_event MCP 도구를 호출한 뒤 답한다."
        ),
    )

