# KanaMate AI Agent Course

KanaMate는 개인 메이트 `나나(Nana)`와 그룹 메이트 `카나(Kana)`를 단계적으로 만드는 6주 실습형 AI Agent 과정입니다.

## Structure

```text
notebooks/learning/   # 학습 노트북
kanamate_app.py       # 주차별 실습 함수와 전체 Gradio WebUI
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

각 노트북의 6번 실습은 단일 파일 `kanamate_app.py`를 import해 실행합니다.

## Run Gradio UI

```bash
python kanamate_app.py
```

실행하면 1-6주차 탭이 있는 Gradio UI가 열립니다.

## Validate

```bash
python -m compileall kanamate_app.py
python - <<'PY'
import nbformat
from pathlib import Path

for path in sorted(Path("notebooks/learning").glob("*.ipynb")):
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)

import kanamate_app
demo = kanamate_app.create_demo()
print(type(demo).__name__)
PY
```

위 검증은 실제 API 호출 없이 문법, 노트북 JSON, Gradio 객체 생성을 확인합니다. 실제 OpenAI API 호출 smoke test는 `.env` 설정 후 노트북이나 Gradio UI에서 직접 확인합니다.

## GitHub

Private repo 기준:

```bash
git init -b main
git add .
git commit -m "Prepare KanaMate course materials"
gh repo create Ssojux2/kanamate-ai-agent-course --private --source=. --remote=origin --push
```

실제 `.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.
