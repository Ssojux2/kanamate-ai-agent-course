# 2주차. Structured Output과 Pydantic으로 요청 구조화하기

## 학습 목표

- 자유 문장 답변과 Pydantic 구조화 결과의 차이를 설명한다.
- `kind`에 따라 `schedule`, `todo`, `reminder`, `unknown` 중 어떤 필드를 읽어야 하는지 판단한다.
- 구조화 결과가 다음 앱 코드나 tool 입력으로 안전한지 확인한다.

## 핵심 개념

Structured output은 모델 답변을 앱에서 바로 쓰기 좋은 양식으로 받는 방법이다. "일정으로 보입니다" 같은 문장만 있으면 다음 코드가 어떤 값을 읽어야 할지 불안정하다. Pydantic 모델을 사용하면 `title`, `date`, `start_time`, `priority`, `minutes_before`처럼 정해진 필드로 결과를 검증할 수 있다.

이번 주에는 tool 실행보다 `structured_response.model_dump()`가 핵심 관찰값이다.

## 실습 흐름

1. `notebook/02_자연어를_구조화된_일정으로.ipynb`에서 `response_format`이 Pydantic 모델을 검증하는 흐름을 본다.
2. 노트북에 정의된 `ScheduleCreate`, `TodoCreate`, `ReminderCreate`, `PracticeExtractionResult` 구조를 확인한다.
3. 일정, 할 일, 알림, 애매한 질문을 각각 넣어 `kind`가 어떻게 달라지는지 본다.
4. `structured_payload_to_message`가 구조화 결과를 사용자 답변으로 바꾸는 방식을 확인한다.
5. 회고 셀에서 자유 문장 답변과 구조화 결과의 차이를 정리한다.

## 관찰할 trace/payload

- `structured_response`: Pydantic으로 검증된 결과 객체
- `kind`: `schedule`, `todo`, `reminder`, `unknown`
- `schedule`: `title`, `date`, `start_time`, `attendees`
- `todo`: `title`, `due_date`, `priority`
- `reminder`: `base_event`, `minutes_before`
- `unknown`: 앱 데이터로 바로 넣기 어려운 요청을 안전하게 분류한 결과

## 확인 질문

1. 자유 문장 답변을 그대로 앱 데이터로 쓰면 어떤 문제가 생길 수 있는가?
2. `kind="reminder"`일 때 반드시 확인해야 할 필드는 무엇인가?
3. `unknown` 결과는 실패인가, 아니면 안전한 분류인가?

## 작은 응용 과제

일정 요청, 할 일 요청, 알림 요청, 애매한 질문을 각각 실행한다. `kind`와 세부 객체가 어떻게 달라지는지 표로 정리한다.
