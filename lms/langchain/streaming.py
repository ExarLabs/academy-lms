"""Streaming support for AI Tutor responses via Redis Streams.

This module provides orchestration for streaming AI Tutor responses:
- Publishing tutor requests to Redis
- Subscribing to response streams
- Forwarding chunks to the browser via Socket.IO

The actual Socket.IO communication is handled by the SocketIOStreamAdapter,
keeping this module focused on orchestration logic.
"""

from typing import Any

import frappe

from .adapters.socketio import SocketIOStreamAdapter
from .redis_publisher import get_publisher
from .tutor_stream_subscriber import create_tutor_stream_subscriber


def request_streaming_response(
	user_id: str,
	message: str,
	module_id: str,
	context: dict[str, Any] | None = None,
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
) -> str | None:
	"""Subscribe to streaming response and forward chunks to Socket.IO.

	This function is designed to be run as a background job via frappe.enqueue().
	It subscribes to the Redis Stream (using XREAD) and forwards each chunk to the
	user's browser via Frappe's Socket.IO realtime system.

	Uses Redis Streams instead of Pub/Sub to solve the race condition where
	subscribers connecting after publishing starts would miss early messages.

	Socket.IO events emitted (via SocketIOStreamAdapter):
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
		f"[STREAMING] Starting: user={user_id} request={request_id} timeout={timeout}"
	)

	# Create adapter for Socket.IO communication
	adapter = SocketIOStreamAdapter(
		user_id=user_id,
		request_id=request_id,
		persist_response=True,
	)

	# Emit stream start event
	adapter.emit_stream_start()

	# Create and start the tutor stream subscriber with adapter callbacks
	subscriber = create_tutor_stream_subscriber(
		user_id=user_id,
		request_id=request_id,
		**adapter.get_callbacks(),
	)

	subscriber.start(timeout=timeout)
	complete_response = subscriber.wait_for_completion(timeout=timeout)
	subscriber.stop()

	# Clean up the Redis Stream after successful consumption
	if complete_response is not None:
		subscriber.cleanup_stream()
		frappe.logger("langchain").info(
			f"[STREAMING] Completed: request={request_id} "
			f"response_length={len(complete_response)}"
		)
	else:
		frappe.logger("langchain").warning(
			f"[STREAMING] No response received: request={request_id}"
		)

	return complete_response
