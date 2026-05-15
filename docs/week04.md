# 4주차. SQLite로 대화 목록과 메시지 관리하기

## 학습 목표

- SQLite 파일에 대화 목록과 메시지 로그를 저장한다.
- `conversations`와 `messages` table의 역할을 구분한다.
- 노트북에서 보이는 대화 목록이 실제 SQLite row와 이어지는지 확인한다.

## 핵심 개념

4주차는 외부 tool이나 MCP를 붙이기 전에, 앱이 대화 상태를 어떻게 저장하는지 먼저 다룬다. 사용자가 메시지를 보내면 화면의 채팅 기록만 바뀌는 것이 아니라, SQLite의 `conversations` row와 `messages` row가 함께 갱신된다.

중요한 관찰 대상은 모델 답변이 아니라 저장 구조다. 대화 하나는 `conversation_id`로 식별하고, 여러 메시지는 같은 `conversation_id`를 외래키처럼 공유한다. 대화를 보관해도 메시지는 삭제하지 않고 `status="archived"`로 표시한다.

## 실습 흐름

1. `notebook/04_나나에게_손과_발을_달아주다.ipynb`에서 SQLite schema와 기본 저장 흐름을 확인한다.
2. 노트북의 `initialize_conversation_db`, `create_conversation`, `append_message` 셀을 실행한다.
3. `list_conversations`로 대화 목록, 메시지 수, 마지막 메시지 preview를 확인한다.
4. `load_conversation`으로 특정 대화의 메시지 로그를 시간순으로 조회한다.
5. `archive_conversation`으로 대화를 보관 처리하고 active 목록에서 빠지는지 본다.

## 관찰할 trace/payload

- `conversation_id`: 대화 하나를 식별하는 고유 값
- `message_id`: 메시지 하나를 식별하는 고유 값
- `conversations.status`: `active` 또는 `archived`
- `message_count`: 한 대화에 저장된 메시지 수
- `last_message`: 목록에서 빠르게 확인하는 마지막 메시지 preview
- `messages.role`: `user`, `assistant`, `system` 중 누가 남긴 메시지인지
- `updated_at`: 새 메시지 저장이나 보관 처리 때 갱신되는 시간

## 확인 질문

1. 대화 목록 table과 메시지 table을 나누는 이유는 무엇인가?
2. `conversation_id`가 대화 목록과 메시지 로그를 어떻게 연결하는가?
3. 보관 처리와 삭제는 사용자 경험과 데이터 검증에서 어떻게 다른가?
4. `message_count`와 `last_message`는 어떤 화면을 만들 때 유용한가?

## 작은 응용 과제

대화 두 개를 만들고 각각 메시지를 저장한다. 하나만 보관한 뒤 active 목록과 전체 목록 결과가 어떻게 다른지 비교한다.
