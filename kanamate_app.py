"""KanaMate weekly practice functions and a single Gradio UI.

Run:
    python kanamate_app.py
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys
import tempfile
import textwrap
import threading
import uuid
from typing import Any, Callable, Literal

import chromadb
import gradio as gr
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

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


# ---------------------------------------------------------------------------
# Week 3. RAG / Agentic RAG
# ---------------------------------------------------------------------------


DEFAULT_STUDENT_MEMORIES = [
    "프로젝트 발표는 2026-04-24 10:00에 민수와 지아가 함께 진행한다.",
    "카나메이트 UI에서는 채팅 답변과 tool trace를 함께 보여준다.",
]
memory_collection: Any | None = None


def reset_memory_collection(memories: list[str] | None = None) -> Any:
    global memory_collection
    source_memories = memories or DEFAULT_STUDENT_MEMORIES
    embedding_function = OpenAIEmbeddingFunction(
        api_key=require_openai_api_key(),
        model_name=openai_embedding_model_name(),
    )
    client = chromadb.Client(Settings(anonymized_telemetry=False))
    memory_collection = client.create_collection(
        name=f"kanamate_week3_{uuid.uuid4().hex[:8]}",
        embedding_function=embedding_function,
    )
    memory_collection.add(
        ids=[f"memory-{index + 1}" for index in range(len(source_memories))],
        documents=source_memories,
        metadatas=[{"source": "student_input"} for _ in source_memories],
    )
    return memory_collection


def get_memory_collection() -> Any:
    global memory_collection
    if memory_collection is None:
        memory_collection = reset_memory_collection()
    return memory_collection


def format_chroma_results(found: dict[str, Any]) -> list[dict[str, Any]]:
    ids = found.get("ids", [[]])[0]
    documents = found.get("documents", [[]])[0]
    distances = found.get("distances", [[]])[0]
    return [
        {"id": ids[index], "content": documents[index], "distance": distances[index]}
        for index in range(len(ids))
    ]


def search_memory_hits(
    query: str,
    top_k: int = 2,
    collection: Any | None = None,
) -> list[dict[str, Any]]:
    """Return Chroma search results as a simple list of dictionaries."""
    target_collection = collection or get_memory_collection()

    # TODO 1: memory_collection.query로 검색한다.
    # 모범 답안 1(강의자료 테스트용)
    found = target_collection.query(query_texts=[query], n_results=top_k)

    # TODO 2: ids/documents/distances의 첫 번째 결과 묶음을 꺼낸다.
    # 모범 답안 2(강의자료 테스트용)
    hits = format_chroma_results(found)

    # TODO 3: 각 hit을 {id, content, distance} 모양으로 바꾼다.
    # 모범 답안 3(강의자료 테스트용)
    return hits


def build_week03_agent(search_hits: Callable[[str, int], list[dict[str, Any]]], max_tokens: int = 700):
    @tool("search_memory", description="학생이 입력한 메모를 검색하고 단순한 hit 리스트로 돌려준다.")
    def search_memory_with_helper(query: str, top_k: int = 2) -> str:
        """Search student memory with the practice helper."""
        return json.dumps({"hits": search_hits(query, top_k)}, ensure_ascii=False)

    return create_agent(
        model=make_model(max_tokens),
        tools=[search_memory_with_helper],
        system_prompt="저장된 메모가 필요한 질문이면 search_memory 도구를 호출한 뒤, 찾은 근거를 바탕으로 답한다.",
    )


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


# ---------------------------------------------------------------------------
# Week 5-6. Sub-agent tools and harnesses
# ---------------------------------------------------------------------------


def _personal_create_schedule(title: str, date: str, start_time: str) -> str:
    """Create a personal schedule."""
    return json.dumps(
        {"ok": True, "schedule": {"title": title, "date": date, "start_time": start_time}},
        ensure_ascii=False,
    )


def _group_confirm_slot(topic: str, selected_slot: str, members: list[str], reason: str) -> str:
    """Confirm a group schedule slot."""
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


personal_create_schedule_tool = tool(
    "personal_create_schedule",
    description="개인 일정을 생성한다.",
)(_personal_create_schedule)
group_confirm_slot_tool = tool(
    "group_confirm_slot",
    description="그룹 일정 시간을 확정한다.",
)(_group_confirm_slot)
memory_save_tool = tool(
    "memory_save",
    description="사용자 메모를 저장한다.",
)(_memory_save)


def build_week05_nana_agent(max_tokens: int = 600):
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
    return create_agent(
        model=make_model(max_tokens),
        tools=[group_confirm_slot_tool],
        system_prompt="너는 그룹 메이트 카나다. 멤버 응답에서 모두 가능한 시간을 찾으면 group_confirm_slot 도구를 호출한다.",
    )


def _week05_delegate_to_nana(request: str) -> str:
    """Delegate a personal request to Nana sub-agent."""
    agent_result = build_week05_nana_agent().invoke({"messages": [{"role": "user", "content": request}]})
    return json.dumps(
        {"agent": "nana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


def _week05_delegate_to_kana(request: str, member_replies: str) -> str:
    """Delegate a group coordination request to Kana sub-agent."""
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
week05_delegate_to_kana = tool(
    "kana_agent",
    description="그룹 일정 조율 요청과 멤버 응답을 카나 sub-agent에게 위임한다.",
)(_week05_delegate_to_kana)


def build_week05_supervisor(max_tokens: int = 900):
    return create_agent(
        model=make_model(max_tokens),
        tools=[week05_delegate_to_nana, week05_delegate_to_kana],
        system_prompt=(
            "너는 카나메이트 supervisor다. 개인 일정 요청은 nana_agent tool을 호출하고, "
            "그룹 일정 조율 요청은 kana_agent tool을 호출한다. 직접 처리하지 말고 반드시 "
            "적절한 sub-agent tool을 호출한 뒤 그 결과를 학생에게 요약한다."
        ),
    )


def delegated_agent_from_trace(agent_result: dict[str, Any]) -> str:
    for event in extract_tool_trace(agent_result):
        if event.get("event") == "tool_call" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return event["tool_name"].replace("_agent", "")
    return "unknown"


def delegated_payload_from_trace(agent_result: dict[str, Any]) -> dict[str, Any]:
    for event in extract_tool_trace(agent_result):
        if event.get("event") == "tool_result" and event.get("tool_name") in {"nana_agent", "kana_agent"}:
            return json.loads(event["content"])
    return {}


golden_cases = [
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
    # TODO 1: member_replies가 있으면 요청과 멤버 응답을 함께 보낸다.
    # 모범 답안 1(강의자료 테스트용)
    content = case["request"]
    if case.get("member_replies"):
        content = f"요청: {case['request']}\n멤버 응답:\n{case['member_replies']}"

    # TODO 2: supervisor trace에서 선택된 agent를 읽는다.
    # 모범 답안 2(강의자료 테스트용)
    supervisor = supervisor_agent or build_week05_supervisor()
    result = supervisor.invoke({"messages": [{"role": "user", "content": content}]})
    selected_agent = delegated_agent_from_trace(result)
    delegate_payload = delegated_payload_from_trace(result)

    # TODO 3: sub-agent 내부 trace의 tool 이름 목록을 만든다.
    # 모범 답안 3(강의자료 테스트용)
    inner_tool_names = [
        event["tool_name"]
        for event in delegate_payload.get("trace", [])
        if event.get("event") == "tool_call"
    ]

    return {
        "name": case["name"],
        "expected_agent": case["expected_agent"],
        "selected_agent": selected_agent,
        "expected_inner_tool": case["expected_inner_tool"],
        "inner_tool_names": inner_tool_names,
        "answer": final_text(result),
        "trace": extract_tool_trace(result),
        "delegate_payload": delegate_payload,
    }


def build_week06_nana_agent(max_tokens: int = 700):
    return create_agent(
        model=make_model(max_tokens),
        tools=[personal_create_schedule_tool, memory_save_tool],
        system_prompt=(
            "너는 나나다. 오늘은 2026-04-23이다. 상대 날짜는 이 날짜 기준으로 YYYY-MM-DD로 바꾼다. "
            "개인 일정이나 메모 요청에 필요한 도구를 호출한다."
        ),
    )


def build_week06_kana_agent(max_tokens: int = 800):
    return create_agent(
        model=make_model(max_tokens),
        tools=[group_confirm_slot_tool],
        system_prompt="너는 카나다. 그룹 응답에서 공통 가능 시간을 찾으면 group_confirm_slot 도구를 호출한다.",
    )


def _week06_delegate_to_nana(request: str) -> str:
    """Delegate a personal request to Nana sub-agent."""
    agent_result = build_week06_nana_agent().invoke({"messages": [{"role": "user", "content": request}]})
    return json.dumps(
        {"agent": "nana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


def _week06_delegate_to_kana(request: str, member_replies: str) -> str:
    """Delegate a group coordination request to Kana sub-agent."""
    message = f"요청: {request}\n그룹 응답:\n{member_replies}"
    agent_result = build_week06_kana_agent().invoke({"messages": [{"role": "user", "content": message}]})
    return json.dumps(
        {"agent": "kana", "answer": final_text(agent_result), "trace": extract_tool_trace(agent_result)},
        ensure_ascii=False,
    )


week06_delegate_to_nana = tool(
    "nana_agent",
    description="개인 일정이나 메모 요청을 나나 sub-agent에게 위임한다.",
)(_week06_delegate_to_nana)
week06_delegate_to_kana = tool(
    "kana_agent",
    description="그룹 일정 조율 요청과 멤버 응답을 카나 sub-agent에게 위임한다.",
)(_week06_delegate_to_kana)


def make_supervisor(mode: str = "auto"):
    if mode == "personal":
        tools = [week06_delegate_to_nana]
        prompt = "너는 카나메이트 supervisor다. 사용자가 personal 모드를 선택했으므로 nana_agent tool을 호출한다."
    elif mode == "group":
        tools = [week06_delegate_to_kana]
        prompt = "너는 카나메이트 supervisor다. 사용자가 group 모드를 선택했으므로 kana_agent tool을 호출한다."
    else:
        tools = [week06_delegate_to_nana, week06_delegate_to_kana]
        prompt = (
            "너는 카나메이트 supervisor다. 개인 일정/메모 요청은 nana_agent tool을 호출하고, "
            "그룹 일정 조율 요청은 kana_agent tool을 호출한다. 직접 처리하지 말고 반드시 "
            "적절한 sub-agent tool을 호출한다."
        )
    return create_agent(model=make_model(1000), tools=tools, system_prompt=prompt)


def run_live_flow(student_request: str, member_replies: str = "", mode: str = "auto") -> dict[str, Any]:
    supervisor = make_supervisor(mode)
    content = (
        f"요청: {student_request}\n그룹 응답:\n{member_replies}"
        if mode in {"auto", "group"}
        else student_request
    )
    supervisor_result = supervisor.invoke({"messages": [{"role": "user", "content": content}]})
    return {
        "selected_agent": delegated_agent_from_trace(supervisor_result),
        "answer": final_text(supervisor_result),
        "trace": extract_tool_trace(supervisor_result),
        "delegate_payload": delegated_payload_from_trace(supervisor_result),
    }


practice_cases = [
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
        # TODO 1: case의 mode/request/member_replies로 run_live_flow를 호출한다.
        # 모범 답안 1(강의자료 테스트용)
        result = runner(case["request"], case.get("member_replies", ""), case.get("mode", "auto"))

        # TODO 2: delegate_payload 내부 trace에서 실제 sub-agent tool 이름을 모은다.
        # 모범 답안 2(강의자료 테스트용)
        inner_tool_names = [
            event["tool_name"]
            for event in result["delegate_payload"].get("trace", [])
            if event.get("event") == "tool_call"
        ]

        # TODO 3: 기대 agent/tool과 실제 결과를 한 report에 담는다.
        # 모범 답안 3(강의자료 테스트용)
        reports.append(
            {
                "name": case["name"],
                "expected_agent": case["expected_agent"],
                "selected_agent": result["selected_agent"],
                "expected_inner_tool": case["expected_inner_tool"],
                "inner_tool_names": inner_tool_names,
                "passed": (
                    case["expected_agent"] == result["selected_agent"]
                    and case["expected_inner_tool"] in inner_tool_names
                ),
                "answer": result["answer"],
                "trace": result["trace"],
                "delegate_payload": result["delegate_payload"],
            }
        )
    return reports


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------


def week01_ui(request: str):
    try:
        result = run_student_schedule_request(request)
        return (
            f"{result['answer']}\n\n{result['list_answer']}",
            {"created_schedule": result["created_schedule"], "schedules": result["schedules"]},
            {"create_trace": result["trace"], "list_trace": result["list_trace"]},
        )
    except Exception as exc:
        return str(exc), {}, {}


def week02_ui(request: str):
    try:
        response = run_student_structured_request(request)
        return response.model_dump()
    except Exception as exc:
        return {"error": str(exc)}


def week03_ui(question: str, memories_text: str):
    try:
        memories = [line.strip() for line in memories_text.splitlines() if line.strip()]
        if not memories:
            return "검색할 메모를 한 줄 이상 입력하세요.", [], []
        reset_memory_collection(memories)
        hits = search_memory_hits(question, top_k=min(2, len(memories)))
        rag_agent = build_week03_agent(search_memory_hits)
        result = rag_agent.invoke({"messages": [{"role": "user", "content": question}]})
        return final_text(result), hits, extract_tool_trace(result)
    except Exception as exc:
        return str(exc), [], []


def week04_ui(request: str):
    try:
        result = run_mcp_event_request(request)
        return result["answer"], result["created_event"], result["trace"]
    except Exception as exc:
        return str(exc), {}, []


def week05_ui(request: str, member_replies: str):
    try:
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


def week06_live_ui(student_request: str, member_replies: str, mode: str):
    try:
        result = run_live_flow(student_request, member_replies, mode)
        return (
            result["answer"],
            {"selected_agent": result["selected_agent"], "delegate_payload": result["delegate_payload"]},
            result["trace"],
        )
    except Exception as exc:
        return str(exc), {}, []


def week06_suite_ui():
    try:
        reports = run_practice_suite(practice_cases)
        return [
            {
                "name": report["name"],
                "expected_agent": report["expected_agent"],
                "selected_agent": report["selected_agent"],
                "expected_inner_tool": report["expected_inner_tool"],
                "inner_tool_names": report["inner_tool_names"],
                "passed": report["passed"],
            }
            for report in reports
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate AI Agent Course") as demo:
        gr.Markdown("# KanaMate AI Agent Course")

        with gr.Tab("Week 1"):
            w1_request = gr.Textbox(label="요청", value="내일 10시에 민수와 회의 일정 잡아줘")
            w1_run = gr.Button("실행", variant="primary")
            w1_clear = gr.Button("일정 초기화")
            w1_answer = gr.Textbox(label="모델 최종 답변", lines=5)
            w1_result = gr.JSON(label="완성 결과")
            w1_trace = gr.JSON(label="Tool Trace")
            w1_run.click(week01_ui, inputs=w1_request, outputs=[w1_answer, w1_result, w1_trace])
            w1_clear.click(lambda: (reset_schedules(), "일정을 초기화했습니다.")[1], outputs=w1_answer)

        with gr.Tab("Week 2"):
            w2_request = gr.Textbox(label="요청", value="발표 30분 전에 알려줘")
            w2_run = gr.Button("구조화 실행", variant="primary")
            w2_result = gr.JSON(label="Pydantic Response")
            w2_run.click(week02_ui, inputs=w2_request, outputs=w2_result)

        with gr.Tab("Week 3"):
            w3_question = gr.Textbox(label="질문", value="카나메이트 UI에서는 무엇을 함께 보여줘?")
            w3_memories = gr.Textbox(
                label="메모",
                lines=4,
                value=(
                    "프로젝트 발표는 2026-04-24 10:00에 민수와 지아가 함께 진행한다.\n"
                    "카나메이트 UI에서는 채팅 답변과 tool trace를 함께 보여준다."
                ),
            )
            w3_run = gr.Button("검색 Agent 실행", variant="primary")
            w3_answer = gr.Textbox(label="모델 최종 답변", lines=5)
            w3_hits = gr.JSON(label="검색 hit 리스트")
            w3_trace = gr.JSON(label="검색 Tool Trace")
            w3_run.click(week03_ui, inputs=[w3_question, w3_memories], outputs=[w3_answer, w3_hits, w3_trace])

        with gr.Tab("Week 4"):
            w4_request = gr.Textbox(
                label="요청",
                value="민수와 지아의 발표 리허설을 2026-04-24 15:00 일정으로 생성해줘",
            )
            w4_run = gr.Button("실행", variant="primary")
            w4_answer = gr.Textbox(label="모델 최종 답변", lines=5)
            w4_event = gr.JSON(label="MCP 서버 생성 payload")
            w4_trace = gr.JSON(label="MCP Tool Trace")
            w4_run.click(week04_ui, inputs=w4_request, outputs=[w4_answer, w4_event, w4_trace])

        with gr.Tab("Week 5"):
            w5_request = gr.Textbox(label="요청", value="팀 회의 시간을 조율해줘")
            w5_member_replies = gr.Textbox(
                label="멤버 응답",
                lines=4,
                value="민수: 2026-04-24 10:00 가능\n지아: 2026-04-24 10:00 가능",
            )
            w5_run = gr.Button("실행", variant="primary")
            w5_answer = gr.Textbox(label="모델 최종 답변", lines=5)
            w5_selected = gr.JSON(label="선택된 Agent와 내부 Tool")
            w5_trace = gr.JSON(label="Supervisor/Sub-Agent Tool Trace")
            w5_run.click(
                week05_ui,
                inputs=[w5_request, w5_member_replies],
                outputs=[w5_answer, w5_selected, w5_trace],
            )

        with gr.Tab("Week 6"):
            with gr.Tab("Live Flow"):
                w6_mode = gr.Radio(["auto", "personal", "group"], value="auto", label="모드")
                w6_request = gr.Textbox(label="요청", value="팀 멤버들과 발표 리허설 시간을 조율해줘")
                w6_member_replies = gr.Textbox(
                    label="멤버 응답",
                    lines=4,
                    value="민수: 2026-04-24 15:00 가능\n지아: 2026-04-24 15:00 가능",
                )
                w6_run = gr.Button("실행", variant="primary")
                w6_answer = gr.Textbox(label="모델 최종 답변", lines=5)
                w6_payload = gr.JSON(label="선택된 Agent와 delegate payload")
                w6_trace = gr.JSON(label="Supervisor Trace")
                w6_run.click(
                    week06_live_ui,
                    inputs=[w6_request, w6_member_replies, w6_mode],
                    outputs=[w6_answer, w6_payload, w6_trace],
                )

            with gr.Tab("Golden Scenario"):
                w6_suite_run = gr.Button("시나리오 실행", variant="primary")
                w6_suite = gr.JSON(label="시나리오 결과")
                w6_suite_run.click(week06_suite_ui, outputs=w6_suite)

    return demo


if __name__ == "__main__":
    create_demo().launch()

