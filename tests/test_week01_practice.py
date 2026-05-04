from exercises.week01_practice import run_student_schedule_request
from tests.helpers import SequenceAgent, agent_result


def test_week01_extracts_created_schedule_and_list_snapshot():
    schedule = {
        "id": "schedule-1",
        "title": "회의",
        "date": "2026-04-24",
        "start_time": "10:00",
        "attendees": ["민수"],
    }
    agent = SequenceAgent(
        [
            agent_result("create_schedule", {"ok": True, "schedule": schedule}, "생성했습니다."),
            agent_result("list_schedules", {"ok": True, "schedules": [schedule]}, "목록입니다."),
        ]
    )

    result = run_student_schedule_request("내일 10시에 민수와 회의 일정 잡아줘", agent=agent)

    assert result["created_schedule"] == schedule
    assert result["schedules"] == [schedule]
    assert result["trace"][0]["tool_name"] == "create_schedule"
    assert result["list_trace"][0]["tool_name"] == "list_schedules"

