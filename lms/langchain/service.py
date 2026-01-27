"""HTTP client for sending data to the LangChain service."""

import uuid

import frappe
import requests

from lms.langchain.api import post_langchain_response
from lms.langchain.config import get_langchain_service_url
from lms.langchain.messages import build_event_message
from lms.langchain.utils.resilience import retry_on_exception


# Retry configuration for HTTP requests
HTTP_RETRY_ATTEMPTS = 3
HTTP_RETRY_DELAY = 2.0
HTTP_RETRY_BACKOFF = 2.0


def _log_retry(exception: Exception, attempt: int) -> None:
	"""Log retry attempts for monitoring."""
	frappe.logger("langchain").warning(
		f"HTTP request retry attempt {attempt}: {exception}"
	)


@retry_on_exception(
	max_attempts=HTTP_RETRY_ATTEMPTS,
	delay=HTTP_RETRY_DELAY,
	backoff=HTTP_RETRY_BACKOFF,
	exceptions=(
		requests.exceptions.ConnectionError,
		requests.exceptions.Timeout,
		requests.exceptions.HTTPError,
	),
	on_retry=_log_retry,
)
def _send_http_request(url: str, payload: dict, timeout: int = 30) -> dict:
	"""Send HTTP request with retry logic.

	Args:
		url: Target URL for the POST request.
		payload: JSON payload to send.
		timeout: Request timeout in seconds.

	Returns:
		Response JSON data.

	Raises:
		requests.exceptions.RequestException: If all retries fail.
	"""
	response = requests.post(url, json=payload, timeout=timeout)
	response.raise_for_status()
	return response.json()


def send_to_langchain_service(**kwargs):
	"""Background job to send data to the LangChain service.

	Builds an event message from kwargs and sends it to the configured
	LangChain service URL. On success, saves the response and notifies
	the user via real-time events.

	This function includes automatic retry with exponential backoff
	for transient network failures.

	Args:
		**kwargs: Event data including:
			- event_type: Type of event (required)
			- user: User ID to notify (required)
			- course: Course name (optional)
			- lesson: Lesson name (optional)
			- Additional event-specific fields
	"""
	request_id = str(uuid.uuid4())
	event_type = kwargs.get("event_type", "unknown")
	user = kwargs.get("user")
	course = kwargs.get("course")
	lesson = kwargs.get("lesson")

	message = build_event_message(event_type, kwargs)

	context = {
		"request_id": request_id,
		"event_type": event_type,
		"course": course,
		**{k: v for k, v in kwargs.items() if k not in ("user", "event_type", "course", "lesson")},
	}

	payload = {
		"user_id": user,
		"message": message,
		"current_lesson": lesson,
		"context": context,
	}

	try:
		response_data = _send_http_request(
			get_langchain_service_url(),
			payload,
		)
		frappe.logger("langchain").info(
			f"LangChain request sent successfully: {request_id}"
		)

		content = response_data.get("response", "")

		post_langchain_response(
			request_id=request_id,
			user=user,
			content=content,
			course=course,
			lesson=lesson,
		)

	except requests.exceptions.RequestException as e:
		frappe.log_error(
			title="LangChain Integration Error",
			message=f"Failed to send request {request_id} to LangChain service after "
			f"{HTTP_RETRY_ATTEMPTS} attempts: {str(e)}\nPayload: {payload}",
		)
