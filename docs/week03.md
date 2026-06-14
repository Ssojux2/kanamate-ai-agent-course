# 3주차. 나나의 기록장을 만들다

**부제:** BaseModel tool 입력 스키마로 SQLite에 저장

## 학습 목표

- Week 2의 structured output 개념을 LangChain tool 입력 스키마로 연결한다.
- `SaveStructuredRequestInput(BaseModel)`로 `save_structured_request` tool의 입력 스키마를 정의한다.
- 모델이 입력 스키마에 맞춰 만든 arguments를 SQLite row로 저장한다.
- `structured_requests`, `schedules`, `todos`, `reminders` table의 역할을 구분한다.
- `kind`에 따라 알맞은 table에 정규화 저장되는지 tool trace와 row count로 확인한다.

## 핵심 개념

2주차 payload는 앱 코드에서 쓰기 좋은 객체지만, 조회와 추적을 위해서는 DB row로 남아야 한다. 3주차에서는 `SaveStructuredRequestInput(BaseModel)`을 저장 tool의 입력 스키마로 붙이고, 모델이 `save_structured_request` tool을 호출할 때 만든 arguments를 구조화된 값으로 본다.

tool 함수는 입력 항목을 모두 인자로 나열하지 않고 `**kwargs`로 받은 뒤, `SaveStructuredRequestInput.model_validate(kwargs)`로 검증한다. 모든 원본 tool arguments는 `structured_requests`에 저장하고, 일정/할 일/알림은 같은 tool 안에서 각각의 table에 정규화한다.

UI 좌측 대화 목록과 별개로 “추출된 일정/할 일/알림”이 실제 DB row로 남는지, 그리고 그 row가 어떤 `tool_call.arguments`에서 왔는지가 이번 주의 핵심 검증 포인트다.

## 실습 흐름

1. `notebook/3주차_나나의_기록장을_만들다.ipynb`에서 `SaveStructuredRequestInput` schema와 SQLite schema를 확인한다.
2. `SaveStructuredRequestInput`을 `save_structured_request` tool의 `args_schema`로 사용한다.
3. tool 함수가 `**kwargs`를 `SaveStructuredRequestInput`으로 검증한 뒤 저장하는지 확인한다.
4. `personal_schedule`, `group_schedule`은 `schedules` table에 저장한다.
5. `todo`는 `todos`, `reminder`는 `reminders` table에 저장한다.
6. `unknown`은 `structured_requests`에만 저장되는지 확인한다.
7. 저장 trace에서 `request_id`가 원본 tool arguments와 정규화 row를 연결하는지 확인한다.

## 관찰할 trace/payload

- `save_structured_request` tool call
- `tool_call.arguments`
- `tool_result.content`
- `structured_requests.payload_json`
- `schedules.schedule_type`
- `todos.priority`
- `reminders.start_time`
- `request_id`
- table별 row count

## 확인 질문

1. `SaveStructuredRequestInput(BaseModel)`이 tool 입력에서 맡는 역할은 무엇인가?
2. `tool_call.arguments`에서 모델이 구조화한 값은 무엇인가?
3. 원본 tool arguments를 `structured_requests.payload_json`에 남기는 이유는 무엇인가?
4. `personal_schedule`과 `group_schedule`을 같은 table에 저장하면서도 구분하려면 어떤 컬럼이 필요한가?
5. `unknown` 요청은 왜 정규화 table에 저장하지 않는가?

## 작은 응용 과제

개인 일정 요청을 하나 추가하고 `save_structured_request`가 호출되는지, `schedule_type`이 `personal_schedule`으로 저장되는지 확인한다.
