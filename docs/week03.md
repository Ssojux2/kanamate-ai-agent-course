# 3주차. ChromaDB 기반 RAG와 Agentic RAG 검색 Tool 만들기

## 학습 목표

- RAG와 Agentic RAG의 차이를 "검색을 누가, 언제 결정하는가"로 설명한다.
- ChromaDB collection에 저장된 메모 수와 검색 hit를 확인한다.
- 직접 검색 결과와 agent tool trace 안의 검색 결과를 비교한다.

## 핵심 개념

RAG는 먼저 검색한 내용을 모델 답변에 넣는 흐름이다. Agentic RAG는 모델이 검색이 필요한지 판단하고 `search_memory` tool을 호출하는 흐름이다. 이번 주의 검색 기억 저장소는 ChromaDB collection이다.

중요한 것은 embedding 수학이나 ChromaDB 내부 index가 아니라, 어떤 메모가 저장됐고 어떤 질문에서 어떤 hit가 돌아왔는지 설명하는 것이다.

## 실습 흐름

1. `notebook/03_rag_agentic_rag.ipynb`에서 기본 메모를 ChromaDB collection에 저장한다.
2. `week03.py`의 `reset_memory_collection`과 `memory_collection_state`로 저장 상태를 확인한다.
3. `search_memory_hits`를 직접 호출해 `hits`와 `distance`를 본다.
4. `search_memory` tool을 가진 agent가 검색이 필요한 질문에서 tool을 호출하는지 확인한다.
5. `python week03.py`로 Gradio UI를 실행해 원본 메모, 검색 hit, collection 상태, tool trace를 함께 본다.

## 관찰할 trace/payload

- `collection_name`: 현재 사용 중인 ChromaDB collection 이름
- `count`: collection에 저장된 메모 수
- `hits`: 검색 결과 리스트
- `content`: 검색된 원문 메모
- `distance`: 질문과 hit 사이의 거리 값
- `search_memory` tool call: agent가 검색 필요성을 판단했는지
- `tool_result` 안의 `hits`: 직접 검색 결과와 같은 구조인지

## 확인 질문

1. RAG와 Agentic RAG는 검색을 누가, 언제 결정한다는 점에서 다른가?
2. ChromaDB `count()`와 `query(...)` 결과는 각각 무엇을 확인하는 값인가?
3. `hits`의 `content`와 최종 답변이 어긋나면 무엇을 의심해야 하는가?
4. `distance`는 왜 최종 답변 문구보다 먼저 봐야 하는가?

## 작은 응용 과제

메모 한 줄을 의도적으로 바꾼 뒤 같은 질문을 다시 실행한다. ChromaDB hit, `distance`, 최종 답변이 어떻게 변하는지 비교한다.
