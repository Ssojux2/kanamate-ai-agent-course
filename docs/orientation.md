# 0주차. Agentic AI 오리엔테이션

이 문서는 1주차 노트북을 열기 전에 읽는 준비 자료다. 목표는 코드를 모두 이해하는 것이 아니라, 앞으로 6주 동안 무엇을 관찰해야 하는지 눈을 맞추는 것이다.

## 1. 일반 챗봇과 agentic AI의 차이

일반 챗봇은 주로 사용자의 질문에 자연어 답변을 만든다. 답변이 좋아 보여도, 실제 앱의 일정 저장소를 바꾸거나 검색 시스템을 호출하거나 다른 agent에게 일을 나누지는 않는다.

agentic AI는 답변 전후에 행동을 한다. 모델은 필요한 도구를 고르고, 도구에 넘길 인자를 만들고, 실행 결과를 받아 다음 답변이나 다음 도구 호출을 결정한다.

| 구분 | 일반 챗봇 | Agentic AI |
| --- | --- | --- |
| 주요 출력 | 자연어 답변 | 답변 + tool call + 실행 결과 |
| 앱과 연결 | 약함 | 일정, 검색, 메모, 외부 서버와 연결 |
| 확인할 것 | 답변이 그럴듯한가 | 어떤 도구를 어떤 인자로 호출했는가 |
| 실패 방식 | 틀린 답변 | 잘못된 tool 선택, 잘못된 인자, 잘못된 payload |

이 과정에서는 "답변이 예쁜가"보다 "실행 흐름을 설명할 수 있는가"를 더 중요하게 본다.

## 2. 핵심 지도

```text
LLM
-> Tool
-> State/Memory
-> ChromaDB Retrieval
-> MCP and SQLite Tool Storage
-> Routing
-> Evaluation
-> Human Oversight
```

- `LLM`: 자연어를 이해하고 다음 행동을 결정하는 모델
- `Tool`: 일정 생성, 목록 조회, 검색처럼 코드로 실행되는 기능
- `State/Memory`: 이미 만든 일정, 저장된 메모처럼 다음 요청에 영향을 주는 정보
- `ChromaDB Retrieval`: 모델이 모르는 메모를 vector DB에서 검색해서 가져오는 흐름
- `MCP and SQLite Tool Storage`: 외부 tool 서버가 표준 방식으로 호출되고, 실행 결과가 로컬 DB에 저장되는 흐름
- `Routing`: supervisor가 어떤 sub-agent에게 맡길지 고르는 흐름
- `Evaluation`: 답변 문구가 아니라 trace, payload, assert로 확인하는 과정
- `Human Oversight`: 사람이 tool 인자와 결과를 검토하고 위험한 실행을 통제하는 관점

## 3. 수강 전 체크리스트

아래 항목을 완벽히 설명할 필요는 없지만, 코드를 보고 대략 알아볼 수 있어야 한다.

- Python 함수: `def run_request(...):`
- 리스트와 딕셔너리: `[]`, `{}`
- JSON 모양: `{"tool_name": "create_schedule"}`
- 문자열과 f-string
- 터미널에서 명령 실행
- Jupyter 노트북 셀 실행
- `.env` 파일에 API key 넣기
- 오류 메시지를 복사해 검색하거나 troubleshooting 문서에서 찾기

## 4. 지금은 몰라도 되는 것

다음 내용은 과정 중 등장하지만 깊게 외우지 않아도 된다.

- LangChain의 내부 agent 실행 구조
- MCP protocol의 상세 스펙
- `streamable-http` transport 내부 동작
- ChromaDB index 알고리즘
- embedding 수학
- SQLite query optimizer와 파일 잠금 세부
- Gradio 컴포넌트 세부 옵션
- production 배포, 인증, 권한, 관측성

수업에서 중요한 것은 "이 코드가 왜 필요한가"와 "어떤 trace를 보면 성공인지"다.

## 5. 환경 준비

```bash
conda activate langchain
source scripts/use_langchain_env.sh
cp .env.example .env
```

새 환경에서 시작한다면 먼저 repo의 환경 파일로 `langchain` env를 만든다.

```bash
conda env create -f environment.yml
conda activate langchain
source scripts/use_langchain_env.sh
```

`.env` 파일에 값을 넣는다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

준비가 됐는지 확인한다.

```bash
python -m compileall week01.py week02.py week03.py week04.py week05.py week06.py
jupyter lab
# 또는
jupyter notebook
```

## 6. Trace 읽기 예고

앞으로 자주 볼 trace는 이런 모양이다.

```json
[
  {
    "event": "tool_call",
    "tool_name": "create_schedule",
    "arguments": {
      "title": "발표 리허설",
      "date": "2026-04-24",
      "start_time": "10:00"
    }
  },
  {
    "event": "tool_result",
    "tool_name": "create_schedule",
    "content": "{\"ok\": true}"
  }
]
```

읽는 순서는 단순하다.

1. 어떤 tool을 호출했는가?
2. arguments가 사용자의 요청과 맞는가?
3. tool result가 성공 payload를 돌려줬는가?
4. 최종 답변이 payload를 근거로 말하는가?

## 7. 0주차 완료 기준

- 일반 챗봇과 agentic AI의 차이를 한 문단으로 설명할 수 있다.
- `tool_call`은 모델의 실행 요청이고 `tool_result`는 도구 실행 결과라고 말할 수 있다.
- `.env` 설정과 Jupyter 실행을 완료했다.
- 막혔을 때 [troubleshooting.md](troubleshooting.md)를 먼저 볼 수 있다.
