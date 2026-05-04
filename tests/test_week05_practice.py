from exercises.week05_practice import run_supervisor_case
from tests.helpers import SequenceAgent, agent_result


def test_week05_reports_selected_agent_and_inner_tool():
    delegate_payload = {
        "agent": "kana",
        "answer": "그룹 시간을 확정했습니다.",
        "trace": [{"event": "tool_call", "tool_name": "group_confirm_slot", "arguments": {}}],
    }
    supervisor = SequenceAgent([agent_result("kana_agent", delegate_payload, "카나에게 위임했습니다.")])
    case = {
        "name": "group_slot",
        "request": "팀 회의 시간을 조율해줘",
        "member_replies": "민수: 15:00 가능\n지아: 15:00 가능",
        "expected_agent": "kana",
        "expected_inner_tool": "group_confirm_slot",
    }

    report = run_supervisor_case(case, supervisor_agent=supervisor)

    assert report["selected_agent"] == "kana"
    assert "group_confirm_slot" in report["inner_tool_names"]
    assert report["delegate_payload"]["agent"] == "kana"

