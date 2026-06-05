# 5주차. 카나가 지난 대화를 불러오다

**부제:** MCP SQLite 이전 대화 검색 tool

## 학습 목표

- 로컬 MCP server가 SQLite 대화/일정 DB를 외부 tool 서버처럼 제공하는 구조를 설명한다.
- `search_previous_conversations`, `load_conversation_messages`, `extract_schedules_from_history` payload를 구분한다.
- agent가 직접 DB를 읽지 않고 MCP tool을 통해 이전 대화의 일정과 참석자 정보를 검색하는 흐름을 검증한다.

## 핵심 개념

5주차는 SQLite DB 접근을 agent 내부 코드에서 분리한다. MCP server는 이전 대화와 일정 DB를 읽는 tool 제공자이고, agent는 MCP tool call을 통해서만 과거 대화에 접근한다.

이번 주의 핵심은 “DB를 읽었다”가 아니라 “MCP tool을 호출해 필요한 과거 대화와 일정 정보를 가져왔다”는 trace다.

## 실습 흐름

1. `notebook/5주차_카나가_지난대화를_불러오다.ipynb`에서 MCP SQLite tool payload shape를 확인한다.
2. `search_previous_conversations`로 관련 대화 목록을 찾는다.
3. `load_conversation_messages`로 선택된 대화 메시지를 불러온다.
4. `extract_schedules_from_history`로 이전 대화에서 일정/참석자 후보를 추출한다.
5. trace에서 MCP tool 호출 순서와 이유를 설명한다.

## 관찰할 trace/payload

- `search_previous_conversations.hits`
- `load_conversation_messages.messages`
- `extract_schedules_from_history.schedules`
- `conversation_id`
- 멤버별 가능 시간 후보

## 확인 질문

1. Agent가 SQLite DB를 직접 읽지 않고 MCP tool을 호출하게 하는 이유는 무엇인가?
2. 대화 목록 검색과 메시지 로드는 왜 다른 tool이어야 하는가?
3. 이전 대화에서 일정 후보를 추출할 때 반드시 남겨야 하는 필드는 무엇인가?

## 작은 응용 과제

팀원 A/B/C 대화를 추가하고 가능한 시간이 겹치는 후보를 찾아본다.
