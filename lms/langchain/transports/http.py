"""HTTP transport for LangChain event delivery.

Sends events to the LangChain service via HTTP POST requests,
using Frappe's background job queue for asynchronous delivery.
"""

from typing import Any, Dict

import frappe

from lms.langchain.transports.base import EventTransport


class HttpEventTransport(EventTransport):
	"""Transport that delivers events via HTTP POST to LangChain service.

	Events are enqueued as background jobs to avoid blocking the main
	request. The actual HTTP call is made by `send_to_langchain_service`.

	Configuration:
		- langchain_service_url: Base URL of the LangChain service
		  (default: http://localhost:7999)
	"""

	def __init__(self, queue: str = "default", enqueue_after_commit: bool = True):
		"""Initialize HTTP transport.

		Args:
			queue: Frappe queue name for background jobs.
			enqueue_after_commit: If True, enqueue after DB transaction commits.
		"""
		self.queue = queue
		self.enqueue_after_commit = enqueue_after_commit

	@property
	def name(self) -> str:
		return "HTTP"

	def send(self, event_type: str, **kwargs: Any) -> bool:
		"""Send event via HTTP POST to LangChain service.

		Enqueues a background job that makes the actual HTTP request.
		This ensures non-blocking operation during document saves.

		Args:
			event_type: Type of event to send.
			**kwargs: Event payload data.

		Returns:
			True if the job was enqueued successfully.
		"""
		from lms.langchain.service import send_to_langchain_service

		try:
			frappe.enqueue(
				send_to_langchain_service,
				queue=self.queue,
				enqueue_after_commit=self.enqueue_after_commit,
				event_type=event_type,
				**kwargs,
			)
			frappe.logger("langchain").debug(
				f"Enqueued HTTP event: {event_type}"
			)
			return True
		except Exception as e:
			frappe.logger("langchain").error(
				f"Failed to enqueue HTTP event {event_type}: {e}"
			)
			return False

	def is_available(self) -> bool:
		"""Check if HTTP transport is available.

		HTTP transport is always considered available as it uses
		background jobs. The actual availability of the LangChain
		service is checked during delivery.

		Returns:
			Always True (availability checked at delivery time).
		"""
		return True

	def get_diagnostics(self) -> Dict[str, Any]:
		"""Get HTTP transport diagnostics."""
		from lms.langchain.config import get_langchain_service_url

		return {
			"transport": self.name,
			"available": self.is_available(),
			"service_url": get_langchain_service_url(),
			"queue": self.queue,
			"enqueue_after_commit": self.enqueue_after_commit,
		}
