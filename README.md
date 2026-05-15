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

3. `langchain` conda 가상환경을 사용합니다.

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
jupyter lab
# 또는
jupyter notebook
```

## 과정에서 보는 핵심

- `trace`: 모델이 어떤 tool을 어떤 인자로 호출했는지
- `structured_response`: 자유 문장이 아니라 앱에서 쓰기 좋은 구조화 결과인지
- `hits`와 `distance`: ChromaDB가 검색한 기억 후보와 근거 점수
- `conversation_id`, `message_id`: SQLite 대화 저장소에서 목록과 메시지가 연결되는지
- `mcp_payload`: MCP 서버가 돌려줘야 하는 실행 결과 모양
- `selected_agent`: supervisor가 어떤 sub-agent에게 위임했는지
- `inner_tool_names`: sub-agent 내부에서 어떤 tool이 실행됐는지

## Repo 구조

```text
notebook/                         # 1-6주차 학습 노트북
environment.yml                   # langchain conda 환경 재현 파일
scripts/use_langchain_env.sh      # langchain env 활성화 + Jupyter kernel 등록
docs/orientation.md               # 0주차 오리엔테이션
docs/week01.md                    # 1주차 강의 정리
docs/week02.md                    # 2주차 강의 정리
docs/week03.md                    # 3주차 강의 정리
docs/week04.md                    # 4주차 강의 정리
docs/week05.md                    # 5주차 강의 정리
docs/week06.md                    # 6주차 강의 정리
```

## 노트북 목록

- [notebook/01_나나를_깨우다.ipynb](notebook/01_나나를_깨우다.ipynb)
- [notebook/02_자연어를_구조화된_일정으로.ipynb](notebook/02_자연어를_구조화된_일정으로.ipynb)
- [notebook/03_기억하고_대화하는_나나.ipynb](notebook/03_기억하고_대화하는_나나.ipynb)
- [notebook/04_나나에게_손과_발을_달아주다.ipynb](notebook/04_나나에게_손과_발을_달아주다.ipynb)
- [notebook/05_카나의_자율_약속_잡기.ipynb](notebook/05_카나의_자율_약속_잡기.ipynb)
- [notebook/06_카나메이트_세상에_나가다.ipynb](notebook/06_카나메이트_세상에_나가다.ipynb)

## API 비용과 quota 주의

일부 노트북은 실제 OpenAI API를 호출합니다. API key, billing, quota가 정상이어야 합니다.

- 4주차는 SQLite-only 실습이라 OpenAI API를 호출하지 않습니다.
- 5주차와 6주차 노트북은 구현 문제 대신 payload/trace 기준을 설명하는 형태입니다.

`insufficient_quota`, billing, rate limit 오류가 나면 API key, billing, usage limit, 현재 가상환경을 먼저 확인하세요.

## 검증 명령

다음 검증은 노트북 JSON이 정상인지 확인합니다.

```bash
python - <<'PY'
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

- 일반 챗봇과 agentic AI의 차이를 설명한다.
- tool call trace에서 `tool_call`과 `tool_result`를 구분한다.
- structured output이 왜 앱 개발에 필요한지 설명한다.
- ChromaDB collection에 메모를 저장하고 RAG/Agentic RAG의 차이를 예시로 말한다.
- SQLite에서 대화 목록과 메시지 로그를 분리해 저장하는 이유를 설명한다.
- MCP tool이 Python 함수 tool과 어떻게 다른지 MCP payload를 근거로 설명한다.
- supervisor와 sub-agent 라우팅 결과를 trace로 검증한다.
