"""Document event handlers for LMS events that trigger LangChain service notifications."""

import frappe

from lms.langchain.lms_events.broker import broker
from lms.langchain.lms_events.events import EventType


def _get_course_for_assignment(
	doc_course: str | None,
	lesson: str | None,
	assignment: str | None,
) -> str | None:
	"""Get course for assignment submission, trying multiple sources.

	The course field in LMS Assignment Submission is a fetch_from field
	that may not be populated on after_insert. This tries multiple sources:
	1. doc.course (if already fetched)
	2. Course Lesson -> course
	3. LMS Assignment -> course

	Args:
		doc_course: The course value from the document (may be None).
		lesson: The lesson link field value.
		assignment: The assignment link field value.

	Returns:
		Course name or None.
	"""
	if doc_course:
		return doc_course
	if lesson:
		course = frappe.db.get_value("Course Lesson", lesson, "course")
		if course:
			return course
	if assignment:
		course = frappe.db.get_value("LMS Assignment", assignment, "course")
		if course:
			return course
	return None


def handle_course_progress_update(doc, method):
	"""Handler for LMS Course Progress on_update event."""
	broker.send(
		event_type=EventType.COURSE_PROGRESS.value,
		user_id=doc.member,
		course=doc.course,
		lesson=doc.lesson,
		chapter=doc.chapter,
		status=doc.status,
		member_name=doc.member_name,
	)


def handle_quiz_submission(doc, method):
	"""Handler for LMS Quiz Submission after_insert event."""
	broker.send(
		event_type=EventType.QUIZ_SUBMISSION.value,
		user_id=doc.member,
		course=doc.course,
		quiz=doc.quiz,
		quiz_title=doc.quiz_title,
		score=doc.score,
		score_out_of=doc.score_out_of,
		percentage=doc.percentage,
		passing_percentage=doc.passing_percentage,
		member_name=doc.member_name,
	)


def handle_assignment_submission(doc, method):
	"""Handler for LMS Assignment Submission after_insert event."""
	# course is a fetch_from field that may not be populated on after_insert
	course = _get_course_for_assignment(doc.course, doc.lesson, doc.assignment)
	broker.send(
		event_type=EventType.ASSIGNMENT_SUBMISSION.value,
		user_id=doc.member,
		course=course,
		lesson=doc.lesson,
		assignment=doc.assignment,
		assignment_title=doc.assignment_title,
		answer=doc.answer,
		question=doc.question,
		submission_type=doc.type,
		member_name=doc.member_name,
	)


def handle_assignment_status_update(doc, method):
	"""Handler for LMS Assignment Submission on_update event.

	Only triggers if the status field has changed.
	"""
	if not doc.has_value_changed("status"):
		return

	# course is a fetch_from field that may not be populated
	course = _get_course_for_assignment(doc.course, doc.lesson, doc.assignment)
	broker.send(
		event_type=EventType.ASSIGNMENT_STATUS_UPDATE.value,
		user_id=doc.member,
		course=course,
		lesson=doc.lesson,
		assignment=doc.assignment,
		assignment_title=doc.assignment_title,
		status=doc.status,
		comments=doc.comments,
		member_name=doc.member_name,
	)


def handle_enrollment(doc, method):
	"""Handler for LMS Enrollment after_insert event."""
	broker.send(
		event_type=EventType.ENROLLMENT.value,
		user_id=doc.member,
		course=doc.course,
		member_name=doc.member_name,
		member_type=doc.member_type,
	)


def handle_certificate_issued(doc, method):
	"""Handler for LMS Certificate after_insert event."""
	broker.send(
		event_type=EventType.CERTIFICATE_ISSUED.value,
		user_id=doc.member,
		course=doc.course,
		course_title=doc.course_title,
		issue_date=str(doc.issue_date) if doc.issue_date else None,
		batch_name=doc.batch_name,
		member_name=doc.member_name,
	)
