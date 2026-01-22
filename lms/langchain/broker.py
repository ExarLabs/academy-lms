"""Message broker for sending LMS events to LangChain service."""

import frappe

from lms.langchain.service import send_to_langchain_service


def _use_redis() -> bool:
	"""Check if Redis mode is enabled for LangChain communication.

	Returns:
		True if Redis pub/sub should be used, False for HTTP fallback.
	"""
	return frappe.conf.get("langchain_use_redis", False)


class LangchainMessageBroker:
	"""Broker for sending LMS events to LangChain service.

	Supports two modes:
	- HTTP mode (default): Uses frappe.enqueue() to send events via HTTP POST
	- Redis mode: Publishes events directly to Redis pub/sub channels

	Set `langchain_use_redis: true` in site_config.json to enable Redis mode.
	"""

	def __init__(self, queue="default", enqueue_after_commit=True):
		self.queue = queue
		self.enqueue_after_commit = enqueue_after_commit

	def send(self, event_type, **kwargs):
		"""Send event to LangChain service via configured mode."""
		if _use_redis():
			self._send_via_redis(event_type, **kwargs)
		else:
			self._send_via_http(event_type, **kwargs)

	def _send_via_http(self, event_type, **kwargs):
		"""Send event via HTTP (original behavior).

		Enqueues a background job that makes an HTTP POST to the LangChain service.
		"""
		frappe.enqueue(
			send_to_langchain_service,
			queue=self.queue,
			enqueue_after_commit=self.enqueue_after_commit,
			event_type=event_type,
			**kwargs,
		)

	def _send_via_redis(self, event_type, **kwargs):
		"""Send event via Redis pub/sub.

		Publishes directly to Redis channel for consumption by the LangChain service.
		This is faster and doesn't require HTTP connectivity between services.
		"""
		from lms.langchain.redis_publisher import get_publisher

		try:
			publisher = get_publisher()
			publisher.publish_event(event_type, **kwargs)
			frappe.logger("langchain").debug(
				f"Published event via Redis: {event_type}"
			)
		except Exception as e:
			frappe.logger("langchain").error(
				f"Failed to publish event via Redis: {e}. Falling back to HTTP."
			)
			# Fallback to HTTP on Redis failure
			self._send_via_http(event_type, **kwargs)


# Default broker instance
broker = LangchainMessageBroker()
