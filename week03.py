"""Week 3 KanaMate Python practice and Gradio UI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

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
# ChromaDB 파일도 repo 아래 tmp에 두어 실습 후 상태를 확인하기 쉽게 한다.
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_WEEK03_CHROMA_DIR = PROJECT_ROOT / "tmp" / "week03_chroma"
DEFAULT_WEEK03_COLLECTION_NAME = "kanamate_week3_memories"


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------


def load_project_env() -> None:
    """Load the repo-root .env next to this weekly script."""
    # Chroma embedding과 ChatOpenAI가 같은 .env 값을 보도록 매번 루트 .env를 로드한다.
    load_dotenv(ENV_PATH, override=True)


def openai_model_name() -> str:
    # 답변 생성 모델 이름이다. embedding 모델 이름과 일부러 분리해 둔다.
    load_project_env()
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def openai_embedding_model_name() -> str:
    # ChromaDB가 문장을 벡터로 바꿀 때 사용할 embedding 모델 이름이다.
    load_project_env()
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)


def require_openai_api_key() -> str:
    # embedding API와 chat API 모두 같은 OPENAI_API_KEY를 사용한다.
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.")
    return api_key


def make_model(max_tokens: int = 500) -> ChatOpenAI:
    # Agent 답변용 모델과 embedding 모델은 .env에서 따로 바꿀 수 있다.
    require_openai_api_key()
    return ChatOpenAI(
        model=openai_model_name(),
        temperature=0,
        max_completion_tokens=max_tokens,
    )


def show_json(value: Any) -> None:
    # 검색 hit의 metadata/distance를 들여쓰기해서 비교하기 쉽게 출력한다.
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def final_text(agent_result: dict[str, Any]) -> str:
    # 최종 답변은 마지막 message에 있지만, 근거는 trace와 hits에서 따로 확인한다.
    return agent_result["messages"][-1].content


def extract_tool_trace(agent_result: dict[str, Any]) -> list[dict[str, Any]]:
    # Agentic RAG에서는 "검색 tool을 불렀는가"가 핵심 관찰 포인트다.
    trace: list[dict[str, Any]] = []
    for message in agent_result.get("messages", []):
        # 모델이 검색이 필요하다고 판단하면 search_memory tool_call이 생긴다.
        for call in getattr(message, "tool_calls", []) or []:
            trace.append(
                {
                    "event": "tool_call",
                    "tool_name": call.get("name"),
                    "arguments": call.get("args", {}),
                }
            )
        if getattr(message, "type", None) == "tool":
            # tool_result content 안의 hits가 답변 근거로 사용된다.
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
# 현재 실습에서 사용 중인 Chroma collection 위치를 UI에 보여주기 위해 보관한다.
memory_persist_dir = DEFAULT_WEEK03_CHROMA_DIR


def reset_memory_collection(memories: list[str] | None = None, persist_dir: str | Path | None = None) -> Any:
    # 매 실습마다 collection을 새로 만들어 "입력 메모 -> 검색 결과" 흐름을 깨끗하게 본다.
    global memory_collection, memory_persist_dir
    source_memories = memories or DEFAULT_STUDENT_MEMORIES
    # resolve()로 절대 경로를 저장해 UI에서 실제 파일 위치를 바로 확인할 수 있게 한다.
    target_dir = Path(persist_dir or DEFAULT_WEEK03_CHROMA_DIR).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    memory_persist_dir = target_dir

    embedding_function = OpenAIEmbeddingFunction(
        # ChromaDB는 문장을 vector로 바꿔 저장하므로 embedding API key가 필요하다.
        api_key=require_openai_api_key(),
        model_name=openai_embedding_model_name(),
    )
    client = chromadb.PersistentClient(path=str(target_dir), settings=Settings(anonymized_telemetry=False))
    try:
        # 이전 실습 collection이 남아 있으면 지우고 같은 이름으로 다시 만든다.
        client.delete_collection(DEFAULT_WEEK03_COLLECTION_NAME)
    except Exception as exc:
        if "does not exist" not in str(exc).lower():
            raise
    memory_collection = client.create_collection(
        name=DEFAULT_WEEK03_COLLECTION_NAME,
        embedding_function=embedding_function,
    )
    memory_collection.add(
        # ids/documents/metadatas는 검색 결과를 다시 사람이 읽을 수 있게 연결해준다.
        # ids는 고유 key, documents는 원문, metadatas는 출처/순서 같은 보조 정보다.
        ids=[f"memory-{index + 1}" for index in range(len(source_memories))],
        documents=source_memories,
        metadatas=[{"source": "student_input", "order": index + 1} for index, _ in enumerate(source_memories)],
    )
    return memory_collection


def get_memory_collection() -> Any:
    # collection을 아직 만들지 않았다면 기본 메모리로 한 번 초기화한다.
    global memory_collection
    if memory_collection is None:
        memory_collection = reset_memory_collection()
    return memory_collection


def format_chroma_results(found: dict[str, Any]) -> list[dict[str, Any]]:
    # Chroma query 결과는 중첩 리스트라 학생이 읽기 쉬운 list[dict]로 펴준다.
    # query_texts를 여러 개 넣을 수 있기 때문에 첫 번째 질문의 결과만 [0]으로 꺼낸다.
    ids = found.get("ids", [[]])[0]
    documents = found.get("documents", [[]])[0]
    distances = found.get("distances", [[]])[0]
    metadatas = found.get("metadatas", [[]])[0]
    return [
        {
            "id": ids[index],
            "content": documents[index],
            "distance": distances[index],
            # metadata가 비어 있을 수도 있어 없으면 빈 dict로 맞춘다.
            "metadata": metadatas[index] if index < len(metadatas) and metadatas[index] else {},
        }
        for index in range(len(ids))
    ]


def memory_collection_state(collection: Any | None = None) -> dict[str, Any]:
    """Return the small ChromaDB state that students should inspect."""
    target_collection = collection or get_memory_collection()
    return {
        # persist_dir/count를 보면 실제로 vector DB가 준비됐는지 빠르게 확인할 수 있다.
        "persist_dir": str(memory_persist_dir),
        "collection_name": getattr(target_collection, "name", DEFAULT_WEEK03_COLLECTION_NAME),
        "count": target_collection.count(),
    }


def search_memory_hits(
    query: str,
    top_k: int = 2,
    collection: Any | None = None,
) -> list[dict[str, Any]]:
    """Return Chroma search results as a simple list of dictionaries."""
    target_collection = collection or get_memory_collection()

    # TODO 문제 1: ChromaDB collection에 질문을 검색한다.
    # 모범 답안 1:
    # query_texts는 여러 질문을 받을 수 있어 결과가 한 번 더 리스트로 감싸진다.
    # n_results는 가장 가까운 기억을 몇 개까지 가져올지 정한다.
    found = target_collection.query(query_texts=[query], n_results=top_k)

    # TODO 문제 2: ids/documents/metadatas/distances를 학생이 읽기 쉬운 모양으로 바꾼다.
    # 모범 답안 2:
    hits = format_chroma_results(found)

    # TODO 문제 3: agent tool trace와 직접 검색 결과가 같은 형식이 되게 반환한다.
    # 모범 답안 3:
    return hits


@tool("search_memory", description="수강생이 입력한 메모를 검색하고 단순한 hit 리스트로 돌려준다.")
def search_memory(query: str, top_k: int = 2) -> str:
    """Search student memory with ChromaDB."""
    # TODO 문제 4: Agentic RAG에서 사용할 검색 tool을 단일 함수로 등록한다.
    # 모범 답안 4:
    # tool이 호출되면 별도 wrapper 없이 현재 Chroma collection을 바로 검색한다.
    target_collection = get_memory_collection()
    found = target_collection.query(query_texts=[query], n_results=top_k)
    hits = format_chroma_results(found)
    # TODO 문제 5: 검색 결과 hits를 JSON 문자열 payload로 반환한다.
    # 모범 답안 5:
    # agent trace에서 이 JSON 문자열을 보면 어떤 근거가 모델에게 전달됐는지 알 수 있다.
    return json.dumps({"hits": hits}, ensure_ascii=False)


def build_week03_agent(max_tokens: int = 700):
    # Agent는 모듈에 등록된 search_memory tool을 그대로 받는다.

    return create_agent(
        model=make_model(max_tokens),
        # TODO 문제 6: agent가 필요할 때 호출할 검색 tool을 tools 목록에 넣는다.
        # 모범 답안 6:
        tools=[search_memory],
        system_prompt="저장된 메모가 필요한 질문이면 search_memory 도구를 호출한 뒤, 찾은 근거를 바탕으로 답한다.",
    )


def run_ui(question: str, memories_text: str):
    try:
        # Textbox의 여러 줄 입력을 ChromaDB에 넣을 메모 리스트로 바꾼다.
        # 빈 줄은 실습 데이터가 아니므로 제거한다.
        memories = [line.strip() for line in memories_text.splitlines() if line.strip()]
        if not memories:
            return "검색할 메모를 한 줄 이상 입력하세요.", [], {}, []
        reset_memory_collection(memories)
        # 직접 검색 결과와 agent trace 안 검색 결과를 나란히 볼 수 있게 둘 다 만든다.
        # direct hits는 RAG 검색 자체를, trace는 agent가 검색 tool을 선택했는지를 보여준다.
        hits = search_memory_hits(question, top_k=min(2, len(memories)))
        state = memory_collection_state()
        rag_agent = build_week03_agent()
        result = rag_agent.invoke({"messages": [{"role": "user", "content": question}]})
        return final_text(result), hits, state, extract_tool_trace(result)
    except Exception as exc:
        return str(exc), [], {}, []


def append_user_message(question: str, history: list[dict[str, str]] | None):
    # 빠른 callback: Chroma/agent 검색 전에 사용자 질문을 먼저 채팅에 표시한다.
    history = list(history or [])
    cleaned_question = question.strip()
    if not cleaned_question:
        return history, history, ""
    history.append({"role": "user", "content": cleaned_question})
    return history, history, ""


def run_chat_response(history: list[dict[str, str]] | None, memories_text: str):
    # 느린 callback: 마지막 질문으로 검색/agent 실행을 마친 뒤 assistant 답변을 추가한다.
    history = list(history or [])
    if not history or history[-1].get("role") != "user":
        return history, history, [], {}, []

    question = history[-1]["content"]
    answer, hits, state, trace = run_ui(question, memories_text)
    history.append({"role": "assistant", "content": answer})
    return history, history, hits, state, trace


def clear_chat():
    return [], [], "", [], {}, []


def create_demo() -> gr.Blocks:
    # 화면은 질문, 원본 메모, 검색 hit, collection 상태, tool trace를 함께 보여준다.
    with gr.Blocks(title="KanaMate Week 3", fill_width=True, fill_height=True) as demo:
        with gr.Column(scale=1, min_width=0):
            gr.Markdown("# KanaMate Week 3")
            history_state = gr.State([])
            chatbot = gr.Chatbot(
                label="KanaMate",
                show_label=False,
                layout="bubble",
                height=560,
                scale=1,
                min_width=0,
                placeholder="",
            )
            with gr.Accordion("메모", open=False):
                memories = gr.Textbox(
                    label="메모",
                    show_label=False,
                    lines=5,
                    min_width=0,
                    value=(
                        "프로젝트 발표는 2026-04-24 10:00에 민수와 지아가 함께 진행한다.\n"
                        "카나메이트 UI에서는 채팅 답변과 tool trace를 함께 보여준다."
                    ),
                )
            with gr.Row(equal_height=True):
                question = gr.Textbox(
                    label="메시지",
                    show_label=False,
                    value="카나메이트 UI에서는 무엇을 함께 보여줘?",
                    scale=8,
                    min_width=0,
                )
                run_button = gr.Button("전송", variant="primary", scale=1, min_width=96)
                clear_button = gr.Button("초기화", scale=1, min_width=96)
            with gr.Accordion("실행 상세", open=False):
                hits_json = gr.JSON(label="검색 hit 리스트")
                state_json = gr.JSON(label="ChromaDB collection 상태")
                trace_json = gr.JSON(label="검색 Tool Trace")

        chat_outputs = [chatbot, history_state, question, hits_json, state_json, trace_json]
        user_outputs = [chatbot, history_state, question]
        response_outputs = [chatbot, history_state, hits_json, state_json, trace_json]
        run_button.click(
            append_user_message,
            inputs=[question, history_state],
            outputs=user_outputs,
            queue=False,
            show_progress="hidden",
        ).then(run_chat_response, inputs=[history_state, memories], outputs=response_outputs)
        question.submit(
            append_user_message,
            inputs=[question, history_state],
            outputs=user_outputs,
            queue=False,
            show_progress="hidden",
        ).then(run_chat_response, inputs=[history_state, memories], outputs=response_outputs)
        clear_button.click(clear_chat, outputs=chat_outputs)
    return demo


if __name__ == "__main__":
    create_demo().launch()
