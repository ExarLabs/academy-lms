"""HTTP client for sending data to the LangChain service."""

import uuid

import frappe
import requests

from lms.langchain.api import post_langchain_response
from lms.langchain.config import get_langchain_service_url
from lms.langchain.messages import build_event_message


def send_to_langchain_service(**kwargs):
	"""Background job to send data to the LangChain service."""
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
		response = requests.post(
			get_langchain_service_url(),
			json=payload,
			timeout=30,
		)
		response.raise_for_status()
		frappe.logger().info(f"LangChain request sent successfully: {request_id}")

		response_data = response.json()
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
			message=f"Failed to send request {request_id} to LangChain service: {str(e)}\nPayload: {payload}",
		)
