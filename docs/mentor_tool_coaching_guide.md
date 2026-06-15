# 멘토용 Agent Tool 코칭 안내

KanaMate 과정에서 학생들에게 가장 먼저 알려줄 관점은 단순하다. Agent는 답변만 만드는 챗봇이 아니라, 필요한 tool을 고르고, 실행할 값을 만들고, 실행 결과를 바탕으로 다음 행동을 정하는 프로그램이다.

## 3가지 핵심

1. 답변보다 trace를 먼저 본다.
   - 학생에게 "최종 답변이 자연스러워도 먼저 `tool_call`과 `tool_result`를 확인하자"고 안내한다.
   - 핵심 질문은 "어떤 tool을 호출했는가?"이다.

2. tool에는 정확한 입력이 들어가야 한다.
   - `arguments`, `structured_response`, `payload`가 사용자 요청과 맞는지 확인한다.
   - 일정이면 `title`, `date`, `start_time`, 참석자 같은 값이 맞아야 하고, 분류 작업이면 `kind`와 세부 필드가 맞아야 한다.

3. 결과는 근거와 연결되어야 한다.
   - SQLite row, ChromaDB `hits`, MCP 검색 결과, sub-agent trace가 최종 답변의 근거가 되는지 본다.
   - 검색 결과가 비었거나 `unknown`이 나와도 바로 실패라고 하지 말고, 안전하게 판단한 결과인지 확인한다.

## Agent 구현의 큰 원칙

- Agent에게 모든 일을 직접 시키지 말고, 역할이 분명한 tool을 제공한다.
- Tool 이름, 설명, 입력 스키마는 모델이 언제 무엇을 써야 하는지 알 수 있게 구체적으로 작성한다.
- 자연어 답변은 마지막 출력이고, 실제 검증 대상은 `tool_call`, `arguments`, `tool_result`, `payload`다.
- 자유로운 문장은 `structured_response`로 구조화하고, 오래 남길 정보는 SQLite 같은 저장소에 row로 남긴다.
- 참고자료 검색은 ChromaDB 같은 RAG tool로, 저장된 구조화 데이터 검색은 SQLite tool로 분리한다.
- 외부 데이터 접근은 MCP tool처럼 경계를 분명히 두고, agent가 직접 DB 내부 구현에 의존하지 않게 한다.
- 복잡한 작업은 supervisor가 직접 처리하지 않고 `nana_agent`, `kana_agent` 같은 sub-agent에게 위임하게 한다.

## 멘토 안내 멘트

> 오늘은 정답 문장보다 trace를 먼저 봅니다. Agent가 무엇을 말했는지가 아니라, 어떤 tool을 어떤 값으로 실행했는지를 확인해 봅시다.

> 좋은 agent 구현은 모델에게 모든 것을 맡기는 것이 아니라, 좋은 tool과 명확한 입력 스키마를 주고 그 실행 과정을 검증할 수 있게 만드는 것입니다.

> 결과가 이상하면 답변 문장부터 고치려고 하지 말고, tool 선택, arguments, tool result, 저장/검색 payload 순서로 확인하세요.
