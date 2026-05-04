from exercises.week02_practice import run_student_structured_request
from kanamate_runtime.week02 import PracticeExtractionResult, ReminderCreate


class FakeStructuredAgent:
    def invoke(self, payload):
        return {
            "structured_response": PracticeExtractionResult(
                kind="reminder",
                reminder=ReminderCreate(title="발표 알림", related_event="발표", offset_minutes=30),
            )
        }


def test_week02_returns_pydantic_structured_response():
    response = run_student_structured_request("발표 30분 전에 알려줘", agent=FakeStructuredAgent())

    assert response.kind == "reminder"
    assert response.reminder is not None
    assert response.reminder.offset_minutes == 30

