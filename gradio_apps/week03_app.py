"""Week 3 Gradio UI."""

from __future__ import annotations

import gradio as gr

from exercises.week03_practice import search_memory_hits
from kanamate_runtime.common import extract_tool_trace, final_text
from kanamate_runtime.week03 import build_practice_rag_agent, reset_memory_collection


def run_request(question: str, memories_text: str):
    try:
        memories = [line.strip() for line in memories_text.splitlines() if line.strip()]
        if not memories:
            return "검색할 메모를 한 줄 이상 입력하세요.", [], []
        reset_memory_collection(memories)
        hits = search_memory_hits(question, top_k=min(2, len(memories)))
        rag_agent = build_practice_rag_agent(search_memory_hits)
        result = rag_agent.invoke({"messages": [{"role": "user", "content": question}]})
        return final_text(result), hits, extract_tool_trace(result)
    except Exception as exc:
        return str(exc), [], []


def create_demo() -> gr.Blocks:
    with gr.Blocks(title="KanaMate Week 3") as demo:
        gr.Markdown("# Week 3 - Memory Search Helper")
        question = gr.Textbox(label="질문", value="카나메이트 UI에서는 무엇을 함께 보여줘?")
        memories = gr.Textbox(
            label="메모",
            lines=4,
            value=(
                "프로젝트 발표는 2026-04-24 10:00에 민수와 지아가 함께 진행한다.\n"
                "카나메이트 UI에서는 채팅 답변과 tool trace를 함께 보여준다."
            ),
        )
        run_button = gr.Button("검색 Agent 실행", variant="primary")
        answer = gr.Textbox(label="모델 최종 답변", lines=5)
        hits_json = gr.JSON(label="검색 hit 리스트")
        trace_json = gr.JSON(label="검색 Tool Trace")

        run_button.click(run_request, inputs=[question, memories], outputs=[answer, hits_json, trace_json])
    return demo


if __name__ == "__main__":
    create_demo().launch()

