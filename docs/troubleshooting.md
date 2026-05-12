# Troubleshooting

이 문서는 카나메이트 과정에서 자주 만나는 오류를 빠르게 확인하기 위한 가이드다. 오류가 나면 먼저 증상 문장을 찾고, 확인 명령을 실행한 뒤 해결을 적용한다.

## 1. `.env` 미설정

| 항목 | 내용 |
| --- | --- |
| 증상 | `.env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.` |
| 원인 | repo 루트에 `.env`가 없거나 `OPENAI_API_KEY` 값이 비어 있음 |
| 해결 | `cp .env.example .env` 후 API key 입력 |
| 확인 명령 | `python -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print(bool(os.getenv('OPENAI_API_KEY')))"` |

## 2. OpenAI quota 또는 billing 오류

| 항목 | 내용 |
| --- | --- |
| 증상 | `insufficient_quota`, `Error code: 429`, billing 관련 오류 |
| 원인 | OpenAI 계정 credit, billing, rate limit 문제 |
| 해결 | OpenAI dashboard에서 billing과 usage limit 확인 |
| 확인 명령 | `python week01.py` 또는 1주차만 `KANAMATE_OFFLINE=1 python week01.py` |

주의: 오프라인 fallback은 `week01.py` 실습에만 있다. 2-6주차는 실제 API 호출이 필요하다.

## 3. `ModuleNotFoundError`

| 항목 | 내용 |
| --- | --- |
| 증상 | `ModuleNotFoundError: No module named 'gradio'` 같은 오류 |
| 원인 | 가상환경을 켜지 않았거나 requirements 설치가 안 됨 |
| 해결 | `conda activate langchain` 후 필요하면 `conda env update -f environment.yml --prune` 실행 |
| 확인 명령 | `python -c "import gradio, langchain, chromadb, pydantic; print('ok')"` |

## 4. Jupyter kernel 문제

| 항목 | 내용 |
| --- | --- |
| 증상 | 노트북에서 설치한 패키지를 못 찾거나 다른 Python을 사용함 |
| 원인 | Jupyter kernel이 `langchain` conda env가 아님 |
| 해결 | `source scripts/use_langchain_env.sh` 실행 후 노트북에서 `Python (langchain)` kernel 선택 |
| 확인 명령 | 노트북 셀에서 `import sys; print(sys.executable)` |

## 5. ChromaDB embedding 오류

| 항목 | 내용 |
| --- | --- |
| 증상 | 3주차에서 embedding, collection, persistent client, query 관련 오류 |
| 원인 | API key 문제, embedding model 설정 문제, ChromaDB 설치 문제, `tmp/week03_chroma` 쓰기 권한 문제 |
| 해결 | `.env`의 `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL=text-embedding-3-small` 확인 후 `environment.yml`로 환경 갱신. 임시 DB가 꼬였으면 Gradio/Jupyter를 끈 뒤 `tmp/week03_chroma`를 삭제하고 다시 실행 |
| 확인 명령 | `python -c "import chromadb; print(chromadb.__version__)"` |

## 6. MCP 서버 tool 로드 실패

| 항목 | 내용 |
| --- | --- |
| 증상 | 4주차에서 MCP tool을 찾지 못하거나 `http://127.0.0.1:8004/mcp` 연결 실패 |
| 원인 | 별도 터미널에서 `python week04_mcp_server.py`를 실행하지 않았거나, `mcp`, `langchain-mcp-adapters` 설치가 맞지 않음 |
| 해결 | 터미널 1에서 `python week04_mcp_server.py`를 먼저 실행하고, 터미널 2나 Jupyter에서 4주차 코드를 다시 실행 |
| 확인 명령 | `python -m compileall week04.py week04_mcp_server.py` |

## 7. SQLite 저장 row가 보이지 않음

| 항목 | 내용 |
| --- | --- |
| 증상 | 4주차에서 MCP payload는 보이지만 SQLite 저장 row가 비어 있음 |
| 원인 | `calendar_create_event`가 호출되지 않았거나, MCP 서버와 클라이언트가 서로 다른 `KANAMATE_WEEK04_DB_PATH`를 보고 있음 |
| 해결 | 요청 문장에 "일정으로 생성"처럼 생성 의도를 분명히 넣고, 서버와 Gradio/Jupyter를 같은 환경 변수로 다시 실행 |
| 확인 명령 | `python -c "from week04 import load_saved_calendar_events; print(load_saved_calendar_events())"` |

## 8. Gradio 포트 충돌

| 항목 | 내용 |
| --- | --- |
| 증상 | Gradio 실행 시 포트가 이미 사용 중이라는 오류 |
| 원인 | 이전 Gradio 서버가 아직 실행 중 |
| 해결 | 이전 터미널에서 `Ctrl+C`로 종료하거나 다른 주차 UI를 하나씩 실행 |
| 확인 명령 | `ps aux | grep gradio` |

## 9. 4주차 MCP 포트 충돌

| 항목 | 내용 |
| --- | --- |
| 증상 | `python week04_mcp_server.py` 실행 시 8004 포트가 이미 사용 중이라는 오류 |
| 원인 | 이전 MCP 서버가 아직 실행 중이거나 다른 프로세스가 8004 포트를 사용 중 |
| 해결 | 이전 서버를 `Ctrl+C`로 종료하거나, 서버와 클라이언트 양쪽에 같은 `KANAMATE_WEEK04_MCP_PORT` 값을 설정 |
| 확인 명령 | `KANAMATE_WEEK04_MCP_PORT=8014 python week04_mcp_server.py` |

## 10. `StructuredTool does not support sync invocation`

| 항목 | 내용 |
| --- | --- |
| 증상 | 4주차 MCP tool이나 agent 실행 중 `NotImplementedError: StructuredTool does not support sync invocation` 발생 |
| 원인 | MCP에서 로드한 LangChain `StructuredTool`은 async 호출만 지원하는데 `invoke(...)`로 실행함 |
| 해결 | 직접 tool 호출은 `run_async(tool.ainvoke(...))`, agent 호출은 `run_async(agent.ainvoke(...))`를 사용 |
| 확인 명령 | `rg -n "practice_mcp_agent.invoke|mcp_agent.invoke|tool.invoke" notebook/04_mcp_tool_call_gradio_ui.ipynb week04.py` |

## 11. 노트북 import 경로 문제

| 항목 | 내용 |
| --- | --- |
| 증상 | 준비 셀에서 repo root를 찾지 못함 |
| 원인 | 노트북을 repo 밖에서 열었거나 현재 작업 경로가 repo 내부가 아님 |
| 해결 | repo 루트에서 Jupyter를 실행하고 노트북의 1번 준비 셀을 먼저 실행 |
| 확인 명령 | 노트북 셀에서 `import sys; print(sys.path[:3])` |

## 12. 그래도 해결되지 않을 때

다음 정보를 함께 정리한다.

- 실행한 명령
- 전체 오류 메시지
- 사용 중인 노트북 또는 파일명
- `python --version`
- `pip show langchain langchain-openai gradio chromadb`
- `python -c "import sqlite3; print(sqlite3.sqlite_version)"`
- `.env`에 key가 있는지 여부. 실제 key 값은 공유하지 않는다.
