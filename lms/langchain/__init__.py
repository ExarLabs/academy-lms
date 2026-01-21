"""LangChain integration module for Frappe LMS.

This module provides:
- Event-driven integration with external LangChain service
- AI Tutor chat functionality
- Document event handlers for LMS events
"""

# Config
from lms.langchain.config import get_ai_tutor_url, get_langchain_service_url

# Message broker
from lms.langchain.broker import LangchainMessageBroker, broker

# Event handlers
from lms.langchain.lms_event_handlers import (
	handle_assignment_status_update,
	handle_assignment_submission,
	handle_certificate_issued,
	handle_course_progress_update,
	handle_enrollment,
	handle_quiz_submission,
)

# API endpoints
from lms.langchain.api import post_langchain_response, send_frontend_event
from lms.langchain.tutor import ask_tutor

# Service functions
from lms.langchain.service import send_to_langchain_service

# Message utilities
from lms.langchain.messages import build_event_message

__all__ = [
	# Config
	"get_langchain_service_url",
	"get_ai_tutor_url",
	# Broker
	"LangchainMessageBroker",
	"broker",
	# Event handlers
	"handle_course_progress_update",
	"handle_quiz_submission",
	"handle_assignment_submission",
	"handle_assignment_status_update",
	"handle_enrollment",
	"handle_certificate_issued",
	# API
	"post_langchain_response",
	"send_frontend_event",
	"ask_tutor",
	# Service
	"send_to_langchain_service",
	# Messages
	"build_event_message",
]
