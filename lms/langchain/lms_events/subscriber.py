"""Event Response Subscriber - Listens to LangChain event responses via Redis.

Subscribes to lms:events_responses:* channels and forwards AI-generated feedback
to the frontend via Frappe's Socket.IO (publish_realtime).
"""

import json
import threading
import time
from typing import Any

import frappe

from lms.langchain.communication.redis.client import get_redis_client
from lms.langchain.config import use_redis_mode
from lms.langchain.repositories import save_langchain_response


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
		self._thread: threading.Thread | None = None
		self._running = False
		self._pubsub = None
		self._site: str | None = None

	@property
	def is_running(self) -> bool:
		"""Check if the subscriber is currently running."""
		return self._running and self._thread is not None and self._thread.is_alive()

	def start(self) -> None:
		"""Start the subscriber in a background daemon thread."""
		if self.is_running:
			frappe.logger("langchain").debug(
				"EventResponseSubscriber already running, skipping start"
			)
			return

		# Capture site name in main thread where frappe.local is initialized
		self._site = frappe.local.site
		self._running = True
		self._thread = threading.Thread(
			target=self._listen_loop,
			daemon=True,
			name="EventResponseSubscriber",
		)
		self._thread.start()
		frappe.logger("langchain").info(
			f"EventResponseSubscriber started, listening on {self.CHANNEL_PATTERN}"
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
		# Use site name captured from main thread (frappe.local is thread-local)
		site = self._site
		if not site:
			return
		while self._running:
			try:
				frappe.init(site=site)
				frappe.connect()
				self._subscribe_and_listen()
			except Exception as e:
				frappe.logger("langchain").error(
					f"Subscriber error, reconnecting in {self.RECONNECT_DELAY}s: {e}",
					exc_info=True
				)
				if self._running:
					time.sleep(self.RECONNECT_DELAY)
			finally:
				frappe.destroy()

	def _subscribe_and_listen(self) -> None:
		"""Subscribe to Redis and process messages."""
		client = get_redis_client()
		self._pubsub = client.pubsub()
		self._pubsub.psubscribe(self.CHANNEL_PATTERN)

		frappe.logger("langchain").info(
			f"EventResponseSubscriber subscribed to pattern: {self.CHANNEL_PATTERN}"
		)

		for message in self._pubsub.listen():
			if not self._running:
				break

			if message["type"] == "pmessage":
				try:
					channel = message["channel"]
					data = json.loads(message["data"])
					frappe.logger("langchain").debug(
						f"Received message on {channel}"
					)
					self._handle_response(channel, data)
				except json.JSONDecodeError as e:
					frappe.logger("langchain").warning(
						f"Invalid JSON in message: {e}"
					)
				except Exception as e:
					frappe.logger("langchain").error(
						f"Error handling response: {e}", exc_info=True
					)

	def _handle_response(self, channel: str, data: dict[str, Any]) -> None:
		"""Handle a response from LangChain and forward to Socket.IO.

		Args:
			channel: Redis channel the message came from
			data: Parsed JSON message data
		"""
		user_id = data.get("user_id")
		content = data.get("content")

		if not user_id or not content:
			frappe.logger("langchain").debug(
				"Skipping response without user_id or content"
			)
			return

		event_type = data.get("event_type", "unknown")

		frappe.logger("langchain").debug(
			f"Forwarding {event_type} response to user {user_id}"
		)

		# Save to Langchain Responses doctype for audit (optional)
		save_langchain_response(
			user_id=user_id,
			content=content,
			response_mode="event",
			event_type=event_type,
			course=data.get("course"),
			lesson=data.get("lesson"),
			timestamp=data.get("timestamp"),
		)

		# Forward to frontend via Socket.IO - ONLY to the specific user
		# Use after_commit=False since we're in a background thread without request context
		frappe.publish_realtime(
			event="langchain_response_received",
			message={
				"content": content,
				"event_type": event_type,
				"course": data.get("course"),
				"lesson": data.get("lesson"),
			},
			user=user_id,
			after_commit=False,
		)


# Singleton instance
_subscriber: EventResponseSubscriber | None = None
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
	if not use_redis_mode():
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
	if not use_redis_mode():
		return

	subscriber = get_subscriber()
	if not subscriber.is_running:
		frappe.logger("langchain").info(
			"EventResponseSubscriber not running, starting via scheduler..."
		)
		subscriber.start()
