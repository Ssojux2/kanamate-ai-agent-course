# KanaMate Agentic AI Course

KanaMate는 개인 메이트 `나나(Nana)`와 그룹 메이트 `카나(Kana)`를 단계적으로 만드는 6주 실습형 agentic AI 과정입니다. 이 repo는 에이전트에 익숙하지 않은 수강생이 agentic AI를 "작동시켜 보는 것"에서 멈추지 않고, tool trace와 structured payload를 읽으며 동작을 설명할 수 있게 만드는 데 초점을 둡니다.

## 처음 시작하는 순서

1. 0주차 문서부터 읽고, 주차별 강의 정리 문서를 함께 확인합니다.
   - [docs/orientation.md](docs/orientation.md)
   - [docs/week01.md](docs/week01.md)
   - [docs/week02.md](docs/week02.md)
   - [docs/week03.md](docs/week03.md)
   - [docs/week04.md](docs/week04.md)
   - [docs/week05.md](docs/week05.md)
   - [docs/week06.md](docs/week06.md)

   코드를 처음 읽을 때는 다음 순서를 권장합니다.

   ```text
   docs/orientation.md
   -> docs/weekXX.md 주차별 강의 정리
   -> notebook/ 주차별 노트북
   -> weekXX.py 주차별 Python 실습/Gradio 데모
   ```

   별도 실습 파일을 따로 찾지 않습니다. 노트북에서 개념을 보고 바로 같은 주차의 `weekXX.py`를 실행하며 trace와 payload를 확인합니다.
   `weekXX.py` 안의 `# TODO 문제`를 먼저 읽고 직접 생각한 뒤, 바로 아래 `# 모범 답안`과 비교합니다.

2. `langchain` conda 가상환경을 사용합니다.

```bash
conda activate langchain
source scripts/use_langchain_env.sh
```

새 머신에서 같은 환경을 다시 만들 때는 repo에 저장된 `environment.yml`을 사용합니다.

```bash
conda env create -f environment.yml
conda activate langchain
source scripts/use_langchain_env.sh
```

3. `.env` 파일을 준비합니다.

```bash
cp .env.example .env
```

`.env`에 OpenAI API key를 설정합니다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

4. 설치와 파일 상태를 확인합니다.

```bash
python -m compileall week01.py week02.py week03.py week04.py week05.py week06.py
jupyter lab
# 또는
jupyter notebook
```

## 과정에서 보는 핵심

일반 챗봇은 답변 문장을 만드는 데 집중하지만, agentic AI는 필요한 도구를 고르고, 인자를 만들고, 실행 결과를 받아 다음 행동을 정합니다. 이 과정에서는 매주 다음 값을 먼저 확인합니다.

- `trace`: 모델이 어떤 tool을 어떤 인자로 호출했는지
- `structured_response`: 자유 문장이 아니라 앱에서 쓰기 좋은 구조화 결과인지
- `payload`: 외부 도구나 MCP 서버가 실제로 돌려준 실행 결과인지
- `hits`와 `distance`: ChromaDB가 검색한 기억 후보와 근거 점수
- `saved_events`: MCP 서버가 SQLite에 실제로 저장한 일정 row
- `saved_memories`: Nana가 `memory_save`로 SQLite에 실제로 저장한 메모 row
- `selected_agent`: supervisor가 어떤 sub-agent에게 위임했는지
- `inner_tool_names`: sub-agent 내부에서 어떤 tool이 실행됐는지

## Repo 구조

```text
notebook/                  # 1-6주차 학습 노트북
environment.yml            # langchain conda 환경 재현 파일
scripts/use_langchain_env.sh # langchain env 활성화 + Jupyter kernel 등록
week01.py                  # 1주차 Python 실습 + Gradio UI
week02.py                  # 2주차 Python 실습 + Gradio UI
week03.py                  # 3주차 Python 실습 + Gradio UI
week04.py                  # 4주차 Python 실습 + Gradio UI
week04_mcp_server.py       # 4주차 별도 실행 MCP HTTP 서버
week05.py                  # 5주차 Python 실습 + Gradio UI
week06.py                  # 6주차 Python 실습 + Gradio UI
docs/orientation.md        # 0주차 오리엔테이션
docs/week01.md             # 1주차 강의 정리
docs/week02.md             # 2주차 강의 정리
docs/week03.md             # 3주차 강의 정리
docs/week04.md             # 4주차 강의 정리
docs/week05.md             # 5주차 강의 정리
docs/week06.md             # 6주차 강의 정리
```

## 노트북과 Python 파일

주차별 강의 정리 문서는 그 주에 무엇을 배워야 하고 어떤 trace/payload를 봐야 하는지 요약합니다. 노트북은 개념과 가장 작은 실행 흐름을 보여줍니다. 노트북을 실행한 뒤에는 같은 주차의 `weekXX.py`를 열어 `# TODO 문제`를 먼저 풀어 보고, 바로 아래 `# 모범 답안`과 비교합니다. 그 다음 터미널에서 실행해 Gradio UI와 trace를 확인합니다.

`week01.py`부터 `week06.py`는 독립 실행 가능한 주차별 Python 실습 파일입니다. 특히 1주차는 노트북을 본 뒤 바로 터미널에서 실행합니다.

```bash
conda activate langchain
python week01.py
```

OpenAI quota가 부족할 때 1주차 흐름만 로컬 fallback으로 확인하려면 다음처럼 실행합니다.

```bash
KANAMATE_OFFLINE=1 python week01.py
```

4주차는 MCP 서버와 실습 코드를 분리해서 실행합니다. 먼저 터미널 하나에서 MCP 서버를 켜 둡니다.

```bash
python week04_mcp_server.py
```

그 다음 다른 터미널이나 Jupyter에서 4주차 노트북 또는 Gradio UI를 실행합니다.

## 노트북 실행

`Jupyter Notebook` 또는 `JupyterLab`에서 `notebook/` 아래 노트북을 1주차부터 순서대로 실행합니다.

```bash
jupyter lab
# 또는
jupyter notebook
```

각 노트북은 다음 흐름을 따릅니다.

- 목표와 오늘의 큰 그림
- 반드시 이해할 것 / 지금은 몰라도 되는 것
- 기본 개념 실습
- KanaMate 확장 예제
- 개념 확인 질문과 작은 응용 과제

## Gradio UI 실행

주차별 Python 실습과 Gradio 데모는 다음 명령으로 실행합니다.

```bash
python week01.py
python week02.py
python week03.py
python week04.py
python week05.py
python week06.py
```

각 파일을 실행하면 해당 주차 Gradio UI가 열립니다. UI는 최종 답변만 보는 화면이 아니라 tool trace, payload, selected agent를 함께 관찰하는 학습 화면입니다.

4주차 Gradio UI를 실행할 때는 별도 터미널에서 `python week04_mcp_server.py`가 먼저 실행 중이어야 합니다.

## API 비용과 quota 주의

이 과정은 실제 OpenAI API를 호출합니다. API key, billing, quota가 정상이어야 합니다.

1주차 실습 파일(`week01.py`)만 quota 오류에 대해 오프라인 fallback을 제공합니다.

```bash
KANAMATE_OFFLINE=1 python week01.py
```

2-6주차는 실제 모델 호출과 embedding 호출이 필요합니다. `insufficient_quota`, billing, rate limit 오류가 나면 API key, billing, usage limit, 현재 가상환경을 먼저 확인하세요.

## 검증 명령

다음 검증은 실제 API 호출 없이 문법, 노트북 JSON, Gradio 객체 생성을 확인합니다.

```bash
python -m compileall week01.py week02.py week03.py week04.py week05.py week06.py
python - <<'PY'
import nbformat
from pathlib import Path

for path in sorted(Path("notebook").glob("*.ipynb")):
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)
    print(path, "valid")

for module_name in ["week01", "week02", "week03", "week04", "week05", "week06"]:
    module = __import__(module_name)
    demo = module.create_demo()
    print(module_name, type(demo).__name__)
PY
```

4주차 SQLite 저장 흐름은 API 호출 없이 MCP tool을 직접 호출해 확인할 수 있습니다. 먼저 다른 터미널에서 MCP 서버를 실행해 둡니다.

```bash
python week04_mcp_server.py
```

```bash
python - <<'PY'
from week04 import load_calendar_mcp_tools, load_saved_calendar_events, mcp_tool_by_name, parse_mcp_tool_result, run_async, write_calendar_mcp_server

write_calendar_mcp_server(include_create_event=True)
tools = load_calendar_mcp_tools()
tool = mcp_tool_by_name(tools, "calendar_create_event")
payload = parse_mcp_tool_result(run_async(tool.ainvoke({
    "title": "발표 리허설",
    "date": "2026-04-24",
    "start_time": "15:00",
    "members": ["민수", "지아"],
})))
print(payload["event_id"], load_saved_calendar_events()[-1]["event_id"])
PY
```

## 완료 기준

수강생은 최종적으로 다음을 할 수 있어야 합니다.

- 일반 챗봇과 agentic AI의 차이를 설명한다.
- tool call trace에서 `tool_call`과 `tool_result`를 구분한다.
- structured output이 왜 앱 개발에 필요한지 설명한다.
- ChromaDB collection에 메모를 저장하고 RAG/Agentic RAG의 차이를 예시로 말한다.
- MCP tool이 Python 함수 tool과 어떻게 다른지, MCP payload와 SQLite 저장 row를 근거로 설명한다.
- supervisor와 sub-agent 라우팅 결과를 trace로 검증한다.
- KanaMate 최종 WebUI에서 입력, 선택 agent, 내부 tool, SQLite 저장 메모, 최종 답변, 실패 가능성을 설명한다.
