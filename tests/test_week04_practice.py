from exercises.week04_practice import run_mcp_event_request
from tests.helpers import SequenceAgent, agent_result


def test_week04_parses_created_event_payload():
    created_event = {
        "server": "kanamate-calendar",
        "tool": "calendar.create_event",
        "arguments": {
            "title": "발표 리허설",
            "date": "2026-04-24",
            "start_time": "15:00",
            "members": ["민수", "지아"],
        },
        "event_id": "event-2026-04-24-1500",
        "status": "created",
    }
    agent = SequenceAgent([agent_result("calendar_create_event", created_event, "생성했습니다.")])

    result = run_mcp_event_request("리허설 일정 생성해줘", agent=agent)

    assert result["created_event"] == created_event
    assert result["created_event"]["status"] == "created"
    assert result["trace"][0]["tool_name"] == "calendar_create_event"

