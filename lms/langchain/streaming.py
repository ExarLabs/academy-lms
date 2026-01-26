"""Streaming support for AI Tutor responses via Redis Streams."""

from typing import Any, Dict, Optional

import frappe

from .redis_publisher import get_publisher
from .redis_subscriber import create_stream_handler


def request_streaming_response(
	user_id: str,
	message: str,
	module_id: str,
	context: Optional[Dict[str, Any]] = None,
) -> str:
	"""Request a streaming AI tutor response.

	Publishes a tutor request to Redis and returns immediately.
	The response will be streamed back via the lms:stream:{user_id}:{request_id} channel.

	Args:
		user_id: The learner's user ID
		message: The user's question/message
		module_id: Current module/lesson context
		context: Optional additional context

	Returns:
		The request_id to use for subscribing to the response stream
	"""
	publisher = get_publisher()
	request_id = publisher.publish_tutor_request(
		user_id=user_id,
		message=message,
		module_id=module_id,
		context=context,
	)

	frappe.logger("langchain").info(
		f"Streaming request submitted: user={user_id} module={module_id} request={request_id}"
	)

	return request_id


def subscribe_and_forward_to_socketio(
	user_id: str,
	request_id: str,
	timeout: float = 60.0,
) -> Optional[str]:
	"""Subscribe to streaming response and forward chunks to Socket.IO.

	This function is designed to be run as a background job via frappe.enqueue().
	It subscribes to the Redis Stream (using XREAD) and forwards each chunk to the
	user's browser via Frappe's Socket.IO realtime system.

	Uses Redis Streams instead of Pub/Sub to solve the race condition where
	subscribers connecting after publishing starts would miss early messages.

	Socket.IO events emitted:
		- ai_tutor_stream_start: { request_id, timestamp }
		- ai_tutor_stream_chunk: { request_id, chunk, index }
		- ai_tutor_stream_end: { request_id, complete_response, total_chunks }
		- ai_tutor_stream_error: { request_id, error_type, message }

	Args:
		user_id: The learner's user ID
		request_id: The request ID to subscribe to
		timeout: Maximum time to wait for stream completion (seconds)

	Returns:
		The complete response text or None if error/timeout
	"""
	frappe.logger("langchain").info(
		f"Starting Socket.IO forwarding: user={user_id} request={request_id}"
	)

	def on_chunk(chunk: str, index: int) -> None:
		"""Forward chunk to browser via Socket.IO."""
		frappe.publish_realtime(
			"ai_tutor_stream_chunk",
			{
				"request_id": request_id,
				"chunk": chunk,
				"index": index,
			},
			user=user_id,
		)

	def on_complete(response: str, total_chunks: int) -> None:
		"""Forward completion to browser via Socket.IO and save response."""
		frappe.publish_realtime(
			"ai_tutor_stream_end",
			{
				"request_id": request_id,
				"complete_response": response,
				"total_chunks": total_chunks,
			},
			user=user_id,
		)

		# Save the complete response to database
		_save_response(user_id, request_id, response)

	def on_error(error_type: str, message: str) -> None:
		"""Forward error to browser via Socket.IO."""
		frappe.publish_realtime(
			"ai_tutor_stream_error",
			{
				"request_id": request_id,
				"error_type": error_type,
				"message": message,
			},
			user=user_id,
		)

	# Publish stream start event
	frappe.publish_realtime(
		"ai_tutor_stream_start",
		{
			"request_id": request_id,
			"timestamp": frappe.utils.now(),
		},
		user=user_id,
	)

	# Create and start the stream handler
	handler = create_stream_handler(
		user_id=user_id,
		request_id=request_id,
		on_chunk=on_chunk,
		on_complete=on_complete,
		on_error=on_error,
	)

	handler.start(timeout=timeout)
	complete_response = handler.wait_for_completion(timeout=timeout)
	handler.stop()

	# Clean up the Redis Stream after successful consumption
	# This is optional - streams will auto-expire via TTL if not deleted
	if complete_response is not None:
		handler.cleanup_stream()

	return complete_response


def _save_response(user_id: str, request_id: str, response: str) -> None:
	"""Save the complete AI tutor response to database.

	Creates a 'Langchain Responses' document if the doctype exists.
	"""
	try:
		if not frappe.db.exists("DocType", "Langchain Responses"):
			frappe.logger("langchain").debug(
				"Langchain Responses doctype not found, skipping save"
			)
			return

		doc = frappe.get_doc({
			"doctype": "Langchain Responses",
			"user": user_id,
			"request_id": request_id,
			"response": response,
			"response_mode": "streaming",
		})
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.logger("langchain").debug(
			f"Saved streaming response: request={request_id}"
		)

	except Exception as e:
		frappe.logger("langchain").error(
			f"Failed to save streaming response: {e}", exc_info=True
		)
