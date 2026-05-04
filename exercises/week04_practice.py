"""Week 4 practice: run a real MCP event-creation request."""

from __future__ import annotations

from typing import Any

from kanamate_runtime.common import extract_tool_trace, final_text
from kanamate_runtime.week04 import (
    build_mcp_event_agent,
    load_calendar_mcp_tools,
    parse_mcp_tool_result,
    write_calendar_mcp_server,
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
    mcp_agent = agent or build_mcp_event_agent(mcp_tools or [])
    result = mcp_agent.invoke({"messages": [{"role": "user", "content": request}]})
    trace = extract_tool_trace(result)

    # TODO 3: trace에서 calendar_create_event MCP tool result를 찾아 payload로 파싱한다.
    # 모범 답안 3(강의자료 테스트용)
    created_event = None
    for event in trace:
        if event.get("event") == "tool_result" and event.get("tool_name") == "calendar_create_event":
            created_event = parse_mcp_tool_result(event["content"])

    return {"answer": final_text(result), "trace": trace, "created_event": created_event}

