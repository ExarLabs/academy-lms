"""Message building utilities for LangChain service events."""

from lms.langchain.lms_events.events import EventType


def _normalize_event_type(event_type: str | EventType) -> str:
	"""Return the string value for an event type."""
	return event_type.value if isinstance(event_type, EventType) else event_type


def build_event_message(event_type: str | EventType, kwargs: dict) -> str:
	"""Build a descriptive message for the LangChain service based on event type."""
	event_type_value = _normalize_event_type(event_type)

	if event_type_value == EventType.COURSE_PROGRESS.value:
		return f"Student progressed in course. Status: {kwargs.get('status')}"

	if event_type_value == EventType.QUIZ_SUBMISSION.value:
		return (
			f"Student submitted quiz '{kwargs.get('quiz_title')}'. "
			f"Score: {kwargs.get('score')}/{kwargs.get('score_out_of')} ({kwargs.get('percentage')}%)"
		)

	if event_type_value == EventType.ASSIGNMENT_SUBMISSION.value:
		return f"Student submitted assignment '{kwargs.get('assignment_title')}'"

	if event_type_value == EventType.ASSIGNMENT_STATUS_UPDATE.value:
		return (
			f"Assignment '{kwargs.get('assignment_title')}' status updated to: {kwargs.get('status')}. "
			f"Comments: {kwargs.get('comments') or 'None'}"
		)

	if event_type_value == EventType.ENROLLMENT.value:
		return f"Student enrolled in course as {kwargs.get('member_type')}"

	if event_type_value == EventType.CERTIFICATE_ISSUED.value:
		return f"Certificate issued for course '{kwargs.get('course_title')}'"

	return f"LMS event: {event_type_value}"
