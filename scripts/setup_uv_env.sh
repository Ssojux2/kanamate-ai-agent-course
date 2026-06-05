#!/usr/bin/env bash

# Prepare the uv-managed environment and register the course Jupyter kernel.
# Run this file from the repo root:
#   bash scripts/setup_uv_env.sh

set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv 명령을 찾지 못했습니다. https://docs.astral.sh/uv/getting-started/installation/ 안내에 따라 uv를 먼저 설치하세요." >&2
  exit 1
fi

uv sync
uv run python -m ipykernel install --user --name kanamate --display-name "Python (KanaMate)" >/dev/null

echo "uv environment synced."
echo "Python: $(uv run python -c 'import sys; print(sys.executable)')"
echo "Jupyter kernel registered: Python (KanaMate)"
