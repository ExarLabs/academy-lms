"""Socket.IO adapter for streaming AI Tutor responses.

This adapter handles the translation between streaming callbacks
and Frappe's Socket.IO realtime system, enabling real-time updates
to the user's browser.
"""

from collections.abc import Callable

import frappe

from ..repositories import save_langchain_response


class SocketIOStreamAdapter:
	"""Adapts streaming callbacks to Socket.IO events.

	This adapter is responsible for:
	- Forwarding stream chunks to the browser via Socket.IO
	- Emitting stream lifecycle events (start, end, error)
	- Persisting the complete response to the database

	Socket.IO events emitted:
		- ai_tutor_stream_start: { request_id, timestamp }
		- ai_tutor_stream_chunk: { request_id, chunk, index }
		- ai_tutor_stream_end: { request_id, complete_response, total_chunks }
		- ai_tutor_stream_error: { request_id, error_type, message }

	Example:
		adapter = SocketIOStreamAdapter(user_id="user@example.com", request_id="abc-123")
		adapter.emit_stream_start()

		subscriber = create_tutor_stream_subscriber(
			user_id=user_id,
			request_id=request_id,
			on_chunk=adapter.on_chunk,
			on_complete=adapter.on_complete,
			on_error=adapter.on_error,
		)
	"""

	# Socket.IO event names
	EVENT_STREAM_START = "ai_tutor_stream_start"
	EVENT_STREAM_CHUNK = "ai_tutor_stream_chunk"
	EVENT_STREAM_END = "ai_tutor_stream_end"
	EVENT_STREAM_ERROR = "ai_tutor_stream_error"

	def __init__(
		self,
		user_id: str,
		request_id: str,
		persist_response: bool = True,
	) -> None:
		"""Initialize the Socket.IO stream adapter.

		Args:
			user_id: The user ID to send events to
			request_id: The request ID for this stream
			persist_response: Whether to save the response to database on completion
		"""
		self.user_id = user_id
		self.request_id = request_id
		self.persist_response = persist_response

	def emit_stream_start(self) -> None:
		"""Emit the stream start event to the browser.

		Should be called before starting the stream subscriber.
		"""
		frappe.publish_realtime(
			self.EVENT_STREAM_START,
			{
				"request_id": self.request_id,
				"timestamp": frappe.utils.now(),
			},
			user=self.user_id,
		)

	def on_chunk(self, chunk: str, index: int) -> None:
		"""Forward a stream chunk to the browser via Socket.IO.

		This method is designed to be passed as the on_chunk callback
		to TutorStreamSubscriber.

		Args:
			chunk: The text chunk received
			index: The chunk index (0-based)
		"""
		frappe.publish_realtime(
			self.EVENT_STREAM_CHUNK,
			{
				"request_id": self.request_id,
				"chunk": chunk,
				"index": index,
			},
			user=self.user_id,
		)

	def on_complete(self, response: str, total_chunks: int) -> None:
		"""Forward stream completion to the browser and persist response.

		This method is designed to be passed as the on_complete callback
		to TutorStreamSubscriber.

		Args:
			response: The complete response text
			total_chunks: Total number of chunks received
		"""
		frappe.publish_realtime(
			self.EVENT_STREAM_END,
			{
				"request_id": self.request_id,
				"complete_response": response,
				"total_chunks": total_chunks,
			},
			user=self.user_id,
		)

		# Persist to database if enabled
		if self.persist_response:
			save_langchain_response(
				user_id=self.user_id,
				content=response,
				response_mode="streaming",
				request_id=self.request_id,
			)

	def on_error(self, error_type: str, message: str) -> None:
		"""Forward stream error to the browser via Socket.IO.

		This method is designed to be passed as the on_error callback
		to TutorStreamSubscriber.

		Args:
			error_type: Type of error that occurred
			message: Error message details
		"""
		frappe.publish_realtime(
			self.EVENT_STREAM_ERROR,
			{
				"request_id": self.request_id,
				"error_type": error_type,
				"message": message,
			},
			user=self.user_id,
		)

	def get_callbacks(self) -> dict:
		"""Get a dict of callbacks suitable for TutorStreamSubscriber.

		Returns:
			Dict with on_chunk, on_complete, on_error callbacks
		"""
		return {
			"on_chunk": self.on_chunk,
			"on_complete": self.on_complete,
			"on_error": self.on_error,
		}
