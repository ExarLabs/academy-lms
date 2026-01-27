"""Message broker for sending LMS events to LangChain service.

Uses the Strategy pattern to support pluggable transport mechanisms.
Transport selection is based on configuration and availability.
"""

import frappe

from lms.langchain.config import use_redis_mode
from lms.langchain.lms_events.transports.base import EventTransport


class LangchainMessageBroker:
	"""Broker for sending LMS events to LangChain service.

	Supports pluggable transports via the Strategy pattern:
	- HTTP transport (default): Uses frappe.enqueue() to send events via HTTP POST
	- Redis transport: Publishes events directly to Redis pub/sub channels

	The broker automatically selects the appropriate transport based on
	configuration and availability. Redis transport falls back to HTTP
	on failure.

	Configuration:
		Set `langchain_use_redis: true` in site_config.json to enable Redis mode.

	Example:
		broker = LangchainMessageBroker()
		broker.send("quiz_submission", user="user@example.com", score=85)

		# Or with explicit transport:
		from lms.langchain.lms_events.transports import HttpEventTransport
		broker = LangchainMessageBroker(transport=HttpEventTransport())
	"""

	def __init__(
		self,
		transport: EventTransport | None = None,
		queue: str = "default",
		enqueue_after_commit: bool = True,
	):
		"""Initialize the message broker.

		Args:
			transport: Explicit transport to use. If None, transport is
				selected automatically based on configuration.
			queue: Frappe queue name for HTTP transport background jobs.
			enqueue_after_commit: If True, HTTP jobs enqueue after DB commit.
		"""
		self._explicit_transport = transport
		self._queue = queue
		self._enqueue_after_commit = enqueue_after_commit
		self._cached_transport: EventTransport | None = None

	def _get_transport(self) -> EventTransport:
		"""Get the appropriate transport for sending events.

		Returns:
			EventTransport instance based on configuration and availability.
		"""
		if self._explicit_transport:
			return self._explicit_transport

		# Lazy import to avoid circular dependencies
		from lms.langchain.lms_events.transports import HttpEventTransport, RedisEventTransport

		if use_redis_mode():
			# Redis transport with HTTP fallback
			http_fallback = HttpEventTransport(
				queue=self._queue,
				enqueue_after_commit=self._enqueue_after_commit,
			)
			return RedisEventTransport(fallback_transport=http_fallback)
		else:
			return HttpEventTransport(
				queue=self._queue,
				enqueue_after_commit=self._enqueue_after_commit,
			)

	@property
	def transport(self) -> EventTransport:
		"""Current transport instance.

		Uses caching for repeated access, but re-evaluates on each
		send() call to respect configuration changes.
		"""
		if self._cached_transport is None:
			self._cached_transport = self._get_transport()
		return self._cached_transport

	def send(self, event_type: str, **kwargs) -> bool:
		"""Send event to LangChain service via configured transport.

		Args:
			event_type: Type of event (e.g., "quiz_submission", "enrollment")
			**kwargs: Event payload data

		Returns:
			True if the event was sent successfully, False otherwise.
		"""
		# Get fresh transport to respect any config changes
		transport = self._get_transport()

		frappe.logger("langchain").debug(
			f"Sending event '{event_type}' via {transport.name} transport"
		)

		return transport.send(event_type, **kwargs)

	def get_diagnostics(self):
		"""Get diagnostic information about the broker and transport.

		Returns:
			Dictionary with broker and transport diagnostics.
		"""
		transport = self._get_transport()
		return {
			"broker": "LangchainMessageBroker",
			"redis_mode_configured": use_redis_mode(),
			"explicit_transport": self._explicit_transport is not None,
			"transport": transport.get_diagnostics(),
		}


# Default broker instance
broker = LangchainMessageBroker()
