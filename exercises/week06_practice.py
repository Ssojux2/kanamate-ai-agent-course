"""Week 6 practice: integrated golden scenario suite."""

from __future__ import annotations

from typing import Any, Callable

from kanamate_runtime.week06 import run_live_flow

practice_cases = [
    {
        "name": "personal_schedule",
        "mode": "personal",
        "request": "내일 11시에 민수와 1:1 일정 잡아줘",
        "member_replies": "",
        "expected_agent": "nana",
        "expected_inner_tool": "personal_create_schedule",
    },
    {
        "name": "memory_save",
        "mode": "personal",
        "request": "프로젝트 발표 장소는 3층 세미나실이라고 메모해줘",
        "member_replies": "",
        "expected_agent": "nana",
        "expected_inner_tool": "memory_save",
    },
    {
        "name": "group_slot",
        "mode": "group",
        "request": "팀 멤버들과 발표 리허설 시간을 조율해줘",
        "member_replies": "민수: 2026-04-24 15:00 가능\n지아: 2026-04-24 15:00 가능",
        "expected_agent": "kana",
        "expected_inner_tool": "group_confirm_slot",
    },
]


def run_practice_suite(
    cases: list[dict[str, Any]],
    runner: Callable[[str, str, str], dict[str, Any]] = run_live_flow,
) -> list[dict[str, Any]]:
    """Run Week 6 golden scenarios and return compact reports."""
    reports = []
    for case in cases:
        # TODO 1: case의 mode/request/member_replies로 run_live_flow를 호출한다.
        # 모범 답안 1(강의자료 테스트용)
        result = runner(case["request"], case.get("member_replies", ""), case.get("mode", "auto"))

        # TODO 2: delegate_payload 내부 trace에서 실제 sub-agent tool 이름을 모은다.
        # 모범 답안 2(강의자료 테스트용)
        inner_tool_names = [
            event["tool_name"]
            for event in result["delegate_payload"].get("trace", [])
            if event.get("event") == "tool_call"
        ]

        # TODO 3: 기대 agent/tool과 실제 결과를 한 report에 담는다.
        # 모범 답안 3(강의자료 테스트용)
        reports.append(
            {
                "name": case["name"],
                "expected_agent": case["expected_agent"],
                "selected_agent": result["selected_agent"],
                "expected_inner_tool": case["expected_inner_tool"],
                "inner_tool_names": inner_tool_names,
                "passed": (
                    case["expected_agent"] == result["selected_agent"]
                    and case["expected_inner_tool"] in inner_tool_names
                ),
                "answer": result["answer"],
                "trace": result["trace"],
                "delegate_payload": result["delegate_payload"],
            }
        )
    return reports

