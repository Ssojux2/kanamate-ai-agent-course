# 5주차. Supervisor/Sub-Agent 위임과 Golden Scenario 하네스

## 학습 목표

- supervisor와 sub-agent의 역할 차이를 설명한다.
- supervisor가 `nana_agent` 또는 `kana_agent` 중 어디로 위임했는지 trace로 확인한다.
- 선택된 agent뿐 아니라 sub-agent 내부 tool이 기대대로 실행됐는지 검증한다.

## 핵심 개념

Sub-agent는 역할과 사용할 도구를 나눈 agent다. Supervisor는 직접 `personal_create_schedule`이나 `group_confirm_slot` 같은 업무 tool을 들고 있지 않다. 대신 `nana_agent`, `kana_agent`처럼 sub-agent를 감싼 tool 중 하나를 호출한다.

Golden Scenario 하네스는 "이 입력이면 이 agent와 내부 tool이 나와야 한다"는 반복 가능한 기준이다. 모델 문장이 조금 달라져도 `selected_agent`와 `inner_tool_names`가 맞으면 라우팅이 통과한 것으로 본다.

## 실습 흐름

1. `notebook/05_subagent_skills_md_harness.ipynb`에서 supervisor와 sub-agent 구성을 확인한다.
2. `week05.py`의 `personal_create_schedule`, `group_confirm_slot`, `memory_save` payload를 읽는다.
3. `nana_agent` 위임 tool과 `kana_agent` 위임 tool이 내부 agent를 실행하고 trace를 payload에 담는지 본다.
4. `run_supervisor_case`로 개인 일정 케이스와 그룹 조율 케이스를 반복 실행한다.
5. `python week05.py`로 Gradio UI에서 `selected_agent`, `inner_tool_names`, delegate payload를 확인한다.

## 관찰할 trace/payload

- supervisor trace: `nana_agent` 또는 `kana_agent` tool call
- `selected_agent`: supervisor가 선택한 sub-agent
- `delegate_payload`: sub-agent가 반환한 답변과 내부 trace
- `inner_tool_names`: sub-agent 내부에서 실제 호출된 업무 tool 이름
- `expected_agent`: golden case가 기대한 agent
- `expected_inner_tool`: golden case가 기대한 내부 tool
- `passed`: 기대 agent와 내부 tool이 모두 맞는지

## 확인 질문

1. supervisor가 직접 `personal_create_schedule`을 호출하지 않는 이유는 무엇인가?
2. `selected_agent`만 맞고 내부 tool이 틀리면 성공이라고 볼 수 있는가?
3. Golden Scenario는 눈으로 한 번 실행해 보는 것과 무엇이 다른가?

## 작은 응용 과제

개인 일정처럼 보이지만 멤버 응답이 포함된 애매한 요청을 만든다. Supervisor가 어떤 agent를 선택하는지 보고, 그 선택이 맞는지 trace를 근거로 토론한다.
