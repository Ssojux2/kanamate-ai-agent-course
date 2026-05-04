"""Week 6 Gradio UI."""

from __future__ import annotations

import gradio as gr

from exercises.week06_practice import practice_cases, run_practice_suite
from kanamate_runtime.week06 import run_live_flow


def run_live(student_request: str, member_replies: str, mode: str):
    try:
        result = run_live_flow(student_request, member_replies, mode)
        return (
            result["answer"],
            {"selected_agent": result["selected_agent"], "delegate_payload": result["delegate_payload"]},
            result["trace"],
        )
    except Exception as exc:
        return str(exc), {}, []


def run_suite():
    try:
        reports = run_practice_suite(practice_cases)
        summary = [
            {
                "name": report["name"],
                "expected_agent": report["expected_agent"],
                "selected_agent": report["selected_agent"],
                "expected_inner_tool": report["expected_inner_tool"],
                "inner_tool_names": report["inner_tool_names"],
                "passed": report["passed"],
            }
            for report in reports
        ]
        return summary
    except Exception as exc:
        return [{"error": str(exc)}]


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 6") as demo:
        gr.Markdown("# Week 6 - Integrated KanaMate Demo")
        with gr.Tab("Live Flow"):
            mode = gr.Radio(["auto", "personal", "group"], value="auto", label="모드")
            student_request = gr.Textbox(label="요청", value="팀 멤버들과 발표 리허설 시간을 조율해줘")
            member_replies = gr.Textbox(
                label="멤버 응답",
                lines=4,
                value="민수: 2026-04-24 15:00 가능\n지아: 2026-04-24 15:00 가능",
            )
            run_button = gr.Button("실행", variant="primary")
            answer = gr.Textbox(label="모델 최종 답변", lines=5)
            payload_json = gr.JSON(label="선택된 Agent와 delegate payload")
            trace_json = gr.JSON(label="Supervisor Trace")
            run_button.click(
                run_live,
                inputs=[student_request, member_replies, mode],
                outputs=[answer, payload_json, trace_json],
            )

        with gr.Tab("Golden Scenario"):
            suite_button = gr.Button("시나리오 실행", variant="primary")
            suite_json = gr.JSON(label="시나리오 결과")
            suite_button.click(run_suite, outputs=suite_json)
    return demo


if __name__ == "__main__":
    create_demo().launch()

