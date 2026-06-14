# 4주차. 나나가 기억을 찾아오다

**부제:** Agentic RAG with ChromaDB + SQLite Search Tools

## 학습 목표

- 개인 참고자료는 ChromaDB RAG 검색 tool로, 구조화된 일정/할 일/알림은 SQLite 검색 tool로 찾는다.
- agent가 필요한 순간 `search_rag_memory`와 `search_sqlite_requests` tool 중 하나를 선택해 호출하는 흐름을 확인한다.
- 답변에 검색된 참고자료와 SQLite row가 첨부 맥락으로 사용되는지 trace로 검증한다.

## 핵심 개념

4주차는 RAG 검색 대상을 둘로 나눈다. 자유로운 개인 참고자료는 ChromaDB에 저장하고 `search_rag_memory` tool이 embedding 검색 결과를 `hits`로 정리한다. 구조화해 저장한 일정/할 일/알림은 `search_sqlite_requests` tool이 SQLite row에서 검색한다.

중요한 것은 agent가 사용자 질문을 어떤 tool의 `query`로 전달했는지, 그리고 답변이 그 검색 결과를 근거로 삼았는지 설명하는 것이다.

## 실습 흐름

1. `notebook/4주차_나나가_기억을_찾아오다.ipynb`에서 ChromaDB 참고자료 저장 흐름을 확인한다.
2. 개인 메모/참고자료 질문은 `search_rag_memory`로 검색한다.
3. 저장된 구조화 row 질문은 `search_sqlite_requests`로 검색한다.
4. trace에서 사용자 질문이 어떤 tool의 `query`로 전달됐는지 본다.
5. tool result의 `hits` 또는 `rows`를 근거로 답변했는지 확인한다.

## 관찰할 trace/payload

- ChromaDB `hits`, `distance`, `metadata`
- SQLite saved request rows
- `search_rag_memory` tool call/result
- `search_sqlite_requests` tool call/result
- 답변에 첨부된 검색 맥락

## 확인 질문

1. ChromaDB에 저장할 정보와 SQLite에 저장할 정보는 어떻게 나누는가?
2. agent가 어떤 상황에서 `search_rag_memory`를 호출해야 하는가?
3. agent가 어떤 상황에서 `search_sqlite_requests`를 호출해야 하는가?
4. 검색 결과와 최종 답변이 어긋나면 무엇을 의심해야 하는가?

## 작은 응용 과제

같은 질문을 개인 참고자료 질문과 저장 일정 질문으로 바꿔 보고, 호출되는 검색 tool과 tool result가 어떻게 달라지는지 비교한다.
