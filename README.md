# KanaMate Agentic AI Course

KanaMate는 개인 메이트 `나나(Nana)`와 그룹 메이트 `카나(Kana)`를 단계적으로 설계하는 6주 노트북 중심 agentic AI 과정입니다. 이 repo는 강의 흐름, 개념 설명, trace/payload 관찰 기준을 담고, 별도 Python 문제 파일은 다른 repo에서 관리합니다.

## 처음 시작하는 순서

1. 0주차 문서부터 읽고, 주차별 강의 정리 문서를 함께 확인합니다.
   - [docs/orientation.md](docs/orientation.md)
   - [docs/week01.md](docs/week01.md)
   - [docs/week02.md](docs/week02.md)
   - [docs/week03.md](docs/week03.md)
   - [docs/week04.md](docs/week04.md)
   - [docs/week05.md](docs/week05.md)
   - [docs/week06.md](docs/week06.md)

2. 노트북을 1주차부터 순서대로 엽니다.

```text
docs/orientation.md
-> docs/weekXX.md 주차별 강의 정리
-> notebook/ 주차별 노트북
```

3. `uv`로 실습 환경을 준비합니다.

```bash
bash scripts/setup_uv_env.sh
```

새 머신에서도 같은 명령을 실행하면 `pyproject.toml`과 `uv.lock` 기준으로 `.venv`가 만들어지고 Jupyter kernel이 등록됩니다.

```bash
uv sync
uv run python -m ipykernel install --user --name kanamate --display-name "Python (KanaMate)"
```

4. `.env` 파일을 준비합니다.

```bash
cp .env.example .env
```

`.env`에 OpenAI API key를 설정합니다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

5. Jupyter를 실행합니다.

```bash
uv run jupyter lab
# 또는
uv run jupyter notebook
```

Jupyter에서 kernel은 `Python (KanaMate)`를 선택합니다.

## uv 환경설정

이 repo는 `uv`가 `.venv` 가상환경을 만들고 관리하는 방식으로 실습 환경을 맞춥니다. Python 버전은 `.python-version`과 `pyproject.toml` 기준으로 Python 3.10 계열을 사용하고, 실제 패키지 버전은 `uv.lock` 기준으로 고정됩니다.

먼저 `uv`가 설치되어 있는지 확인합니다.

```bash
uv --version
```

명령이 실행되지 않으면 `uv`를 먼저 설치한 뒤 repo 루트에서 다음 스크립트를 실행합니다.

```bash
bash scripts/setup_uv_env.sh
```

이 스크립트는 세 가지 일을 합니다.

1. `uv sync`로 `pyproject.toml`과 `uv.lock` 기준의 `.venv`를 생성하거나 동기화합니다.
2. LangChain agent, OpenAI, ChromaDB, nbformat import가 정상인지 health check를 실행합니다.
3. Jupyter에서 선택할 `Python (KanaMate)` kernel을 등록합니다.

같은 작업을 직접 실행하려면 아래 명령을 사용합니다.

```bash
uv sync
uv run python - <<'PY'
from importlib.metadata import version

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

import chromadb
import nbformat

print("Environment health check passed.")
print(f"langchain: {version('langchain')}")
print(f"langgraph-prebuilt: {version('langgraph-prebuilt')}")
PY
uv run python -m ipykernel install --user --name kanamate --display-name "Python (KanaMate)"
```

처음 clone한 환경에서는 `.venv`가 새로 만들어집니다. 이미 `.venv`가 있는 환경에서는 `uv sync`가 현재 환경을 `pyproject.toml`과 `uv.lock`에 맞게 다시 정렬합니다.

LangChain 1.x agent import는 `langgraph-prebuilt` 전이 의존성 버전에 민감합니다. 이 repo는 노트북 재현성을 위해 `langgraph-prebuilt==1.0.8`을 직접 고정합니다. `from langchain.agents import create_agent`에서 `ExecutionInfo` import 오류가 나면 repo 루트에서 아래 명령으로 lockfile 기준 환경을 다시 맞춥니다.

```bash
uv sync --frozen
bash scripts/setup_uv_env.sh
```

실습에는 OpenAI API key가 필요하므로 `.env` 파일도 준비합니다.

```bash
cp .env.example .env
```

`.env`에는 실제 key 값만 직접 채우고, 예시는 다음 형식을 따릅니다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

환경 준비가 끝나면 Jupyter를 실행합니다.

```bash
uv run jupyter lab
# 또는
uv run jupyter notebook
```

Jupyter 화면에서 kernel은 `Python (KanaMate)`를 선택합니다. 이 kernel은 repo의 `.venv` Python을 사용합니다.

## 주차별 흐름

| 주차 | 주제 | 이번 주에 만드는 것 | 핵심 학습 포인트 |
| --- | --- | --- | --- |
| 1주차 | 나나를 깨우다 | Nana 개인 일정 tool | Tool call, tool result, 메모리 저장소 |
| 2주차 | 자연어를 구조화된 요청으로 | Pydantic structured output | `kind`, 검증 가능한 payload, unknown 처리 |
| 3주차 | 나나의 기록장을 만들다 | Structured output SQLite 저장 | 정규화 table, 원본 payload, `request_id` 연결 |
| 4주차 | 나나가 기억을 찾아오다 | Agentic RAG with ChromaDB + SQLite | ChromaDB 참고자료 검색, SQLite row 검색, RAG tool 선택 |
| 5주차 | 카나가 지난 대화를 불러오다 | MCP SQLite 이전 대화 검색 tool | MCP tool contract, 대화 검색, 일정 후보 추출 |
| 6주차 | 카나메이트가 약속을 결정하다 | Supervisor/Sub-agent 최종 일정 결정 | Delegate tool, Nana/Kana 책임 분리, 최종 후보 결정 |

## 과정에서 보는 핵심

- `personal_create_schedule`, `personal_list_schedules`, `personal_delete_schedule`: Nana 개인 일정 tool
- `structured_response`: Pydantic으로 검증된 `personal_schedule`, `group_schedule`, `todo`, `reminder`, `unknown` payload
- `structured_requests`, `schedules`, `todos`, `reminders`: structured output을 저장하는 SQLite table
- `search_personal_references`, `search_saved_requests`: ChromaDB/SQLite Agentic RAG tool
- `search_previous_conversations`, `load_conversation_messages`, `extract_schedules_from_history`: MCP SQLite 이전 대화 검색 tool
- `nana_agent`, `kana_agent`: supervisor가 호출하는 delegate tool

## Repo 구조

```text
notebook/                         # 1-6주차 학습 노트북
pyproject.toml                    # uv 프로젝트 의존성 정의
uv.lock                           # uv 재현 환경 lockfile
.python-version                   # uv가 사용할 Python 버전
scripts/setup_uv_env.sh           # uv sync + Jupyter kernel 등록
docs/orientation.md               # 0주차 오리엔테이션
docs/week01.md                    # 1주차 강의 정리
docs/week02.md                    # 2주차 강의 정리
docs/week03.md                    # 3주차 강의 정리
docs/week04.md                    # 4주차 강의 정리
docs/week05.md                    # 5주차 강의 정리
docs/week06.md                    # 6주차 강의 정리
```

## 노트북 목록

- 1주차 나나를 깨우다: [notebook/1주차_나나를_깨우다.ipynb](notebook/1주차_나나를_깨우다.ipynb)
- 2주차 자연어를 구조화된 요청으로: [notebook/2주차_자연어를_구조화된_요청으로_만든다.ipynb](notebook/2주차_자연어를_구조화된_요청으로_만든다.ipynb)
- 3주차 나나의 기록장을 만들다: [notebook/3주차_나나의_기록장을_만들다.ipynb](notebook/3주차_나나의_기록장을_만들다.ipynb)
- 4주차 나나가 기억을 찾아오다: [notebook/4주차_나나가_기억을_찾아오다.ipynb](notebook/4주차_나나가_기억을_찾아오다.ipynb)
- 5주차 카나가 지난 대화를 불러오다: [notebook/5주차_카나가_지난대화를_불러오다.ipynb](notebook/5주차_카나가_지난대화를_불러오다.ipynb)
- 6주차 카나메이트가 약속을 결정하다: [notebook/6주차_카나메이트가_약속을_결정하다.ipynb](notebook/6주차_카나메이트가_약속을_결정하다.ipynb)

## API 비용과 quota 주의

모든 주차 노트북은 LangChain 기반 흐름을 기준으로 실제 OpenAI API key를 확인합니다. API key, billing, quota가 정상이어야 합니다.

- 1, 2, 3, 5, 6주차는 `ChatOpenAI`와 LangChain `create_agent` 실행이 포함됩니다.
- 4주차는 `ChatOpenAI` agent 실행과 ChromaDB embedding 호출이 포함됩니다.

`insufficient_quota`, billing, rate limit 오류가 나면 API key, billing, usage limit, 현재 uv 환경을 먼저 확인하세요.

## 검증 명령

다음 검증은 노트북 JSON이 정상인지 확인합니다.

```bash
uv run python - <<'PY'
import nbformat
from pathlib import Path

for path in sorted(Path("notebook").glob("*.ipynb")):
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)
    print(path, "valid")
PY
```

## 완료 기준

수강생은 최종적으로 다음을 할 수 있어야 합니다.

- 개인 일정 tool의 생성/조회/삭제 trace를 설명한다.
- 사용자 요청을 검증 가능한 structured output payload로 구조화한다.
- structured output을 SQLite table에 정규화 저장하는 이유를 설명한다.
- ChromaDB 참고자료 검색과 SQLite 저장 요청 검색의 차이를 말한다.
- MCP SQLite tool로 이전 대화와 일정 정보를 검색하는 흐름을 설명한다.
- Supervisor/Sub-agent 구조에서 최종 회의 시간을 결정하는 trace를 검증한다.
