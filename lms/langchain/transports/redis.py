"""Redis transport for LangChain event delivery.

Publishes events directly to Redis pub/sub channels for consumption
by the LangChain service. Faster than HTTP and doesn't require
direct network connectivity between services.
"""

from typing import Any

import frappe

from lms.langchain.transports.base import EventTransport


class RedisEventTransport(EventTransport):
	"""Transport that publishes events to Redis pub/sub channels.

	Events are published synchronously to Redis, which is faster
	than HTTP for inter-service communication when both services
	share a Redis instance.

	Configuration:
		- langchain_use_redis: Must be True in site config
		- Redis connection uses Frappe's redis configuration
	"""

	def __init__(self, fallback_transport: EventTransport = None):
		"""Initialize Redis transport.

		Args:
			fallback_transport: Optional transport to use if Redis fails.
				If provided, events will be sent via fallback on Redis errors.
		"""
		self._fallback = fallback_transport

	@property
	def name(self) -> str:
		return "Redis"

	def send(self, event_type: str, **kwargs: Any) -> bool:
		"""Publish event to Redis pub/sub channel.

		Args:
			event_type: Type of event to publish.
			**kwargs: Event payload data.

		Returns:
			True if published successfully (or fallback succeeded).
		"""
		from lms.langchain.redis_publisher import get_publisher

		try:
			publisher = get_publisher()
			publisher.publish_event(event_type, **kwargs)
			frappe.logger("langchain").debug(
				f"Published event via Redis: {event_type}"
			)
			return True
		except Exception as e:
			frappe.logger("langchain").error(
				f"Failed to publish event via Redis: {e}"
			)
			if self._fallback:
				frappe.logger("langchain").info(
					f"Falling back to {self._fallback.name} transport"
				)
				return self._fallback.send(event_type, **kwargs)
			return False

	def is_available(self) -> bool:
		"""Check if Redis transport is available.

		Verifies that Redis mode is enabled and Redis is reachable.

		Returns:
			True if Redis is configured and accessible.
		"""
		from lms.langchain.config import use_redis_mode

		if not use_redis_mode():
			return False

		try:
			from lms.langchain.redis_client import get_redis_client

			client = get_redis_client()
			return client.ping() if client else False
		except Exception:
			return False

	def get_diagnostics(self) -> dict[str, Any]:
		"""Get Redis transport diagnostics."""
		from lms.langchain.config import use_redis_mode

		diagnostics = {
			"transport": self.name,
			"available": self.is_available(),
			"redis_mode_enabled": use_redis_mode(),
			"has_fallback": self._fallback is not None,
		}

		if self._fallback:
			diagnostics["fallback_transport"] = self._fallback.name

		return diagnostics
