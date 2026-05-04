"""Week 3 RAG setup helpers."""

from __future__ import annotations

import json
import uuid
from typing import Any, Callable

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain.agents import create_agent
from langchain.tools import tool

from kanamate_runtime.common import (
    make_model,
    openai_embedding_model_name,
    require_openai_api_key,
)

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


def build_practice_rag_agent(search_hits: Callable[[str, int], list[dict[str, Any]]], max_tokens: int = 700):
    @tool("search_memory", description="학생이 입력한 메모를 검색하고 단순한 hit 리스트로 돌려준다.")
    def search_memory_with_helper(query: str, top_k: int = 2) -> str:
        """Search student memory with the practice helper."""
        return json.dumps({"hits": search_hits(query, top_k)}, ensure_ascii=False)

    return create_agent(
        model=make_model(max_tokens),
        tools=[search_memory_with_helper],
        system_prompt="저장된 메모가 필요한 질문이면 search_memory 도구를 호출한 뒤, 찾은 근거를 바탕으로 답한다.",
    )

