# 6주차. 채팅 UI에서 Nana/Kana Sub-Agent 통합 데모 실행하기

## 학습 목표

- Nana/Kana 통합 흐름을 WebUI에서 실행한다.
- supervisor trace, delegate payload, sub-agent 내부 tool trace를 한 번에 설명한다.
- Nana의 `memory_save`가 구조화한 메모를 SQLite row로 저장했는지 확인한다.
- 최종 데모에서 입력, 선택 agent, 내부 tool, 최종 답변, 실패 가능성을 발표한다.

## 핵심 개념

최종 WebUI는 단순히 화면이 작동하는지 보는 데모가 아니다. 사용자의 입력을 supervisor가 받고, supervisor가 sub-agent tool을 호출하고, sub-agent가 내부 업무 tool을 실행한 뒤, UI가 그 근거를 함께 보여주는 설명 가능한 데모다.

6주차의 Nana는 개인 일정뿐 아니라 메모 저장도 처리한다. 메모 요청은 `memory_save(title, content)` tool arguments로 구조화되고, `memory_save` tool 자체가 SQLite `saved_memories` table 생성과 저장까지 처리한다. 기본 DB 파일은 `tmp/week06_memory.sqlite3`이고, 필요하면 `KANAMATE_WEEK06_DB_PATH`로 바꿀 수 있다. Kana는 그룹 일정 확정 흐름을 담당한다. `auto`, `personal`, `group` 모드에 따라 supervisor가 사용할 수 있는 위임 tool 목록도 달라진다.

## 실습 흐름

1. `notebook/06_webui_subagent.ipynb`에서 최종 UI 목표와 발표 흐름을 확인한다.
2. `week06.py`의 `memory_save`, `load_saved_memories`, `week06_delegate_to_nana`, `week06_delegate_to_kana` payload를 읽는다.
3. `make_supervisor(mode)`가 `auto`, `personal`, `group` 모드별로 어떤 tool을 제공하는지 확인한다.
4. `run_live_flow`로 사용자 입력을 실행하고 `selected_agent`, `delegate_payload`, `saved_memories`, supervisor trace를 모은다.
5. `run_practice_suite`로 개인 일정, 메모 저장, 그룹 일정 확정 케이스가 모두 통과하는지 본다.
6. `python week06.py`로 WebUI를 실행해 채팅 답변, 검증 payload, SQLite 저장 메모를 함께 확인한다.

## 관찰할 trace/payload

- `selected_agent`: supervisor가 선택한 Nana 또는 Kana
- supervisor trace: 위임 tool call과 tool result
- `delegate_payload.trace`: sub-agent 내부 실행 trace
- `inner_tool_names`: `personal_create_schedule`, `memory_save`, `group_confirm_slot`
- `memory_id`: `memory_save` payload와 SQLite row를 연결하는 값
- `saved_memories`: SQLite에서 다시 읽은 메모 row 목록
- `passed`: practice suite에서 기대 agent와 내부 tool이 맞는지
- 최종 답변: payload를 근거로 설명하는지
- 실패 가능성: 사람이 검토해야 할 날짜, 시간, 멤버, 메모 내용

## 확인 질문

1. 최종 WebUI에서 `selected_agent`와 `delegate_payload`를 함께 보여주는 이유는 무엇인가?
2. `passed=True`를 만들기 위해 어떤 trace 값을 확인해야 하는가?
3. `memory_save` payload의 `memory_id`와 SQLite `saved_memories` row는 어떻게 연결되는가?
4. 이 데모에서 사람이 검토해야 할 값은 무엇이며, 자동 실행하면 위험한 부분은 무엇인가?

## 작은 응용 과제

KanaMate 개선 미니 프로젝트 아이디어 하나를 정한다. 입력, 선택 agent, 내부 tool, SQLite 저장 row, payload, 실패 가능성 순서로 발표 템플릿을 작성한다.
