from exercises.week06_practice import practice_cases, run_practice_suite


def fake_runner(request: str, member_replies: str, mode: str):
    if mode == "group":
        selected_agent = "kana"
        tool_name = "group_confirm_slot"
    elif "메모" in request:
        selected_agent = "nana"
        tool_name = "memory_save"
    else:
        selected_agent = "nana"
        tool_name = "personal_create_schedule"
    return {
        "selected_agent": selected_agent,
        "answer": "ok",
        "trace": [{"event": "tool_call", "tool_name": f"{selected_agent}_agent", "arguments": {}}],
        "delegate_payload": {
            "agent": selected_agent,
            "trace": [{"event": "tool_call", "tool_name": tool_name, "arguments": {}}],
        },
    }


def test_week06_practice_suite_marks_all_cases_passed():
    reports = run_practice_suite(practice_cases, runner=fake_runner)

    assert len(reports) == 3
    assert all(report["passed"] for report in reports)

