"""Redis subscriber for receiving streaming responses from LangChain service."""

import json
import threading
from typing import Any, Callable, Dict, Optional

import frappe

from .redis_client import get_redis_client


class StreamingResponseHandler:
	"""Subscribes to Redis channels for streaming AI tutor responses.

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
		on_chunk: Optional[Callable[[str, int], None]] = None,
		on_complete: Optional[Callable[[str, int], None]] = None,
		on_error: Optional[Callable[[str, str], None]] = None,
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

		self._channel = f"lms:stream:{user_id}:{request_id}"
		self._pubsub = None
		self._thread: Optional[threading.Thread] = None
		self._running = False

		# Accumulated response
		self._chunks: list = []
		self._complete_response: Optional[str] = None

	def start(self, timeout: float = 60.0) -> None:
		"""Start listening for streaming responses.

		Args:
			timeout: Maximum time to wait for stream completion (seconds)
		"""
		client = get_redis_client()
		self._pubsub = client.pubsub()
		self._pubsub.subscribe(self._channel)
		self._running = True

		frappe.logger("langchain").info(
			f"Starting stream listener: channel={self._channel}"
		)

		# Start listener thread
		self._thread = threading.Thread(
			target=self._listen_loop,
			kwargs={"timeout": timeout},
			daemon=True,
		)
		self._thread.start()

	def stop(self) -> None:
		"""Stop listening and clean up."""
		self._running = False

		if self._pubsub:
			try:
				self._pubsub.unsubscribe(self._channel)
				self._pubsub.close()
			except Exception:
				pass
			self._pubsub = None

		if self._thread and self._thread.is_alive():
			self._thread.join(timeout=1.0)
			self._thread = None

	def wait_for_completion(self, timeout: float = 60.0) -> Optional[str]:
		"""Wait for the stream to complete and return the full response.

		Args:
			timeout: Maximum time to wait (seconds)

		Returns:
			Complete response text or None if timed out/error
		"""
		if self._thread:
			self._thread.join(timeout=timeout)

		return self._complete_response

	def _listen_loop(self, timeout: float) -> None:
		"""Main listening loop (runs in background thread)."""
		import time

		start_time = time.time()

		try:
			while self._running and (time.time() - start_time) < timeout:
				message = self._pubsub.get_message(timeout=1.0)
				if message is None:
					continue

				if message["type"] != "message":
					continue

				try:
					data = json.loads(message["data"])
					self._handle_message(data)

					# Stop on completion or error
					if data.get("type") in ("stream_end", "error"):
						break

				except json.JSONDecodeError as e:
					frappe.logger("langchain").error(
						f"Failed to parse stream message: {e}"
					)

		except Exception as e:
			frappe.logger("langchain").error(
				f"Stream listener error: {e}", exc_info=True
			)
			if self.on_error:
				self.on_error("listener_error", str(e))

		finally:
			self._running = False

	def _handle_message(self, data: Dict[str, Any]) -> None:
		"""Handle an incoming stream message."""
		msg_type = data.get("type")

		if msg_type == "stream_start":
			frappe.logger("langchain").debug(
				f"Stream started: request={self.request_id}"
			)

		elif msg_type == "stream_chunk":
			chunk = data.get("chunk", "")
			index = data.get("index", len(self._chunks))
			self._chunks.append(chunk)

			if self.on_chunk:
				self.on_chunk(chunk, index)

		elif msg_type == "stream_end":
			total_chunks = data.get("total_chunks", len(self._chunks))
			self._complete_response = data.get(
				"complete_response", "".join(self._chunks)
			)

			frappe.logger("langchain").info(
				f"Stream completed: request={self.request_id} chunks={total_chunks}"
			)

			if self.on_complete:
				self.on_complete(self._complete_response, total_chunks)

		elif msg_type == "error":
			error_type = data.get("error_type", "unknown")
			error_message = data.get("message", "Unknown error")

			frappe.logger("langchain").error(
				f"Stream error: request={self.request_id} type={error_type} msg={error_message}"
			)

			if self.on_error:
				self.on_error(error_type, error_message)


def create_stream_handler(
	user_id: str,
	request_id: str,
	on_chunk: Optional[Callable[[str, int], None]] = None,
	on_complete: Optional[Callable[[str, int], None]] = None,
	on_error: Optional[Callable[[str, str], None]] = None,
) -> StreamingResponseHandler:
	"""Factory function to create a streaming response handler.

	Args:
		user_id: The learner's user ID
		request_id: The request ID to listen for
		on_chunk: Callback for each chunk
		on_complete: Callback when streaming completes
		on_error: Callback on error

	Returns:
		Configured StreamingResponseHandler instance
	"""
	return StreamingResponseHandler(
		user_id=user_id,
		request_id=request_id,
		on_chunk=on_chunk,
		on_complete=on_complete,
		on_error=on_error,
	)
