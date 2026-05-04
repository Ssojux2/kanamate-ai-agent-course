from pathlib import Path

import nbformat


def test_learning_notebooks_are_valid_and_gradio_based():
    notebook_paths = sorted(Path("notebooks/learning").glob("*.ipynb"))
    assert len(notebook_paths) == 6

    for path in notebook_paths:
        nb = nbformat.read(path, as_version=4)
        nbformat.validate(nb)
        source = "\n".join(cell.get("source", "") for cell in nb.cells)
        assert "Streamlit" not in source
        assert "streamlit" not in source
        assert "/Users/ssojux2/Working/kakao_clone_coding" not in source
        assert "Gradio" in source

