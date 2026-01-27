"""Redis event publisher for LangChain integration."""

import json
import uuid
from datetime import datetime
from typing import Any, Optional

import frappe

from .redis_client import publish_message


class RedisEventPublisher:
	"""Publishes LMS events and tutor requests to Redis channels.

	Channel naming convention:
		- lms:events:{type} - LMS document events
		- lms:tutor:requests - AI tutor chat requests
	"""

	# Channel names
	EVENTS_PREFIX = "lms:events"
	TUTOR_REQUESTS_CHANNEL = "lms:tutor:requests"

	def publish_event(self, event_type: str, **kwargs) -> int:
		"""Publish an LMS event to Redis.

		Args:
			event_type: Type of event (quiz_submission, enrollment, etc.)
			**kwargs: Event payload data

		Returns:
			Number of subscribers that received the message
		"""
		channel = f"{self.EVENTS_PREFIX}:{event_type}"

		message = {
			"event_type": event_type,
			"timestamp": datetime.utcnow().isoformat(),
			"request_id": str(uuid.uuid4()),
			**kwargs,
		}

		frappe.logger("langchain").debug(
			f"Publishing event to {channel}: {json.dumps(message)[:200]}"
		)

		return publish_message(channel, message)

	def publish_tutor_request(
		self,
		user_id: str,
		message: str,
		module_id: str,
		request_id: str | None = None,
		context: dict[str, Any] | None = None,
	) -> str:
		"""Publish a tutor chat request to Redis.

		Args:
			user_id: The learner's user ID
			message: The user's question/message
			module_id: Current module/lesson context
			request_id: Optional request ID (generated if not provided)
			context: Optional additional context

		Returns:
			The request_id used for this request
		"""
		if not request_id:
			request_id = str(uuid.uuid4())

		payload = {
			"user_id": user_id,
			"message": message,
			"module_id": module_id,
			"request_id": request_id,
			"timestamp": datetime.utcnow().isoformat(),
		}

		if context:
			payload["context"] = context

		frappe.logger("langchain").info(
			f"Publishing tutor request: user={user_id} module={module_id} request={request_id}"
		)

		publish_message(self.TUTOR_REQUESTS_CHANNEL, payload)

		return request_id


# Singleton instance
_publisher: RedisEventPublisher | None = None


def get_publisher() -> RedisEventPublisher:
	"""Get or create the Redis event publisher singleton.

	Returns:
		RedisEventPublisher instance
	"""
	global _publisher

	if _publisher is None:
		_publisher = RedisEventPublisher()

	return _publisher
