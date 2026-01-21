"""Message broker for sending LMS events to LangChain service."""

import frappe

from lms.langchain.service import send_to_langchain_service


class LangchainMessageBroker:
	"""Broker for sending LMS events to LangChain service."""

	def __init__(self, queue="default", enqueue_after_commit=True):
		self.queue = queue
		self.enqueue_after_commit = enqueue_after_commit

	def send(self, event_type, **kwargs):
		"""Enqueue event to be sent to LangChain service."""
		frappe.enqueue(
			send_to_langchain_service,
			queue=self.queue,
			enqueue_after_commit=self.enqueue_after_commit,
			event_type=event_type,
			**kwargs,
		)


# Default broker instance
broker = LangchainMessageBroker()
