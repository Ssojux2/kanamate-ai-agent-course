"""Standalone Week 4 KanaMate MCP server."""

from __future__ import annotations

import json
import os
import pathlib
import sqlite3

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
# 이 파일은 "tool 제공자" 역할만 한다. week04.py는 이 서버에 요청하는 client다.
DEFAULT_WEEK04_DB_PATH = PROJECT_ROOT / "tmp" / "week04_calendar.sqlite3"
DEFAULT_WEEK04_MCP_HOST = "127.0.0.1"
DEFAULT_WEEK04_MCP_PORT = 8004


def load_server_env() -> None:
    """Load optional repo-root environment variables without overriding the shell."""
    load_dotenv(ENV_PATH, override=False)


def week04_mcp_host() -> str:
    # 기본은 로컬에서만 접근 가능한 주소다. 수업에서는 외부 공개가 필요 없다.
    load_server_env()
    return os.getenv("KANAMATE_WEEK04_MCP_HOST", DEFAULT_WEEK04_MCP_HOST)


def week04_mcp_port() -> int:
    load_server_env()
    raw_port = os.getenv("KANAMATE_WEEK04_MCP_PORT", str(DEFAULT_WEEK04_MCP_PORT))
    try:
        return int(raw_port)
    except ValueError as exc:
        raise RuntimeError("KANAMATE_WEEK04_MCP_PORT는 정수여야 합니다.") from exc


def resolve_calendar_db_path(db_path: str | pathlib.Path | None = None) -> pathlib.Path:
    # server가 실제로 저장할 SQLite 파일 위치를 한 곳에서 결정한다.
    load_server_env()
    configured_path = db_path or os.getenv("KANAMATE_WEEK04_DB_PATH") or DEFAULT_WEEK04_DB_PATH
    return pathlib.Path(configured_path).resolve()


DB_PATH = resolve_calendar_db_path()
# FastMCP가 아래 @mcp.tool 함수들을 MCP tool 목록으로 노출한다.
# 이 서버에서 제공하는 MCP tool:
# - calendar_check_availability: 멤버와 날짜를 받아 가능한 시간 후보를 돌려준다.
# - calendar_create_event: 일정 정보를 받아 SQLite에 그룹 일정 row를 저장한다.
mcp = FastMCP("kanamate-calendar", host=week04_mcp_host(), port=week04_mcp_port())


def ensure_calendar_db(reset: bool = False) -> pathlib.Path:
    """Create the teaching SQLite calendar table and optionally clear old rows."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # client가 payload의 event_id와 이 table row의 event_id를 비교한다.
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
            conn.execute("DELETE FROM calendar_events")
        conn.commit()
    return DB_PATH


@mcp.tool()
def calendar_check_availability(members: list[str], date: str) -> dict:
    """그룹 멤버의 가능한 시간을 조회한다."""
    # TODO 문제 1: MCP 서버가 제공하는 가능 시간 조회 tool payload를 만든다.
    # 모범 답안 1:
    # 실제 캘린더 연동 대신 고정 slot을 돌려 MCP 호출 흐름에 집중한다.
    return {
        "server": "kanamate-calendar",
        "tool": "calendar.check_availability",
        "arguments": {"members": members, "date": date},
        "available_slots": [f"{date} 10:00", f"{date} 15:00"],
    }


@mcp.tool()
def calendar_create_event(title: str, date: str, start_time: str, members: list[str]) -> dict:
    """그룹 일정을 생성한다."""
    # TODO 문제 2: 입력값으로 같은 요청을 다시 찾을 수 있는 event_id를 만든다.
    # 모범 답안 2:
    # 같은 입력은 같은 event_id를 만들게 해 SQLite row 비교가 쉬워진다.
    event_id = f"event-{date}-{start_time}".replace(":", "")
    members_json = json.dumps(members, ensure_ascii=False)
    ensure_calendar_db()
    with sqlite3.connect(DB_PATH) as conn:
        # TODO 문제 3: MCP tool 실행 결과를 SQLite calendar_events table에 저장한다.
        # 모범 답안 3:
        # INSERT OR REPLACE라 같은 실습을 반복해도 마지막 결과가 남는다.
        conn.execute(
            """
            INSERT OR REPLACE INTO calendar_events
                (event_id, title, date, start_time, members_json, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, title, date, start_time, members_json, "created"),
        )
        conn.commit()
    # TODO 문제 4: MCP client가 확인할 수 있는 payload를 반환한다.
    # 모범 답안 4:
    return {
        "server": "kanamate-calendar",
        "tool": "calendar.create_event",
        "arguments": {"title": title, "date": date, "start_time": start_time, "members": members},
        "event_id": event_id,
        "sqlite_path": str(DB_PATH),
        "status": "created",
    }


def main() -> None:
    # 서버를 먼저 띄운 뒤 notebook/week04.py가 http://host:port/mcp로 접속한다.
    ensure_calendar_db()
    host = week04_mcp_host()
    port = week04_mcp_port()
    print(f"Week 4 MCP server: http://{host}:{port}/mcp")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
