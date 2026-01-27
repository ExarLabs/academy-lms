"""Document event handlers for LMS events that trigger LangChain service notifications."""

from lms.langchain.lms_events.broker import broker


def handle_course_progress_update(doc, method):
	"""Handler for LMS Course Progress on_update event."""
	broker.send(
		event_type="course_progress",
		user_id=doc.member,
		course=doc.course,
		lesson=doc.lesson,
		chapter=doc.chapter,
		status=doc.status,
	)


def handle_quiz_submission(doc, method):
	"""Handler for LMS Quiz Submission after_insert event."""
	broker.send(
		event_type="quiz_submission",
		user_id=doc.member,
		course=doc.course,
		quiz=doc.quiz,
		quiz_title=doc.quiz_title,
		score=doc.score,
		score_out_of=doc.score_out_of,
		percentage=doc.percentage,
		passing_percentage=doc.passing_percentage,
	)


def handle_assignment_submission(doc, method):
	"""Handler for LMS Assignment Submission after_insert event."""
	broker.send(
		event_type="assignment_submission",
		user_id=doc.member,
		course=doc.course,
		lesson=doc.lesson,
		assignment=doc.assignment,
		assignment_title=doc.assignment_title,
		answer=doc.answer,
		question=doc.question,
		submission_type=doc.type,
	)


def handle_assignment_status_update(doc, method):
	"""Handler for LMS Assignment Submission on_update event.

	Only triggers if the status field has changed.
	"""
	if not doc.has_value_changed("status"):
		return

	broker.send(
		event_type="assignment_status_update",
		user_id=doc.member,
		course=doc.course,
		lesson=doc.lesson,
		assignment=doc.assignment,
		assignment_title=doc.assignment_title,
		status=doc.status,
		comments=doc.comments,
	)


def handle_enrollment(doc, method):
	"""Handler for LMS Enrollment after_insert event."""
	broker.send(
		event_type="enrollment",
		user_id=doc.member,
		course=doc.course,
		member_name=doc.member_name,
		member_type=doc.member_type,
	)


def handle_certificate_issued(doc, method):
	"""Handler for LMS Certificate after_insert event."""
	broker.send(
		event_type="certificate_issued",
		user_id=doc.member,
		course=doc.course,
		course_title=doc.course_title,
		issue_date=str(doc.issue_date) if doc.issue_date else None,
		batch_name=doc.batch_name,
	)
