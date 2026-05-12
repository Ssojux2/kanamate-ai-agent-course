# 4주차. MCP 서버 Tool Call과 SQLite 저장 흐름 연결하기

## 학습 목표

- Python 함수 tool과 MCP tool의 차이를 tool 제공 위치 기준으로 설명한다.
- 별도 실행 중인 MCP HTTP 서버에서 tool 목록을 가져와 agent가 호출하는 흐름을 이해한다.
- MCP payload의 `event_id`와 SQLite 저장 row의 `event_id`를 비교한다.

## 핵심 개념

MCP는 도구를 agent 코드 안에 직접 넣는 대신, 외부 서버가 표준 방식으로 tool 목록과 실행 결과를 제공하게 해준다. 이번 주에는 `week04_mcp_server.py`가 로컬 FastMCP 서버로 동작하고, `week04.py`는 그 서버에 붙는 client/UI 역할을 한다.

일정 생성 tool인 `calendar_create_event`는 MCP payload를 반환하는 동시에 SQLite `calendar_events` table에 row를 저장한다. 따라서 성공 여부는 최종 답변이 아니라 MCP payload와 SQLite row를 같이 봐야 한다.

## 실습 흐름

1. 다른 터미널에서 MCP 서버를 먼저 실행한다.

```bash
python week04_mcp_server.py
```

2. `notebook/04_mcp_tool_call_gradio_ui.ipynb`에서 기본 endpoint `http://127.0.0.1:8004/mcp`를 확인한다.
3. `week04_mcp_server.py`의 `calendar_check_availability`, `calendar_create_event`가 어떤 payload를 반환하는지 본다.
4. `week04.py`에서 `load_calendar_mcp_tools`, `run_mcp_event_request`, `parse_mcp_tool_result` 흐름을 확인한다.
5. `python week04.py`로 Gradio UI를 실행해 MCP payload, SQLite row, trace를 한 화면에서 비교한다.

## 관찰할 trace/payload

- `calendar_create_event` tool call: agent가 MCP tool을 호출했는지
- MCP tool result content: 서버가 돌려준 원본 결과
- `parse_mcp_tool_result(...)` payload: UI와 검증 코드가 읽는 dict
- `event_id`: MCP payload와 SQLite row를 연결하는 값
- `arguments`: 서버가 받은 `title`, `date`, `start_time`, `members`
- `saved_events`: SQLite에서 다시 읽은 저장 row 목록

## 확인 질문

1. Python 함수 tool과 MCP tool은 어디에서 tool 목록을 가져온다는 점이 다른가?
2. MCP payload에서 사람이 반드시 확인해야 할 필드는 무엇인가?
3. SQLite 저장 row는 MCP payload와 어떤 값으로 연결되는가?
4. `streamable-http`, `FastMCP`, `MultiServerMCPClient` 중 지금 깊게 몰라도 되는 것은 무엇이며, 그래도 관찰해야 하는 결과는 무엇인가?
5. MCP tool을 agent에서 실행할 때 `invoke`가 아니라 `ainvoke`를 써야 하는 이유는 무엇인가?

## 작은 응용 과제

날짜와 멤버를 바꾼 요청을 실행한다. MCP payload의 `arguments`, `event_id`, SQLite row가 어떻게 달라지는지 비교한다.
