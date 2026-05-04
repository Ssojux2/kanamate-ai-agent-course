"""Week 5 Gradio UI."""

from __future__ import annotations

import gradio as gr

from exercises.week05_practice import run_supervisor_case


def run_request(request: str, member_replies: str):
    try:
        expected_agent = "kana" if member_replies.strip() else "nana"
        expected_inner_tool = "group_confirm_slot" if expected_agent == "kana" else "personal_create_schedule"
        report = run_supervisor_case(
            {
                "name": "ui_case",
                "request": request,
                "member_replies": member_replies,
                "expected_agent": expected_agent,
                "expected_inner_tool": expected_inner_tool,
            }
        )
        return (
            report["answer"],
            {
                "selected_agent": report["selected_agent"],
                "inner_tool_names": report["inner_tool_names"],
            },
            {"delegate_payload": report["delegate_payload"], "supervisor_trace": report["trace"]},
        )
    except Exception as exc:
        return str(exc), {}, {}


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 5") as demo:
        gr.Markdown("# Week 5 - Supervisor Harness")
        request = gr.Textbox(label="요청", value="팀 회의 시간을 조율해줘")
        member_replies = gr.Textbox(
            label="멤버 응답",
            lines=4,
            value="민수: 2026-04-24 10:00 가능\n지아: 2026-04-24 10:00 가능",
        )
        run_button = gr.Button("실행", variant="primary")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        selected_json = gr.JSON(label="선택된 Agent와 내부 Tool")
        trace_json = gr.JSON(label="Supervisor/Sub-Agent Tool Trace")

        run_button.click(
            run_request,
            inputs=[request, member_replies],
            outputs=[answer, selected_json, trace_json],
        )
    return demo


if __name__ == "__main__":
    create_demo().launch()

