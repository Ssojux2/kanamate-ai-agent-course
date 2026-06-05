# 2주차. 자연어를 구조화된 요청으로

**부제:** Structured output

## 학습 목표

- Pydantic으로 사용자 요청을 `personal_schedule`, `group_schedule`, `todo`, `reminder`, `unknown`으로 구조화한다.
- `title`, `date`, `start_time`, `end_time`, `members`, `priority`, `reason`을 검증 가능한 payload로 만든다.
- 자유 문장 답변과 structured output payload의 차이를 설명한다.

## 핵심 개념

Structured output은 모델 답변을 앱에서 바로 쓰기 좋은 양식으로 받는 방법이다. 일정처럼 보이는 문장만 있으면 다음 코드가 어떤 값을 읽어야 할지 불안정하다. Pydantic 모델을 사용하면 요청 종류와 필드를 검증 가능한 객체로 받을 수 있다.

## 실습 흐름

1. `notebook/2주차_자연어를_구조화된_요청으로_만든다.ipynb`에서 `response_format`이 Pydantic 모델을 검증하는 흐름을 본다.
2. 개인 일정, 그룹 일정, 할 일, 알림, 애매한 질문을 각각 구조화한다.
3. `kind`에 따라 어떤 필드를 읽어야 하는지 확인한다.
4. `members`, `priority`, `reason`처럼 요청 종류에 따라 의미가 달라지는 필드를 비교한다.

## 관찰할 trace/payload

- `structured_response`
- `kind`: `personal_schedule`, `group_schedule`, `todo`, `reminder`, `unknown`
- `title`, `date`, `start_time`, `end_time`
- `members`, `priority`, `reason`

## 확인 질문

1. 자유 문장 답변을 그대로 앱 데이터로 쓰면 어떤 문제가 생길 수 있는가?
2. `personal_schedule`과 `group_schedule`은 어떤 필드에서 가장 크게 달라지는가?
3. `unknown` 결과는 실패인가, 아니면 안전한 분류인가?

## 작은 응용 과제

개인 일정, 그룹 일정, 할 일, 알림, 애매한 질문을 각각 넣고 `kind`와 세부 필드가 어떻게 달라지는지 표로 정리한다.
