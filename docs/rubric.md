# 카나메이트 평가 루브릭

이 루브릭은 모델 답변 문구의 자연스러움보다 agentic AI 실행 흐름을 설명하고 검증하는 능력을 평가한다.

## 공통 평가 원칙

- 최종 답변만 보고 평가하지 않는다.
- `trace`, `structured_response`, `payload`, `selected_agent`, `inner_tool_names`를 근거로 평가한다.
- 통과 기준은 "작동했다"가 아니라 "왜 작동했는지 설명할 수 있다"다.

## 주차별 루브릭

| 주차 | 최소 통과 기준 | 우수 기준 | 응용 기준 |
| --- | --- | --- | --- |
| 1주차 Tool call | `create_schedule`, `list_schedules` trace를 찾을 수 있다 | tool arguments가 사용자 요청과 맞는지 설명한다 | 새 일정 요청 문장을 만들고 trace 차이를 비교한다 |
| 2주차 Structured output | `kind`와 세부 객체를 확인할 수 있다 | 자유 문장 응답보다 Pydantic 객체가 안전한 이유를 설명한다 | 새 `unknown` 또는 `reminder` 예시를 만들고 결과를 비교한다 |
| 3주차 RAG/ChromaDB | ChromaDB collection `count()`와 `hits` 목록을 확인할 수 있다 | RAG와 Agentic RAG 차이를 ChromaDB `query` 흐름으로 설명한다 | 메모를 바꿔 검색 결과, `distance`, 답변 변화를 관찰한다 |
| 4주차 MCP/SQLite | MCP payload의 `event_id`와 SQLite row의 `event_id`를 비교할 수 있다 | Python 함수 tool과 MCP tool의 차이를 payload와 저장 row 기준으로 설명한다 | 다른 날짜/멤버 요청으로 payload와 SQLite row 변화를 확인한다 |
| 5주차 Sub-agent | `selected_agent`가 기대 agent와 같은지 확인한다 | supervisor trace와 sub-agent inner trace를 구분한다 | 개인/그룹 경계가 애매한 요청을 만들고 라우팅을 토론한다 |
| 6주차 WebUI | 최종 UI에서 선택 agent와 내부 tool을 설명한다 | 실패 가능성과 사람이 검토해야 할 값을 함께 말한다 | KanaMate 개선 미니 프로젝트를 제안하고 trace 기준을 설계한다 |

## 최종 평가: KanaMate 개선 미니 프로젝트

수강생은 기존 흐름을 크게 벗어나지 않는 작은 개선을 하나 제안하고 설명한다.

예시 주제:

- 나나가 일정 생성 전에 참석자 누락 여부를 확인하게 만들기
- 카나가 공통 가능 시간이 없을 때 대안을 제안하게 만들기
- ChromaDB 메모 검색 결과가 없을 때 답변 정책 정하기
- SQLite에 저장된 일정 row를 기준으로 중복 일정 처리 정책 정하기
- 최종 WebUI에 trace 요약을 더 보기 쉽게 표시하기

## 최종 발표 템플릿

발표는 아래 순서를 따른다.

1. 입력: 사용자가 어떤 요청을 했는가?
2. 선택 agent: supervisor가 누구에게 맡겼는가?
3. 내부 tool: sub-agent가 어떤 tool을 호출했는가?
4. payload: 실행 결과에서 중요한 값은 무엇인가?
5. 최종 답변: payload를 근거로 답했는가?
6. 실패 가능성: 어떤 값은 사람이 확인해야 하는가?

## 채점 기준

| 항목 | 배점 | 설명 |
| --- | ---: | --- |
| 개념 설명 | 25 | 일반 챗봇과 agentic AI 차이, tool/ChromaDB RAG/MCP SQLite/sub-agent 역할 설명 |
| trace 해석 | 30 | tool call, tool result, ChromaDB hits, SQLite row, payload, selected agent를 근거로 설명 |
| 구현 수정 | 25 | 기존 TODO 또는 작은 개선을 repo 패턴에 맞게 구현 |
| 검증 태도 | 20 | assert, golden scenario, 실패 가능성을 함께 확인 |

## 감점 기준

- 최종 답변 문구만 보고 성공이라고 판단한다.
- tool arguments가 사용자 요청과 맞는지 확인하지 않는다.
- API 오류와 코드 오류를 구분하지 못한다.
- MCP, SQLite, RAG, ChromaDB, sub-agent를 이름만 말하고 실행 흐름으로 설명하지 못한다.
- 사람의 검토가 필요한 값과 자동 실행해도 되는 값을 구분하지 않는다.
