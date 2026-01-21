"""Message building utilities for LangChain service events."""


def build_event_message(event_type, kwargs):
	"""Build a descriptive message for the LangChain service based on event type."""
	if event_type == "course_progress":
		return f"Student progressed in course. Status: {kwargs.get('status')}"

	if event_type == "quiz_submission":
		return (
			f"Student submitted quiz '{kwargs.get('quiz_title')}'. "
			f"Score: {kwargs.get('score')}/{kwargs.get('score_out_of')} ({kwargs.get('percentage')}%)"
		)

	if event_type == "assignment_submission":
		return f"Student submitted assignment '{kwargs.get('assignment_title')}'"

	if event_type == "assignment_status_update":
		return (
			f"Assignment '{kwargs.get('assignment_title')}' status updated to: {kwargs.get('status')}. "
			f"Comments: {kwargs.get('comments') or 'None'}"
		)

	if event_type == "enrollment":
		return f"Student enrolled in course as {kwargs.get('member_type')}"

	if event_type == "certificate_issued":
		return f"Certificate issued for course '{kwargs.get('course_title')}'"

	return f"LMS event: {event_type}"
