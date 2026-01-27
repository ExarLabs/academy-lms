"""LangChain integration module for Frappe LMS.

This module provides:
- Event-driven integration with external LangChain service
- AI Tutor chat functionality with streaming support
- Document event handlers for LMS events
- Repository pattern for data persistence
- Pluggable transport layer (HTTP, Redis) via Strategy pattern
- Resilience utilities for fault tolerance
"""

# Config
# Adapters
from lms.langchain.tutor_chat.adapters.socketio import SocketIOStreamAdapter

# Message broker
from lms.langchain.lms_events.broker import LangchainMessageBroker, broker
from lms.langchain.lms_events.api import send_frontend_event
from lms.langchain.lms_events.events import EventType
from lms.langchain.config import (
	get_ai_tutor_url,
	get_langchain_service_url,
	use_redis_mode,
)

# Event response subscriber (for document events)
from lms.langchain.lms_events.subscriber import (
	EventResponseSubscriber,
	ensure_subscriber_running,
	get_subscriber,
	start_event_response_subscriber,
	stop_event_response_subscriber,
)

# Event handlers
from lms.langchain.lms_events.handlers import (
	handle_assignment_status_update,
	handle_assignment_submission,
	handle_certificate_issued,
	handle_course_progress_update,
	handle_enrollment,
	handle_quiz_submission,
)

# Message utilities
from lms.langchain.communication.http.messages import build_event_message

# Repositories
from lms.langchain.repositories import (
	get_response_by_request_id,
	response_exists,
	save_langchain_response,
)

# Service functions
from lms.langchain.communication.http.client import send_to_langchain_service

# Transports (Strategy pattern)
from lms.langchain.lms_events.transports import (
	EventTransport,
	HttpEventTransport,
	RedisEventTransport,
)
from lms.langchain.tutor_chat.api import ask_tutor, post_langchain_response

# Tutor stream subscriber (for AI Tutor streaming responses)
from lms.langchain.tutor_chat.stream_subscriber import (
	# Backward compatibility aliases
	StreamingResponseHandler,
	TutorStreamSubscriber,
	create_stream_handler,
	create_tutor_stream_subscriber,
)

# Utilities
from lms.langchain.utils import retry_on_exception

__all__ = [
	# Config
	"get_langchain_service_url",
	"get_ai_tutor_url",
	"use_redis_mode",
	# Broker
	"LangchainMessageBroker",
	"broker",
	"EventType",
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
	# Adapters
	"SocketIOStreamAdapter",
	# Transports
	"EventTransport",
	"HttpEventTransport",
	"RedisEventTransport",
	# Utilities
	"retry_on_exception",
]
