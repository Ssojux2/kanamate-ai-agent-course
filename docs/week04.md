# 4주차. 나나가 기억을 찾아오다

**부제:** Agentic RAG with ChromaDB + SQLite

## 학습 목표

- 개인 참고자료는 ChromaDB에서, 구조화된 일정/할 일/알림은 SQLite에서 검색한다.
- agent가 필요한 순간 `search_personal_references`와 `search_saved_requests` tool 중 하나를 선택해 호출하는 흐름을 확인한다.
- 답변에 검색된 참고자료와 SQLite row가 첨부 맥락으로 사용되는지 trace로 검증한다.

## 핵심 개념

4주차는 RAG 검색 대상을 둘로 나눈다. 자유로운 개인 참고자료는 ChromaDB에 저장해 embedding 검색을 사용하고, 3주차에서 구조화해 저장한 일정/할 일/알림은 SQLite row 검색을 사용한다.

중요한 것은 agent가 어떤 질문에서 어떤 검색 tool을 선택했는지, 그리고 답변이 그 검색 결과를 근거로 삼았는지 설명하는 것이다.

## 실습 흐름

1. `notebook/04_나나가_기억을_찾아오다.ipynb`에서 ChromaDB 참고자료 저장 흐름을 확인한다.
2. SQLite saved request row 검색 역할을 `search_saved_requests`로 구분한다.
3. 개인 참고자료 질문은 `search_personal_references`를 호출하는지 본다.
4. 저장 일정/할 일/알림 질문은 `search_saved_requests`를 호출해야 한다는 기준을 세운다.
5. trace에서 어떤 RAG tool이 왜 호출됐는지 설명한다.

## 관찰할 trace/payload

- ChromaDB `hits`, `distance`, `metadata`
- SQLite saved request rows
- `search_personal_references` tool call
- `search_saved_requests` tool call
- 답변에 첨부된 검색 맥락

## 확인 질문

1. ChromaDB에 저장할 정보와 SQLite에 저장할 정보는 어떻게 나누는가?
2. agent가 어떤 상황에서 `search_saved_requests`를 호출해야 하는가?
3. 검색 결과와 최종 답변이 어긋나면 무엇을 의심해야 하는가?

## 작은 응용 과제

같은 질문을 개인 참고자료 질문과 저장 일정 질문으로 바꿔 보고, 호출되어야 하는 RAG tool이 어떻게 달라지는지 비교한다.
