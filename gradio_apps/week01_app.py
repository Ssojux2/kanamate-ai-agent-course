"""Week 1 Gradio UI."""

from __future__ import annotations

import gradio as gr

from exercises.week01_practice import run_student_schedule_request
from kanamate_runtime.week01 import reset_schedules


def run_request(request: str):
    try:
        result = run_student_schedule_request(request)
        return (
            f"{result['answer']}\n\n{result['list_answer']}",
            {"created_schedule": result["created_schedule"], "schedules": result["schedules"]},
            {"create_trace": result["trace"], "list_trace": result["list_trace"]},
        )
    except Exception as exc:
        return str(exc), {}, {}


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 1") as demo:
        gr.Markdown("# Week 1 - Schedule Tool Flow")
        request = gr.Textbox(label="요청", value="내일 10시에 민수와 회의 일정 잡아줘")
        run_button = gr.Button("실행", variant="primary")
        clear_button = gr.Button("일정 초기화")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        result_json = gr.JSON(label="완성 결과")
        trace_json = gr.JSON(label="Tool Trace")

        run_button.click(run_request, inputs=request, outputs=[answer, result_json, trace_json])
        clear_button.click(lambda: (reset_schedules(), "일정을 초기화했습니다.")[1], outputs=answer)
    return demo


if __name__ == "__main__":
    create_demo().launch()

