# 0주차. Agentic AI 오리엔테이션

이 문서는 1주차 노트북을 열기 전에 읽는 준비 자료다. 목표는 코드를 모두 이해하는 것이 아니라, 앞으로 6주 동안 무엇을 관찰해야 하는지 눈을 맞추는 것이다.

## 학습 목표

- 일반 챗봇과 agentic AI의 차이를 설명한다.
- 모델 답변보다 `tool_call`, `tool_result`, `payload`가 더 중요한 이유를 이해한다.
- 1-6주차 노트북 실행에 필요한 환경을 준비한다.
- 오류가 났을 때 실행한 셀, 오류 메시지, 사용 파일을 기준으로 원인을 좁힌다.

## 핵심 개념

일반 챗봇은 주로 자연어 답변을 만든다. agentic AI는 답변 전후에 행동을 한다. 모델은 필요한 도구를 고르고, 도구에 넘길 인자를 만들고, 실행 결과를 받아 다음 답변이나 다음 도구 호출을 결정한다.

| 구분 | 일반 챗봇 | Agentic AI |
| --- | --- | --- |
| 주요 출력 | 자연어 답변 | 답변 + tool call + 실행 결과 |
| 앱과 연결 | 약함 | 개인 일정, SQLite 저장소, ChromaDB, MCP, Sub-agent와 연결 |
| 확인할 것 | 답변이 그럴듯한가 | 어떤 도구를 어떤 인자로 호출했는가 |
| 실패 방식 | 틀린 답변 | 잘못된 tool 선택, 잘못된 인자, 잘못된 payload |

6주 과정은 아래 흐름으로 확장된다.

```text
나나를 깨우다 (Nana Personal Schedule Tools)
-> 자연어를 구조화된 요청으로 (Structured Output)
-> 나나의 기록장을 만들다 (Structured Output to SQLite)
-> 나나가 기억을 찾아오다 (Agentic RAG with ChromaDB + SQLite)
-> 카나가 지난 대화를 불러오다 (MCP SQLite History Search Tools)
-> 카나메이트가 약속을 결정하다 (Supervisor/Sub-Agent Final Scheduling)
```

## 실습 흐름

수강 전에는 Python 함수, 리스트/딕셔너리, JSON 모양, 문자열, 터미널 명령, Jupyter 셀 실행, `.env` 파일 편집을 대략 알아볼 수 있으면 충분하다.

repo 루트에서 `uv` 환경을 준비한다.

```bash
bash scripts/setup_uv_env.sh
```

이 명령은 `pyproject.toml`과 `uv.lock` 기준으로 `.venv`를 만들고, Jupyter에서 선택할 `Python (KanaMate)` kernel을 등록한다.

`.env` 파일을 준비한다.

```bash
cp .env.example .env
```

`.env` 파일에는 다음 값을 넣는다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Jupyter를 실행한다.

```bash
uv run jupyter lab
# 또는
uv run jupyter notebook
```

Jupyter에서 kernel은 `Python (KanaMate)`를 선택한다.

## 관찰할 trace/payload

앞으로 자주 볼 trace는 이런 모양이다.

```json
[
  {
    "event": "tool_call",
    "tool_name": "personal_create_schedule",
    "arguments": {
      "title": "발표 리허설",
      "date": "2026-05-19",
      "start_time": "15:00"
    }
  },
  {
    "event": "tool_result",
    "tool_name": "personal_create_schedule",
    "content": "{\"ok\": true}"
  }
]
```

읽는 순서는 단순하다.

1. 어떤 tool을 호출했는가?
2. arguments가 사용자 요청과 맞는가?
3. tool result 또는 structured payload가 성공적으로 만들어졌는가?
4. 최종 답변이 payload와 검색 근거를 바탕으로 말하는가?

## 확인 질문

1. 일반 챗봇과 agentic AI는 출력과 실패 방식이 어떻게 다른가?
2. `tool_call`과 `tool_result`는 각각 누가 만들고 무엇을 의미하는가?
3. SQLite 저장소처럼 tool trace가 없는 주차에서는 무엇을 검증해야 하는가?
4. 최종 답변이 자연스러워도 trace나 payload를 확인해야 하는 이유는 무엇인가?

## 작은 응용 과제

1주차 노트북을 열기 전에 `.env` 설정과 Jupyter 실행을 끝낸다. 오류가 난다면 실행한 셀, 전체 오류 메시지, 사용 중인 파일명, Python 환경을 함께 정리한다.
