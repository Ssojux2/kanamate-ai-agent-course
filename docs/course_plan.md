# 카나메이트(KanaMate) 에이전트 입문 과정 계획

이 문서는 카나메이트 6주 과정을 에이전트에 익숙하지 않은 수강생 기준으로 재정리한 계획서다. 목표는 복잡한 agent framework를 깊게 외우는 것이 아니라, agentic AI가 어떤 판단과 도구 실행 흐름으로 동작하는지 trace를 보며 설명하고 작은 수준으로 수정할 수 있게 만드는 것이다.

## 1. 대상과 목표

### 대상

- agentic AI, tool call, RAG, MCP, sub-agent 흐름에 아직 익숙하지 않은 수강생
- Python 문법을 조금 배웠거나 예제를 따라 입력하며 흐름을 익힐 수 있는 수강생
- ChatGPT, Claude, Copilot 같은 AI 도구는 써봤지만 에이전트 실행 trace는 낯선 수강생
- 터미널, Jupyter, `.env` 설정은 낯설 수 있지만 안내를 따라 실습할 수 있는 수강생

함수, 리스트, 딕셔너리, 문자열, JSON의 아주 기본적인 모양은 수업 중 반복 설명한다. 다만 이 과정은 Python 입문 과정 자체를 대체하지 않고, Python 기초를 agentic AI 실습 안에서 다시 확인하는 방식으로 진행한다.

### 과정 목표

수강생은 과정을 마친 뒤 다음을 할 수 있어야 한다.

- 일반 챗봇과 agentic AI의 차이를 설명할 수 있다.
- 모델이 직접 업무를 끝내는 것이 아니라 tool call 인자를 만들고 실행 결과를 받아 답한다는 점을 설명할 수 있다.
- `trace`, `structured_response`, `payload`, `selected_agent`, `inner_tool_names`를 보고 실행 흐름을 검증할 수 있다.
- 일정/메모/그룹 조율 맥락에서 tool, structured output, ChromaDB 기반 RAG, SQLite 저장 MCP, sub-agent를 작은 수준으로 수정할 수 있다.
- 최종 WebUI에서 입력, 선택 agent, 내부 tool, 최종 답변, 실패 가능성을 발표할 수 있다.

### 비목표

- LangChain 내부 추상화 전체 이해
- MCP protocol 상세 구현
- vector database 알고리즘과 embedding 수학
- SQLite query optimizer와 파일 잠금 세부
- production-grade 인증, 권한, 배포, 모니터링
- 대규모 multi-agent system 설계

## 2. 과정의 큰 그림

카나메이트는 개인 메이트 `나나(Nana)`와 그룹 메이트 `카나(Kana)`로 구성된 AI 일정·협업 비서다.

| 메이트 | 역할 |
| --- | --- |
| 나나 | 개인 일정, 할 일, 메모 저장과 검색 기반 질의응답 |
| 카나 | 그룹 멤버 응답을 바탕으로 가능한 시간을 찾고 그룹 일정을 확정 |

학습 흐름은 다음 순서로 넓어진다.

```text
LLM
-> Tool call
-> Structured output
-> State/Memory
-> Retrieval, Agentic RAG, and ChromaDB
-> External tools through MCP and SQLite
-> Supervisor and sub-agent routing
-> Explainable WebUI demo
```

핵심 관찰 대상은 모델의 최종 문장이 아니라 실행 중간값이다. 수강생은 매주 "무슨 tool이 호출됐는가", "인자는 맞는가", "payload는 기대한 구조인가", "검증 기준을 통과했는가"를 확인한다.

## 3. Repo 구조와 역할

```text
notebook/
  01_llm_agent_function_tool_call.ipynb
  02_structured_output_pydantic.ipynb
  03_rag_agentic_rag.ipynb
  04_mcp_tool_call_gradio_ui.ipynb
  05_subagent_skills_md_harness.ipynb
  06_webui_subagent.ipynb
week01.py ... week06.py
docs/
  orientation.md
  course_plan.md
  troubleshooting.md
  rubric.md
```

- `notebook/`: 개념 설명, 노트북 내부 예제 실행, 회고 질문
- `weekXX.py`: 노트북 다음에 바로 푸는 `# TODO 문제`, 바로 아래 `# 모범 답안`, Gradio UI, smoke test 대상
- `docs/`: 0주차 오리엔테이션, 과정 계획, 오류 대응, 평가 루브릭

## 4. 노트북 공통 구성

| 섹션 | 내용 |
| --- | --- |
| 0. 목표 | 이번 주 성취 기준과 완성 결과 |
| 1. 준비 | API key 확인, 공통 import, helper 함수 |
| 2. 개념 | 오늘의 큰 그림, 반드시 이해할 것, 지금은 몰라도 되는 것 |
| 3. 기본 개념 실습 | 실제 API 호출이 포함된 가장 작은 핵심 예제 |
| 4. 카나메이트 확장 예제 | 같은 개념을 카나메이트 맥락으로 확장 |
| 5. 확장 예제 실행 | trace, route, structured response, payload 확인 |
| 6. 회고 | 개념 확인 질문 3개와 작은 응용 과제 |

1주차 노트북에는 회고 직전에 `python week01.py`로 별도 실행하는 안내만 추가한다.

## 5. 0-6주 로드맵

| 주차 | 주제 | 성취 기준 |
| --- | --- | --- |
| 0주차 | 오리엔테이션 | agentic AI 큰 그림과 실습 환경을 설명할 수 있다 |
| 1주차 | Function call, Tool call | `tool_call`과 `tool_result`를 구분하고 일정 생성/조회 trace를 설명할 수 있다 |
| 2주차 | Structured output, Pydantic | 자유 문장과 Pydantic 객체의 차이를 설명하고 `kind`별 결과를 확인할 수 있다 |
| 3주차 | RAG, Agentic RAG, ChromaDB | ChromaDB collection 저장 상태, 검색 `hits`, agent tool trace를 비교하고 RAG/Agentic RAG 차이를 설명할 수 있다 |
| 4주차 | 실제 로컬 MCP 서버와 SQLite | MCP payload와 SQLite 저장 row를 비교하고 Python 함수 tool과 MCP tool의 차이를 설명할 수 있다 |
| 5주차 | Sub-agent와 역할 분리 | supervisor가 `nana_agent` 또는 `kana_agent`로 위임했는지 검증할 수 있다 |
| 6주차 | 설명 가능한 WebUI 통합 데모 | 입력, 선택 agent, 내부 tool, 최종 답변, 실패 가능성을 발표할 수 있다 |

## 6. 주차별 수정 방향

### 0주차. 문서 기반 오리엔테이션

- 별도 Python 실습 없이 환경 세팅과 개념 지도를 준비한다.
- 일반 챗봇과 agentic AI 차이를 먼저 잡는다.
- 최종 체크는 `.env`, Jupyter Notebook/JupyterLab 실행, compileall 통과다.

### 1주차. Tool call 관찰

- 목표는 tool을 많이 만드는 것이 아니라, 모델이 만든 tool arguments를 읽는 것이다.
- 실습 기준은 `create_schedule`, `list_schedules` 호출 trace를 직접 찾아 설명하는 것이다.
- 회고 질문은 `tool_call`과 `tool_result`의 차이에 집중한다.

### 2주차. Structured output 필요성

- structured output을 "모델 답변을 엑셀/앱에 넣기 좋은 양식으로 받기"로 설명한다.
- 실습 기준은 `kind`, `schedule`, `todo`, `reminder`, `unknown` 차이를 말하는 것이다.
- 자유 문장 답변을 바로 앱에 넣기 어려운 이유를 확인한다.

### 3주차. RAG, Agentic RAG, ChromaDB

- RAG는 먼저 검색하고 답하는 흐름이다.
- Agentic RAG는 모델이 검색 필요성을 판단하고 tool을 호출하는 흐름이다.
- ChromaDB는 검색 기억을 담는 collection으로 직접 관찰한다.
- `client`, `collection`, `add`, `count`, `query`, `hits`, `distance`를 수업 관찰 대상으로 둔다.
- ChromaDB 내부 index, embedding 수학, HNSW 튜닝은 구현 세부로 두고 다루지 않는다.

### 4주차. 분리된 MCP HTTP 서버와 SQLite 저장

- MCP는 "도구를 외부 서버에서 표준 방식으로 가져오는 방법"으로 정의한다.
- 수강생은 별도 터미널에서 `python week04_mcp_server.py`로 간단한 MCP 서버를 실행하고, 노트북과 Gradio UI는 `http://127.0.0.1:8004/mcp`로 요청한다.
- `streamable-http`, `FastMCP`, `MultiServerMCPClient`는 지금은 몰라도 되는 구현 세부로 분리한다.
- MCP 서버의 `calendar_create_event` tool은 SQLite에 일정 row를 저장한다.
- 실습 기준은 MCP 서버 payload에서 `server`, `tool`, `arguments`, `status`를 확인하고, 같은 `event_id`가 SQLite row에도 저장됐는지 확인하는 것이다.

### 5주차. Sub-agent 라우팅

- supervisor는 직접 일정 생성 tool을 들고 있지 않고, sub-agent tool을 호출한다.
- Golden Scenario는 눈으로 한 번 확인하는 대신 반복 가능한 평가 케이스를 만드는 장치다.
- 실습 기준은 요청 유형에 따라 `nana_agent` 또는 `kana_agent` 선택을 검증하는 것이다.

### 6주차. 설명 가능한 통합 데모

- 최종 결과물은 단순히 작동하는 WebUI가 아니라 trace를 보며 설명할 수 있는 WebUI다.
- 발표 템플릿은 입력, 선택 agent, 내부 tool, 최종 답변, 실패 가능성 순서로 구성한다.
- 최종 응용은 KanaMate 개선 미니 프로젝트로 평가한다.

## 7. 테스트 전략

- `python -m compileall week01.py week02.py week03.py week04.py week05.py week06.py`
- 모든 노트북 `nbformat.validate` 통과
- 기존 `weekXX.py`의 `create_demo()`가 API 호출 없이 생성되는지 확인
- 노트북 다음에 같은 주차 `weekXX.py`의 `# TODO 문제`를 보고 바로 아래 `# 모범 답안`과 비교하는 흐름이 README와 노트북에 일관되게 안내되는지 확인
- 4주차 MCP 서버를 별도 실행한 뒤 MCP tool을 직접 호출했을 때 `tmp/week04_calendar.sqlite3`에 row가 저장되는지 확인

## 8. 완료 기준

- README만 보고 새 수강생이 환경 세팅과 첫 노트북 실행 순서를 알 수 있다.
- 0주차 오리엔테이션 문서가 agentic AI 큰 그림과 선수지식을 설명한다.
- 각 주차 노트북에 "오늘의 큰 그림", "반드시 이해할 것", "지금은 몰라도 되는 것", "막혔을 때 볼 trace", "개념 확인 질문", "작은 응용 과제"가 있다.
- 학습 동선이 `notebook`에서 같은 주차 `weekXX.py` 실습으로 바로 이어진다.
- 주차별 평가 기준이 [rubric.md](rubric.md)에 명시되어 있다.
- 흔한 오류 대응이 [troubleshooting.md](troubleshooting.md)에 정리되어 있다.
