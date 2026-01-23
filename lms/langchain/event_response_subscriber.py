"""Event Response Subscriber - Listens to LangChain event responses via Redis.

Subscribes to lms:events_responses:* channels and forwards AI-generated feedback
to the frontend via Frappe's Socket.IO (publish_realtime).
"""

import json
import threading
import time
from typing import Any, Callable, Dict, Optional

import frappe

from .redis_client import get_redis_client, get_redis_url


class EventResponseSubscriber:
	"""Subscribe to lms:events_responses:* and forward ALL responses to Socket.IO.

	This subscriber runs in a background thread and listens for AI-generated
	feedback from the LangChain service. Any response with user_id and content
	is forwarded to that specific user via Socket.IO.

	The frontend (Lesson.vue) already has a listener for 'langchain_response_received'
	that displays the feedback as a toast notification.
	"""

	CHANNEL_PATTERN = "lms:events_responses:*"
	RECONNECT_DELAY = 5  # seconds

	def __init__(self) -> None:
		"""Initialize the subscriber."""
		self._thread: Optional[threading.Thread] = None
		self._running = False
		self._pubsub = None

	@property
	def is_running(self) -> bool:
		"""Check if the subscriber is currently running."""
		return self._running and self._thread is not None and self._thread.is_alive()

	def start(self) -> None:
		"""Start the subscriber in a background daemon thread."""
		if self.is_running:
			frappe.logger("langchain").warning(
				"Event response subscriber already running"
			)
			return

		self._running = True
		self._thread = threading.Thread(
			target=self._listen_loop,
			daemon=True,
			name="EventResponseSubscriber",
		)
		self._thread.start()
		frappe.logger("langchain").info(
			"Event response subscriber started, listening on %s",
			self.CHANNEL_PATTERN,
		)

	def stop(self) -> None:
		"""Stop the subscriber gracefully."""
		self._running = False
		if self._pubsub:
			try:
				self._pubsub.punsubscribe(self.CHANNEL_PATTERN)
				self._pubsub.close()
			except Exception as e:
				frappe.logger("langchain").debug(f"Error closing pubsub: {e}")
			self._pubsub = None
		frappe.logger("langchain").info("Event response subscriber stopped")

	def _listen_loop(self) -> None:
		"""Main listening loop - runs in background thread."""
		while self._running:
			try:
				self._subscribe_and_listen()
			except Exception as e:
				frappe.logger("langchain").error(
					f"Subscriber error, reconnecting in {self.RECONNECT_DELAY}s: {e}"
				)
				if self._running:
					time.sleep(self.RECONNECT_DELAY)

	def _subscribe_and_listen(self) -> None:
		"""Subscribe to Redis and process messages."""
		client = get_redis_client()
		self._pubsub = client.pubsub()
		self._pubsub.psubscribe(self.CHANNEL_PATTERN)

		frappe.logger("langchain").debug(
			f"Subscribed to pattern: {self.CHANNEL_PATTERN}"
		)

		for message in self._pubsub.listen():
			if not self._running:
				break

			if message["type"] == "pmessage":
				try:
					channel = message["channel"]
					data = json.loads(message["data"])
					self._handle_response(channel, data)
				except json.JSONDecodeError as e:
					frappe.logger("langchain").warning(
						f"Invalid JSON in message: {e}"
					)
				except Exception as e:
					frappe.logger("langchain").error(
						f"Error handling response: {e}",
						exc_info=True,
					)

	def _handle_response(self, channel: str, data: Dict[str, Any]) -> None:
		"""Handle a response from LangChain and forward to Socket.IO.

		Args:
			channel: Redis channel the message came from
			data: Parsed JSON message data
		"""
		user_id = data.get("user_id")
		content = data.get("content")

		if not user_id or not content:
			frappe.logger("langchain").debug(
				f"Skipping response without user_id or content: {data}"
			)
			return

		event_type = data.get("event_type", "unknown")

		frappe.logger("langchain").info(
			f"Forwarding {event_type} response to user {user_id}"
		)

		# Save to Langchain Responses doctype for audit (optional)
		self._save_response(data)

		# Forward to frontend via Socket.IO - ONLY to the specific user
		frappe.publish_realtime(
			event="langchain_response_received",
			message={
				"content": content,
				"event_type": event_type,
				"course": data.get("course"),
				"lesson": data.get("lesson"),
			},
			user=user_id,
			after_commit=True,
		)

	def _save_response(self, data: Dict[str, Any]) -> None:
		"""Save the response to Langchain Responses doctype for audit.

		This is optional and fails silently if the doctype doesn't exist.
		"""
		try:
			if frappe.db.exists("DocType", "Langchain Responses"):
				doc = frappe.new_doc("Langchain Responses")
				doc.user = data.get("user_id")
				doc.event_type = data.get("event_type")
				doc.content = data.get("content")
				doc.course = data.get("course")
				doc.lesson = data.get("lesson")
				doc.timestamp = data.get("timestamp")
				doc.insert(ignore_permissions=True)
				frappe.db.commit()
		except Exception as e:
			# Non-critical - log and continue
			frappe.logger("langchain").debug(
				f"Could not save response to doctype: {e}"
			)


# Singleton instance
_subscriber: Optional[EventResponseSubscriber] = None
_subscriber_lock = threading.Lock()


def get_subscriber() -> EventResponseSubscriber:
	"""Get or create the event response subscriber singleton.

	Returns:
		EventResponseSubscriber instance
	"""
	global _subscriber

	if _subscriber is None:
		with _subscriber_lock:
			if _subscriber is None:
				_subscriber = EventResponseSubscriber()

	return _subscriber


def start_event_response_subscriber() -> None:
	"""Start the event response subscriber.

	Call this to start listening for LangChain event responses.
	Safe to call multiple times - will not start duplicate subscribers.
	"""
	if not _use_redis():
		frappe.logger("langchain").debug(
			"Redis mode disabled, not starting event response subscriber"
		)
		return

	subscriber = get_subscriber()
	if not subscriber.is_running:
		subscriber.start()


def stop_event_response_subscriber() -> None:
	"""Stop the event response subscriber."""
	subscriber = get_subscriber()
	subscriber.stop()


def ensure_subscriber_running() -> None:
	"""Ensure the event response subscriber is running.

	This function is designed to be called by Frappe's scheduler
	to periodically check and restart the subscriber if it crashed.
	"""
	if not _use_redis():
		return

	subscriber = get_subscriber()
	if not subscriber.is_running:
		frappe.logger("langchain").info(
			"Event response subscriber not running, starting..."
		)
		subscriber.start()


def _use_redis() -> bool:
	"""Check if Redis mode is enabled for LangChain communication."""
	return frappe.conf.get("langchain_use_redis", False)
