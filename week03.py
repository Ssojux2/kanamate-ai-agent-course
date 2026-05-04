"""Week 3 KanaMate assignment and Gradio UI."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable

import chromadb
import gradio as gr
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load the repo-root .env next to this weekly script."""
    load_dotenv(ENV_PATH, override=False)


def openai_model_name() -> str:
    load_project_env()
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def openai_embedding_model_name() -> str:
    load_project_env()
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)


def require_openai_api_key() -> str:
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    return api_key


def make_model(max_tokens: int = 500) -> ChatOpenAI:
    require_openai_api_key()
    return ChatOpenAI(
        model=openai_model_name(),
        temperature=0,
        max_completion_tokens=max_tokens,
    )


def show_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def final_text(agent_result: dict[str, Any]) -> str:
    return agent_result["messages"][-1].content


def extract_tool_trace(agent_result: dict[str, Any]) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for message in agent_result.get("messages", []):
        for call in getattr(message, "tool_calls", []) or []:
            trace.append(
                {
                    "event": "tool_call",
                    "tool_name": call.get("name"),
                    "arguments": call.get("args", {}),
                }
            )
        if getattr(message, "type", None) == "tool":
            trace.append(
                {
                    "event": "tool_result",
                    "tool_name": getattr(message, "name", None),
                    "content": message.content,
                }
            )
    return trace

# ---------------------------------------------------------------------------
# Week 3. RAG / Agentic RAG
# ---------------------------------------------------------------------------


DEFAULT_STUDENT_MEMORIES = [
    "프로젝트 발표는 2026-04-24 10:00에 민수와 지아가 함께 진행한다.",
    "카나메이트 UI에서는 채팅 답변과 tool trace를 함께 보여준다.",
]
memory_collection: Any | None = None


def reset_memory_collection(memories: list[str] | None = None) -> Any:
    global memory_collection
    source_memories = memories or DEFAULT_STUDENT_MEMORIES
    embedding_function = OpenAIEmbeddingFunction(
        api_key=require_openai_api_key(),
        model_name=openai_embedding_model_name(),
    )
    client = chromadb.Client(Settings(anonymized_telemetry=False))
    memory_collection = client.create_collection(
        name=f"kanamate_week3_{uuid.uuid4().hex[:8]}",
        embedding_function=embedding_function,
    )
    memory_collection.add(
        ids=[f"memory-{index + 1}" for index in range(len(source_memories))],
        documents=source_memories,
        metadatas=[{"source": "student_input"} for _ in source_memories],
    )
    return memory_collection


def get_memory_collection() -> Any:
    global memory_collection
    if memory_collection is None:
        memory_collection = reset_memory_collection()
    return memory_collection


def format_chroma_results(found: dict[str, Any]) -> list[dict[str, Any]]:
    ids = found.get("ids", [[]])[0]
    documents = found.get("documents", [[]])[0]
    distances = found.get("distances", [[]])[0]
    return [
        {"id": ids[index], "content": documents[index], "distance": distances[index]}
        for index in range(len(ids))
    ]


def search_memory_hits(
    query: str,
    top_k: int = 2,
    collection: Any | None = None,
) -> list[dict[str, Any]]:
    """Return Chroma search results as a simple list of dictionaries."""
    target_collection = collection or get_memory_collection()

    # TODO 1: memory_collection.query로 검색한다.
    # 모범 답안 1(강의자료 테스트용)
    found = target_collection.query(query_texts=[query], n_results=top_k)

    # TODO 2: ids/documents/distances의 첫 번째 결과 묶음을 꺼낸다.
    # 모범 답안 2(강의자료 테스트용)
    hits = format_chroma_results(found)

    # TODO 3: 각 hit을 {id, content, distance} 모양으로 바꾼다.
    # 모범 답안 3(강의자료 테스트용)
    return hits


def build_week03_agent(search_hits: Callable[[str, int], list[dict[str, Any]]], max_tokens: int = 700):
    @tool("search_memory", description="학생이 입력한 메모를 검색하고 단순한 hit 리스트로 돌려준다.")
    def search_memory_with_helper(query: str, top_k: int = 2) -> str:
        """Search student memory with the practice helper."""
        return json.dumps({"hits": search_hits(query, top_k)}, ensure_ascii=False)

    return create_agent(
        model=make_model(max_tokens),
        tools=[search_memory_with_helper],
        system_prompt="저장된 메모가 필요한 질문이면 search_memory 도구를 호출한 뒤, 찾은 근거를 바탕으로 답한다.",
    )


def run_ui(question: str, memories_text: str):
    try:
        memories = [line.strip() for line in memories_text.splitlines() if line.strip()]
        if not memories:
            return "검색할 메모를 한 줄 이상 입력하세요.", [], []
        reset_memory_collection(memories)
        hits = search_memory_hits(question, top_k=min(2, len(memories)))
        rag_agent = build_week03_agent(search_memory_hits)
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
        run_button.click(run_ui, inputs=[question, memories], outputs=[answer, hits_json, trace_json])
    return demo


if __name__ == "__main__":
    create_demo().launch()
