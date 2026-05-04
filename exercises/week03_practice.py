"""Week 3 practice: normalize vector-search hits."""

from __future__ import annotations

from typing import Any

from kanamate_runtime.week03 import format_chroma_results, get_memory_collection


def search_memory_hits(
    query: str,
    top_k: int = 2,
    collection: Any | None = None,
) -> list[dict[str, Any]]:
    """Return Chroma search results as a simple list of dictionaries."""
    memory_collection = collection or get_memory_collection()

    # TODO 1: memory_collection.query로 검색한다.
    # 모범 답안 1(강의자료 테스트용)
    found = memory_collection.query(query_texts=[query], n_results=top_k)

    # TODO 2: ids/documents/distances의 첫 번째 결과 묶음을 꺼낸다.
    # 모범 답안 2(강의자료 테스트용)
    hits = format_chroma_results(found)

    # TODO 3: 각 hit을 {id, content, distance} 모양으로 바꾼다.
    # 모범 답안 3(강의자료 테스트용)
    return hits

