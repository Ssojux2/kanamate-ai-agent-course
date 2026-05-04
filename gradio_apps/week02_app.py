"""Week 2 Gradio UI."""

from __future__ import annotations

import gradio as gr

from exercises.week02_practice import run_student_structured_request


def run_request(request: str):
    try:
        response = run_student_structured_request(request)
        return response.model_dump()
    except Exception as exc:
        return {"error": str(exc)}


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 2") as demo:
        gr.Markdown("# Week 2 - Structured Output")
        request = gr.Textbox(label="요청", value="발표 30분 전에 알려줘")
        run_button = gr.Button("구조화 실행", variant="primary")
        result_json = gr.JSON(label="Pydantic Response")

        run_button.click(run_request, inputs=request, outputs=result_json)
    return demo


if __name__ == "__main__":
    create_demo().launch()

