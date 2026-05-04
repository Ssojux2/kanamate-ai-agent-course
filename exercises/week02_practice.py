"""Week 2 practice: structured output with Pydantic."""

from __future__ import annotations

from typing import Any

from kanamate_runtime.week02 import PracticeExtractionResult, build_practice_extract_agent


def run_student_structured_request(
    request: str,
    agent: Any | None = None,
) -> PracticeExtractionResult:
    """Run the extended structured-output agent and return its Pydantic response."""
    practice_extract_agent = agent or build_practice_extract_agent()

    # TODO 1: practice_extract_agent.invoke로 request를 실행한다.
    # 모범 답안 1(강의자료 테스트용)
    result = practice_extract_agent.invoke({"messages": [{"role": "user", "content": request}]})

    # TODO 2: result에서 structured_response를 꺼낸다.
    # 모범 답안 2(강의자료 테스트용)
    response = result["structured_response"]

    # TODO 3: UI와 자동 점검에서 재사용할 Pydantic 객체를 돌려준다.
    # 모범 답안 3(강의자료 테스트용)
    return response

