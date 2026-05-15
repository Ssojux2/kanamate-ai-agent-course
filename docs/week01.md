# 1주차. Function/Tool Call로 개인 일정 생성, 조회, 삭제하기

## 학습 목표

- 모델이 직접 일정을 저장하는 것이 아니라 tool 이름과 arguments를 만든다는 점을 설명한다.
- `create_schedule`, `list_schedules`, `delete_schedule`의 `tool_call`과 `tool_result`를 구분한다.
- 최종 답변보다 일정 payload의 `id`, `date`, `start_time`, `attendees`를 먼저 확인한다.

## 핵심 개념

Function/tool call은 자연어 요청을 코드 실행으로 연결하는 첫 단계다. 사용자가 "발표 리허설을 내일 10시에 잡아줘"라고 말하면 모델은 Python 함수를 직접 실행하지 않는다. 대신 호출할 tool 이름과 arguments를 구조화해서 만들고, 노트북 코드는 그 요청을 실행한 뒤 결과를 다시 모델에게 전달한다.

이번 주에는 개인 메이트 `나나(Nana)`가 메모리 안의 일정 목록을 다룬다. 중요한 관찰 대상은 답변 문장이 아니라 모델이 만든 tool arguments와 tool 실행 결과다.

## 실습 흐름

1. `notebook/01_나나를_깨우다.ipynb`에서 tool call의 기본 구조를 본다.
2. 노트북의 준비 셀을 실행해 환경 변수와 공통 helper를 준비한다.
3. `create_schedule`이 일정 payload를 JSON 문자열로 반환하는지 확인한다.
4. `list_schedules`로 현재 일정 목록을 조회하고 생성 결과와 이어지는지 본다.
5. `delete_schedule`로 `schedule_id`가 맞는 일정을 삭제하는지 확인한다.
6. 회고 셀에서 tool call과 tool result를 구분해 설명한다.

## 관찰할 trace/payload

- `tool_call`: 모델이 선택한 tool 이름과 arguments
- `create_schedule` arguments: `title`, `date`, `start_time`, `attendees`
- `tool_result`: 실제 tool 실행 결과 JSON 문자열
- `created_schedule`: 저장된 일정의 `id`, `date`, `start_time`
- `list_schedules` result: 생성된 일정이 목록에 남아 있는지
- `delete_schedule` result: `deleted=True`와 삭제 대상 `schedule_id`

## 확인 질문

1. `tool_call`과 `tool_result`는 각각 누가 만들고 무엇을 의미하는가?
2. 사용자가 "내일 10시"라고 말했을 때 사람이 검증해야 할 arguments는 무엇인가?
3. 최종 답변이 자연스러워도 `list_schedules` trace를 확인해야 하는 이유는 무엇인가?

## 작은 응용 과제

참석자가 없는 개인 일정 요청과 참석자가 있는 일정 요청을 각각 실행한다. 두 trace에서 `attendees` arguments와 저장 payload가 어떻게 달라지는지 비교한다.
