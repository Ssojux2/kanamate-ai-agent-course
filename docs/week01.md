# 1주차. 나나를 깨우다

**부제:** Nana 개인 일정 tool

## 학습 목표

- `personal_create_schedule`, `personal_list_schedules`, `personal_delete_schedule`의 역할을 구분한다.
- 모델이 개인 일정 tool을 어떤 arguments로 호출하는지 trace로 확인한다.
- 메모리 저장소에 내 개인 일정이 생성, 조회, 삭제되는 흐름을 설명한다.

## 핵심 개념

1주차는 Nana가 내 개인 일정을 다루는 가장 작은 agentic 흐름이다. 모델은 일정을 직접 저장하지 않고, 개인 일정 tool 이름과 arguments를 만든다. 노트북 코드는 tool call을 실행하고, 메모리 저장소 결과를 다시 모델에게 전달한다.

## 실습 흐름

1. `notebook/01_나나를_깨우다.ipynb`에서 개인 일정 tool call의 기본 구조를 본다.
2. `personal_create_schedule`이 `title`, `date`, `start_time`, `attendees`를 받아 저장 payload를 만드는지 확인한다.
3. `personal_list_schedules`로 현재 내 일정 목록을 조회한다.
4. `personal_delete_schedule`로 `schedule_id`가 맞는 일정을 삭제한다.
5. 최종 답변보다 tool arguments와 저장소 결과를 먼저 검증한다.

## 관찰할 trace/payload

- `personal_create_schedule` tool call arguments
- `personal_list_schedules` tool result
- `personal_delete_schedule` tool result
- 저장된 개인 일정의 `id`, `title`, `date`, `start_time`, `attendees`

## 확인 질문

1. 모델 답변과 tool call은 어떤 점에서 다른가?
2. 개인 일정 생성에서 사람이 반드시 검증해야 할 arguments는 무엇인가?
3. 최종 답변이 자연스러워도 저장소 payload를 확인해야 하는 이유는 무엇인가?

## 작은 응용 과제

참석자가 없는 개인 일정과 참석자가 있는 개인 일정을 각각 생성한다. 두 trace에서 `attendees`와 저장 payload가 어떻게 달라지는지 비교한다.
