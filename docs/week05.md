# 5주차. MCP 서버 Tool Call 분리하기

## 학습 목표

- MCP를 agent 코드 밖에서 tool을 제공하는 서버 구조로 설명한다.
- MCP 서버가 반환해야 하는 tool payload 모양을 읽는다.
- 단일 agent가 MCP tool을 호출했는지 trace와 payload로 확인하는 기준을 세운다.

## 핵심 개념

5주차는 4주차의 SQLite 저장소와 분리해서 MCP 자체에 집중한다. 실제 MCP server/client 문제 코드는 별도 문제 repo에서 작성하고, 이 레포의 노트북은 tool schema, payload, trace 관찰 기준을 정리한다.

Agent는 Python 함수를 직접 받지 않고 MCP 서버에서 읽어온 tool을 사용한다. 이번 주의 성공 기준은 SQLite row가 아니라 MCP payload다. 서버가 어떤 arguments를 받았고 어떤 `event_id`와 `status`를 반환했는지 확인한다.

## 실습 흐름

1. `notebook/05_카나의_자율_약속_잡기.ipynb`에서 MCP payload shape를 확인한다.
2. `calendar_check_availability` payload와 `calendar_create_event` payload의 공통 필드를 비교한다.
3. 일정 생성 payload의 `arguments`, `event_id`, `status`를 확인한다.
4. 예시 trace에서 `tool_call`과 `tool_result`를 구분한다.
5. 실제 문제 repo에서 MCP 서버를 붙일 때 어떤 값을 검증해야 하는지 정리한다.

## 관찰할 trace/payload

- `calendar_check_availability` tool call: 가능 시간 조회 요청인지
- `calendar_create_event` tool call: 일정 생성 요청인지
- `arguments`: MCP 서버가 받은 `title`, `date`, `start_time`, `members`
- `event_id`: MCP 서버가 생성한 일정 식별 값
- `status`: MCP 서버 tool 실행 결과
- `mcp_payload`: MCP tool result를 JSON으로 해석한 값

## 확인 질문

1. Python 함수 tool과 MCP tool은 어디에서 tool 목록을 가져온다는 점이 다른가?
2. MCP 서버를 agent 코드와 분리하면 어떤 장점이 있는가?
3. MCP payload에서 사람이 반드시 확인해야 할 필드는 무엇인가?
4. 실제 문제 repo에서 MCP tool을 agent에 연결할 때 어떤 trace를 먼저 봐야 하는가?

## 작은 응용 과제

가능 시간 조회 payload와 일정 생성 payload에서 공통 필드와 생성 전용 필드를 나눠 본다.
