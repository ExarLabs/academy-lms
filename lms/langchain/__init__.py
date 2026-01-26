"""LangChain integration module for Frappe LMS.

This module provides:
- Event-driven integration with external LangChain service
- AI Tutor chat functionality with streaming support
- Document event handlers for LMS events
- Repository pattern for data persistence
"""

# Config
from lms.langchain.config import (
	get_ai_tutor_url,
	get_langchain_service_url,
	use_redis_mode,
)

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

# Repositories
from lms.langchain.repositories import (
	get_response_by_request_id,
	response_exists,
	save_langchain_response,
)

# Event response subscriber (for document events)
from lms.langchain.event_response_subscriber import (
	EventResponseSubscriber,
	ensure_subscriber_running,
	get_subscriber,
	start_event_response_subscriber,
	stop_event_response_subscriber,
)

# Tutor stream subscriber (for AI Tutor streaming responses)
from lms.langchain.tutor_stream_subscriber import (
	TutorStreamSubscriber,
	create_tutor_stream_subscriber,
	# Backward compatibility aliases
	StreamingResponseHandler,
	create_stream_handler,
)

# Exceptions
from lms.langchain.exceptions import (
	ConfigurationError,
	LangchainError,
	PersistenceError,
	ServiceUnavailableError,
	StreamingError,
)

# Adapters
from lms.langchain.adapters import SocketIOStreamAdapter

__all__ = [
	# Config
	"get_langchain_service_url",
	"get_ai_tutor_url",
	"use_redis_mode",
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
	# Repositories
	"save_langchain_response",
	"response_exists",
	"get_response_by_request_id",
	# Event response subscriber
	"EventResponseSubscriber",
	"get_subscriber",
	"start_event_response_subscriber",
	"stop_event_response_subscriber",
	"ensure_subscriber_running",
	# Tutor stream subscriber
	"TutorStreamSubscriber",
	"create_tutor_stream_subscriber",
	# Backward compatibility
	"StreamingResponseHandler",
	"create_stream_handler",
	# Exceptions
	"LangchainError",
	"ServiceUnavailableError",
	"StreamingError",
	"PersistenceError",
	"ConfigurationError",
	# Adapters
	"SocketIOStreamAdapter",
]
