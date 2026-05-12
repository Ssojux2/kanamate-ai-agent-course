#!/usr/bin/env bash

# 수강생이 매번 같은 conda env와 Jupyter kernel을 쓰게 하는 준비 스크립트다.
# Source this file from the repo root:
#   source scripts/use_langchain_env.sh

set -euo pipefail

if ! command -v conda >/dev/null 2>&1; then
  echo "conda 명령을 찾지 못했습니다. Anaconda/Miniconda를 먼저 활성화하세요." >&2
  return 1 2>/dev/null || exit 1
fi

# conda shell hook을 로드해야 non-interactive shell에서도 conda activate가 동작한다.
CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate langchain

# Jupyter가 "Python (langchain)" kernel을 보게 하려고 기존 kernel을 새로 등록한다.
KERNEL_DIR="$(
  python - <<'PY'
from pathlib import Path
from jupyter_core.paths import jupyter_data_dir

print(Path(jupyter_data_dir()) / "kernels" / "langchain")
PY
)"
rm -rf "$KERNEL_DIR"
python -m ipykernel install --user --name langchain --display-name "Python (langchain)" >/dev/null

echo "Activated conda env: $CONDA_DEFAULT_ENV"
echo "Python: $(python -c 'import sys; print(sys.executable)')"
echo "Jupyter kernel registered: Python (langchain)"
