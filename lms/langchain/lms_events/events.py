"""Centralized LMS event type definitions."""

from enum import Enum


class EventType(str, Enum):
	"""Enumerates LMS event types sent to the LangChain service."""

	COURSE_PROGRESS = "course_progress"
	QUIZ_SUBMISSION = "quiz_submission"
	ASSIGNMENT_SUBMISSION = "assignment_submission"
	ASSIGNMENT_STATUS_UPDATE = "assignment_status_update"
	ENROLLMENT = "enrollment"
	CERTIFICATE_ISSUED = "certificate_issued"


__all__ = ["EventType"]

