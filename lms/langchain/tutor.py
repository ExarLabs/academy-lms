"""AI Tutor chat endpoint for interactive tutoring."""

import frappe
import requests

from lms.langchain.config import get_ai_tutor_url


def _use_streaming() -> bool:
	"""Check if streaming mode is enabled for AI Tutor responses.

	Returns:
		True if streaming should be used, False for synchronous HTTP.
	"""
	return frappe.conf.get("langchain_use_redis", False)


@frappe.whitelist(allow_guest=False)
def ask_tutor(message, current_lesson, course_name, user_id=None):
	"""
	Proxy to LangChain AI tutor service.

	Supports two modes:
	- Streaming mode: Returns immediately with request_id, response streams via Socket.IO
	- Sync mode (default): Waits for complete response from LangChain service

	Set `langchain_use_redis: true` in site_config.json to enable streaming mode.

	Args:
		message: User's question
		current_lesson: Lesson name for context
		course_name: Course name for context
		user_id: Optional user ID (defaults to session user)

	Returns:
		dict: {"response": "<tutor_message>"} in sync mode
		dict: {"mode": "streaming", "request_id": "<uuid>"} in streaming mode
	"""
	if not user_id:
		user_id = frappe.session.user

	module_id = f"{course_name}:{current_lesson}" if course_name else current_lesson or "default"

	if _use_streaming():
		return _ask_tutor_streaming(
			user_id=user_id,
			message=message,
			module_id=module_id,
			current_lesson=current_lesson,
			course_name=course_name,
		)
	else:
		return _ask_tutor_sync(
			user_id=user_id,
			message=message,
			current_lesson=current_lesson,
			course_name=course_name,
		)


def _ask_tutor_streaming(user_id, message, module_id, current_lesson, course_name):
	"""Handle AI tutor request with streaming response.

	Publishes request to Redis and returns immediately.
	Response is streamed back via Socket.IO events:
	- ai_tutor_stream_start
	- ai_tutor_stream_chunk
	- ai_tutor_stream_end
	- ai_tutor_stream_error

	Args:
		user_id: User ID
		message: User's question
		module_id: Module context string
		current_lesson: Lesson name
		course_name: Course name

	Returns:
		dict with mode="streaming" and request_id
	"""
	from lms.langchain.streaming import (
		request_streaming_response,
		subscribe_and_forward_to_socketio,
	)

	context = {
		"current_lesson": current_lesson or "Course Overview",
		"course_name": course_name or "General Course",
	}

	# Submit the streaming request
	request_id = request_streaming_response(
		user_id=user_id,
		message=message,
		module_id=module_id,
		context=context,
	)

	# Enqueue background job to forward streaming chunks to Socket.IO
	frappe.enqueue(
		subscribe_and_forward_to_socketio,
		queue="default",
		enqueue_after_commit=True,
		user_id=user_id,
		request_id=request_id,
		timeout=60.0,
	)

	frappe.logger("langchain").info(
		f"Streaming request initiated: user={user_id} request={request_id}"
	)

	return {
		"mode": "streaming",
		"request_id": request_id,
	}


def _ask_tutor_sync(user_id, message, current_lesson, course_name):
	"""Handle AI tutor request with synchronous HTTP response.

	Original behavior - waits for complete response from LangChain service.

	Args:
		user_id: User ID
		message: User's question
		current_lesson: Lesson name
		course_name: Course name

	Returns:
		dict with response text
	"""
	payload = {
		"user_id": user_id,
		"message": message,
		"current_lesson": current_lesson or "Course Overview",
		"course_name": course_name or "General Course",
	}

	api_endpoint = get_ai_tutor_url()

	try:
		response = requests.post(
			api_endpoint,
			json=payload,
			headers={"Content-Type": "application/json"},
			timeout=30,
		)

		if response.status_code == 200:
			api_response = response.json()
			return {
				"mode": "sync",
				"response": api_response.get("response", "How can I help you with this lesson?"),
			}
		else:
			frappe.log_error(
				f"AI Tutor API Error: {response.status_code} - {response.text}",
				"AI Tutor Error",
			)
			return {
				"mode": "sync",
				"response": "I'm having trouble connecting to the AI service. Please try again later.",
			}

	except requests.exceptions.RequestException as e:
		frappe.log_error(str(e), "AI Tutor Connection Error")
		return {
			"mode": "sync",
			"response": "The AI tutor service is currently unavailable. Please try again later.",
		}
	except Exception as e:
		frappe.log_error(str(e), "AI Tutor General Error")
		return {
			"mode": "sync",
			"response": "I encountered an error. Please try again.",
		}
