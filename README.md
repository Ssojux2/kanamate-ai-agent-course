# KanaMate AI Agent Course

KanaMate는 개인 메이트 `나나(Nana)`와 그룹 메이트 `카나(Kana)`를 단계적으로 만드는 6주 실습형 AI Agent 과정입니다.

## Structure

```text
notebooks/learning/   # 학습 노트북
exercises/            # 주차별 Python 실습 파일
kanamate_runtime/     # 공통 helper, tool, agent factory
gradio_apps/          # 주차별 Gradio WebUI
tests/                # API 호출 없이 돌릴 수 있는 구조 검증 테스트
docs/course_plan.md   # 6주 과정 계획
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에 `OPENAI_API_KEY`를 설정합니다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Run Notebooks

Jupyter에서 `notebooks/learning/` 아래 노트북을 1주차부터 순서대로 실행합니다.

```bash
jupyter lab
```

각 노트북의 6번 실습은 대응되는 `exercises/weekXX_practice.py` 파일을 import해 실행합니다.

## Run Gradio Apps

```bash
python -m gradio_apps.week01_app
python -m gradio_apps.week02_app
python -m gradio_apps.week03_app
python -m gradio_apps.week04_app
python -m gradio_apps.week05_app
python -m gradio_apps.week06_app
```

## Validate

```bash
python -m compileall exercises kanamate_runtime gradio_apps
pytest
```

`pytest`는 fake agent와 fake collection을 사용해 API key 없이 구조를 검증합니다. 실제 OpenAI API 호출 smoke test는 `.env` 설정 후 노트북이나 Gradio 앱에서 직접 확인합니다.

## GitHub

Private repo 기준:

```bash
git init -b main
git add .
git commit -m "Prepare KanaMate course materials"
gh repo create Ssojux2/kanamate-ai-agent-course --private --source=. --remote=origin --push
```

실제 `.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.

