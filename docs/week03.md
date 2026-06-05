# 3주차. 나나의 기록장을 만들다

**부제:** 구조화된 출력을 SQLite에 저장

## 학습 목표

- Week 2의 structured output을 SQLite row로 저장한다.
- `structured_requests`, `schedules`, `todos`, `reminders` table의 역할을 구분한다.
- `kind`에 따라 알맞은 table에 정규화 저장되는지 확인한다.

## 핵심 개념

2주차 payload는 앱 코드에서 쓰기 좋은 객체지만, 조회와 추적을 위해서는 DB row로 남아야 한다. 모든 원본 structured output은 `structured_requests`에 저장하고, 일정/할 일/알림은 각각의 table에 정규화한다.

UI 좌측 대화 목록과 별개로 “추출된 일정/할 일/알림”이 실제 DB row로 남는지가 이번 주의 핵심 검증 포인트다.

## 실습 흐름

1. `notebook/3주차_나나의_기록장을_만들다.ipynb`에서 SQLite schema를 확인한다.
2. 예시 structured output payload를 준비한다.
3. `personal_schedule`, `group_schedule`은 `schedules` table에 저장한다.
4. `todo`는 `todos`, `reminder`는 `reminders` table에 저장한다.
5. 저장 trace에서 `request_id`가 원본 payload와 정규화 row를 연결하는지 확인한다.

## 관찰할 trace/payload

- `structured_requests.payload_json`
- `schedules.schedule_type`
- `todos.priority`
- `reminders.start_time`
- `request_id`
- table별 row count

## 확인 질문

1. 원본 payload를 `structured_requests`에 남기는 이유는 무엇인가?
2. `personal_schedule`과 `group_schedule`을 같은 table에 저장하면서도 구분하려면 어떤 컬럼이 필요한가?
3. `unknown` 요청은 왜 정규화 table에 저장하지 않는가?

## 작은 응용 과제

`unknown` payload를 하나 추가하고 `structured_requests`에만 저장되는지 확인한다.
