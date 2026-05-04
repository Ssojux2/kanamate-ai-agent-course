# 카나메이트(KanaMate) 6주 과정 계획

이 문서는 카나메이트 6주 과정을 학습 노트북과 단일 Python 실습/WebUI 파일로 구성한 현재 구조를 설명한다.

## 1. 과정 목표

카나메이트는 개인 메이트 `나나(Nana)`와 그룹 메이트 `카나(Kana)`로 구성된 AI 일정·협업 비서다.

| 메이트 | 역할 |
| --- | --- |
| 나나 | 개인 일정, 할 일, 메모 저장과 검색 기반 질의응답 |
| 카나 | 그룹 멤버 응답을 바탕으로 가능한 시간을 찾고 그룹 일정을 확정 |

학생은 Function call, Tool call, Structured output, Pydantic, RAG, Agentic RAG, 실제 로컬 MCP 서버 tool call, Sub-agent, Gradio WebUI 흐름을 실제 API 호출 기반으로 설명할 수 있어야 한다.

## 2. Repo 구조

```text
notebooks/learning/
  01_llm_agent_function_tool_call.ipynb
  02_structured_output_pydantic.ipynb
  03_rag_agentic_rag.ipynb
  04_mcp_tool_call_gradio_ui.ipynb
  05_subagent_skills_md_harness.ipynb
  06_webui_subagent.ipynb
kanamate_app.py
```

원칙:

- `.env`의 `OPENAI_API_KEY`를 필수로 사용한다.
- `OPENAI_MODEL` 기본값은 `gpt-4o-mini`, `OPENAI_EMBEDDING_MODEL` 기본값은 `text-embedding-3-small`이다.
- 노트북은 학습 흐름과 실행 예시를 제공하고, 코드 작성형 실습은 `kanamate_app.py`에서 실행한다.
- Gradio 앱은 `python kanamate_app.py` 명령으로 실행한다.
- `kanamate_app.py` 하나에 1-6주차 실습 함수, 공통 helper, tool, agent factory, Gradio 탭 UI를 함께 둔다.
- private 강의 repo 기준으로 모범 답안 주석과 구현은 단일 실습 파일에 유지한다.

## 3. 노트북 공통 구성

| 섹션 | 내용 |
| --- | --- |
| 0. 목표 | 이번 주 학습 목표와 완성 결과 |
| 1. 준비 | API key 확인, 공통 import, helper 함수 |
| 2. 개념 | 핵심 개념 요약 |
| 3. 기본 개념 실습 | 실제 API 호출이 포함된 가장 작은 핵심 개념 예제 |
| 4. 카나메이트 확장 예제 | 기본 개념에 이번 주 추가 기능 1개를 붙여 카나메이트 맥락으로 확장 |
| 5. 확장 예제 실행 | 4번에서 추가한 같은 기능을 실행하고 trace, route, structured response, 저장 상태 확인 |
| 6. 코드 작성형 실습(.py 파일) | `kanamate_app.py`의 주차별 helper를 실행 |
| 6-0. 실습 자동 점검 | 모델 문구가 아니라 trace, structured response, payload를 assert로 확인 |
| 6-1. 로컬 Gradio UI 실습 | `python kanamate_app.py`로 전체 WebUI를 실행 |
| 7. 회고 | 배운 점과 다음 주 연결 포인트 |

## 4. 6주 로드맵

| 주차 | 주제 | 결과물 |
| --- | --- | --- |
| 1주차 | Function call, Tool call 기본 구조 | 일정 생성에 목록 조회 기능을 추가하고 Gradio에서 생성 결과와 목록 표시 |
| 2주차 | Structured output, Pydantic | schedule/todo 구조화에 reminder 타입을 추가하고 Gradio에서 Pydantic 객체 표시 |
| 3주차 | RAG, Agentic RAG | 메모 검색 결과를 `search_memory_hits` helper로 정리하고 Gradio에서 답변과 hit 표시 |
| 4주차 | 실제 로컬 MCP 서버, Gradio UI | FastMCP 서버에 가능 시간 조회와 일정 생성 도구를 등록하고 Gradio에서 MCP payload 표시 |
| 5주차 | Sub-agent와 역할 분리 | Supervisor 라우팅을 Golden Scenario 하네스로 점검하고 Gradio에서 선택 agent와 내부 trace 표시 |
| 6주차 | WebUI 통합 데모 | 나나/카나 통합 flow를 최종 시나리오 세트로 점검하고 Gradio에서 실행 |

## 5. 테스트 전략

- `python -m compileall kanamate_app.py`로 Python 문법을 확인한다.
- 노트북 JSON 유효성을 검사한다.
- Gradio 앱은 import 시 API 호출 없이 `create_demo()`가 생성되는지 확인한다.
- 실제 OpenAI API 호출이 필요한 노트북 실행은 `.env` 설정 후 수동 smoke test로 수행한다.

## 6. 완료 기준

- 6개 학습 노트북은 `notebooks/learning/` 아래에 있으며 hard-coded local path를 포함하지 않는다.
- 각 주차 실습은 `kanamate_app.py`에서 실행된다.
- WebUI는 `python kanamate_app.py` 하나로 실행된다.
- `.env`는 Git에 포함하지 않고 `.env.example`만 제공한다.
- private GitHub repo `Ssojux2/kanamate-ai-agent-course`에 올릴 수 있는 README, requirements, ignore 파일이 준비되어 있다.
