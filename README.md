# KanaMate AI Agent Course

KanaMate는 개인 메이트 `나나(Nana)`와 그룹 메이트 `카나(Kana)`를 단계적으로 만드는 6주 실습형 AI Agent 과정입니다.

## Structure

```text
notebooks/learning/   # 학습 노트북
week01.py             # 1주차 과제 + Gradio UI
week02.py             # 2주차 과제 + Gradio UI
week03.py             # 3주차 과제 + Gradio UI
week04.py             # 4주차 과제 + Gradio UI
week05.py             # 5주차 과제 + Gradio UI
week06.py             # 6주차 과제 + Gradio UI
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

각 노트북의 6번 실습은 같은 주차의 `weekXX.py` 파일을 import해 실행합니다.

## Run Gradio UI

```bash
python week01.py
python week02.py
python week03.py
python week04.py
python week05.py
python week06.py
```

각 파일을 실행하면 해당 주차 Gradio UI가 바로 열립니다.

## Validate

```bash
python -m compileall week01.py week02.py week03.py week04.py week05.py week06.py
python - <<'PY'
import nbformat
from pathlib import Path

for path in sorted(Path("notebooks/learning").glob("*.ipynb")):
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)

for module_name in ["week01", "week02", "week03", "week04", "week05", "week06"]:
    module = __import__(module_name)
    demo = module.create_demo()
    print(module_name, type(demo).__name__)
PY
```

위 검증은 실제 API 호출 없이 문법, 노트북 JSON, Gradio 객체 생성을 확인합니다. 실제 OpenAI API 호출 smoke test는 `.env` 설정 후 해당 주차 노트북이나 `weekXX.py` Gradio UI에서 직접 확인합니다.

## GitHub

Private repo 기준:

```bash
git init -b main
git add .
git commit -m "Prepare KanaMate course materials"
gh repo create Ssojux2/kanamate-ai-agent-course --private --source=. --remote=origin --push
```

실제 `.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.
