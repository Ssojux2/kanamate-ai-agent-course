"""Week 4 Gradio UI."""

from __future__ import annotations

import gradio as gr

from exercises.week04_practice import run_mcp_event_request


def run_request(request: str):
    try:
        result = run_mcp_event_request(request)
        return result["answer"], result["created_event"], result["trace"]
    except Exception as exc:
        return str(exc), {}, []


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 4") as demo:
        gr.Markdown("# Week 4 - Real MCP Server")
        request = gr.Textbox(
            label="요청",
            value="민수와 지아의 발표 리허설을 2026-04-24 15:00 일정으로 생성해줘",
        )
        run_button = gr.Button("실행", variant="primary")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        event_json = gr.JSON(label="MCP 서버 생성 payload")
        trace_json = gr.JSON(label="MCP Tool Trace")

        run_button.click(run_request, inputs=request, outputs=[answer, event_json, trace_json])
    return demo


if __name__ == "__main__":
    create_demo().launch()

