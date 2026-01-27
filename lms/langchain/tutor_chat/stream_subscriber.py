"""Tutor Stream Subscriber - Receives streaming AI Tutor responses via Redis Streams.

Uses Redis Streams (XREAD) instead of Pub/Sub to solve the race condition where
subscribers connecting after publishing starts would miss early messages.
Streams persist messages until consumed, allowing late subscribers to read
from the beginning.
"""

import threading
from collections.abc import Callable
from typing import Any

import frappe

from lms.langchain.communication.redis.client import get_redis_client


class TutorStreamSubscriber:
	"""Subscribes to Redis Streams for streaming AI tutor responses.

	Uses Redis Streams with XREAD to consume messages. Starts reading from
	ID "0" to ensure all messages are received, even those published before
	the subscriber started.

	Handles the following message types:
		- stream_start: Response streaming has begun
		- stream_chunk: Individual token/chunk of the response
		- stream_end: Response streaming completed
		- error: An error occurred during streaming
	"""

	def __init__(
		self,
		user_id: str,
		request_id: str,
		on_chunk: Callable[[str, int], None] | None = None,
		on_complete: Callable[[str, int], None] | None = None,
		on_error: Callable[[str, str], None] | None = None,
	):
		"""Initialize the streaming response handler.

		Args:
			user_id: The learner's user ID
			request_id: The request ID to listen for
			on_chunk: Callback for each chunk (chunk_text, chunk_index)
			on_complete: Callback when streaming completes (full_response, total_chunks)
			on_error: Callback on error (error_type, error_message)
		"""
		self.user_id = user_id
		self.request_id = request_id
		self.on_chunk = on_chunk
		self.on_complete = on_complete
		self.on_error = on_error

		self._stream_key = f"lms:stream:{user_id}:{request_id}"
		self._thread: threading.Thread | None = None
		self._running = False

		# Track last read ID for incremental reads
		self._last_id = "0"

		# Accumulated response
		self._chunks: list = []
		self._complete_response: str | None = None

	def start(self, timeout: float = 60.0) -> None:
		"""Start listening for streaming responses.

		Args:
			timeout: Maximum time to wait for stream completion (seconds)
		"""
		self._running = True

		# Capture context from main thread (frappe.local not available in spawned threads)
		# Thread needs: site_name (for frappe.init), redis_url (for Redis connection)
		from lms.langchain.communication.redis.client import get_redis_url
		redis_url = get_redis_url()
		site_name = frappe.local.site
		frappe.logger("langchain").info(
			f"Starting stream listener: key={self._stream_key}"
		)

		# Start listener thread, passing context needed for Frappe initialization
		self._thread = threading.Thread(
			target=self._listen_loop,
			kwargs={"timeout": timeout, "redis_url": redis_url, "site_name": site_name},
			daemon=True,
		)
		self._thread.start()

	def stop(self) -> None:
		"""Stop listening and clean up."""
		self._running = False

		if self._thread and self._thread.is_alive():
			self._thread.join(timeout=1.0)
			self._thread = None

	def wait_for_completion(self, timeout: float = 60.0) -> str | None:
		"""Wait for the stream to complete and return the full response.

		Args:
			timeout: Maximum time to wait (seconds)

		Returns:
			Complete response text or None if timed out/error
		"""
		if self._thread:
			self._thread.join(timeout=timeout)

		return self._complete_response

	def cleanup_stream(self) -> bool:
		"""Delete the stream after successful consumption.

		Call this after stream_end is processed to clean up Redis.

		Returns:
			True if stream was deleted, False if it didn't exist
		"""
		try:
			client = get_redis_client()
			deleted = client.delete(self._stream_key)
			if deleted:
				frappe.logger("langchain").debug(
					f"Cleaned up stream: {self._stream_key}"
				)
			return deleted > 0
		except Exception as e:
			frappe.logger("langchain").error(
				f"Failed to cleanup stream: {e}"
			)
			return False

	def _listen_loop(self, timeout: float, redis_url: str, site_name: str) -> None:
		"""Main listening loop using XREAD (runs in background thread).

		Args:
			timeout: Maximum time to wait for stream completion (seconds)
			redis_url: Redis URL (passed from main thread since frappe.conf is not bound in threads)
			site_name: Frappe site name (for initializing Frappe context in thread)
		"""
		import time

		try:
			# Initialize Frappe context for this thread
			# Required for: frappe.publish_realtime(), frappe.db, frappe.logger()
			frappe.init(site=site_name)
			frappe.connect()

			# Create a dedicated Redis connection for this thread
			import redis
			client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
			start_time = time.time()
			block_ms = 1000  # Block for 1 second per XREAD call
			poll_count = 0

			while self._running and (time.time() - start_time) < timeout:
				poll_count += 1
				# XREAD from last position, blocking for efficient polling
				# Using last_id ensures we don't re-process messages
				result = client.xread(
					{self._stream_key: self._last_id},
					count=100,  # Process up to 100 entries per call
					block=block_ms,
				)

				if not result:
					# No new messages, continue polling
					if poll_count % 10 == 0:  # Log every 10 polls (~10 seconds)
						frappe.logger("langchain").debug(
							f"Stream listener polling: key={self._stream_key} "
							f"polls={poll_count} elapsed={time.time() - start_time:.1f}s"
						)
					continue

				# Process all entries from the stream
				# Result format: [[stream_key, [(entry_id, fields), ...]]]
				for _stream_key, entries in result:
					for entry_id, fields in entries:
						self._last_id = entry_id
						should_stop = self._handle_message(fields)

						if should_stop:
							return

		except Exception as e:
			frappe.logger("langchain").error(
				f"Stream listener error: {e}", exc_info=True
			)
			if self.on_error:
				self.on_error("listener_error", str(e))

		finally:
			self._running = False
			# Close the thread-local Redis connection
			try:
				if 'client' in locals() and client:
					client.close()
			except Exception:
				pass
			# Clean up Frappe context for this thread
			try:
				frappe.destroy()
			except Exception:
				pass

	def _handle_message(self, fields: dict[str, Any]) -> bool:
		"""Handle an incoming stream message.

		Args:
			fields: Field-value dict from the stream entry

		Returns:
			True if streaming is complete and we should stop listening
		"""
		msg_type = fields.get("type")

		if msg_type == "stream_start":
			frappe.logger("langchain").debug(
				f"Stream started: request={self.request_id}"
			)
			return False

		elif msg_type == "stream_chunk":
			chunk = fields.get("chunk", "")
			# Redis Streams store all values as strings
			index = int(fields.get("index", len(self._chunks)))
			self._chunks.append(chunk)

			if self.on_chunk:
				self.on_chunk(chunk, index)

			return False

		elif msg_type == "stream_end":
			total_chunks = int(fields.get("total_chunks", len(self._chunks)))
			self._complete_response = fields.get(
				"complete_response", "".join(self._chunks)
			)

			frappe.logger("langchain").info(
				f"Stream completed: request={self.request_id} chunks={total_chunks}"
			)

			if self.on_complete:
				self.on_complete(self._complete_response, total_chunks)

			return True  # Stop listening

		elif msg_type == "error":
			error_type = fields.get("error_type", "unknown")
			error_message = fields.get("message", "Unknown error")

			frappe.logger("langchain").error(
				f"Stream error: request={self.request_id} type={error_type} msg={error_message}"
			)

			if self.on_error:
				self.on_error(error_type, error_message)

			return True  # Stop listening

		return False


def create_tutor_stream_subscriber(
	user_id: str,
	request_id: str,
	on_chunk: Callable[[str, int], None] | None = None,
	on_complete: Callable[[str, int], None] | None = None,
	on_error: Callable[[str, str], None] | None = None,
) -> TutorStreamSubscriber:
	"""Factory function to create a tutor stream subscriber.

	Args:
		user_id: The learner's user ID
		request_id: The request ID to listen for
		on_chunk: Callback for each chunk
		on_complete: Callback when streaming completes
		on_error: Callback on error

	Returns:
		Configured TutorStreamSubscriber instance
	"""
	return TutorStreamSubscriber(
		user_id=user_id,
		request_id=request_id,
		on_chunk=on_chunk,
		on_complete=on_complete,
		on_error=on_error,
	)


# Backward compatibility alias
create_stream_handler = create_tutor_stream_subscriber
StreamingResponseHandler = TutorStreamSubscriber
