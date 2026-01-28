"""Repository pattern for LangChain data persistence.

Provides a unified interface for saving and retrieving LangChain responses,
eliminating duplicate persistence logic across the module.
"""

from typing import Any, Optional

import frappe


def save_langchain_response(
	user_id: str,
	content: str,
	response_mode: str = "sync",
	request_id: str | None = None,
	event_type: str | None = None,
	course: str | None = None,
	lesson: str | None = None,
	timestamp: str | None = None,
) -> str | None:
	"""Save a LangChain response to the database.

	Unified persistence method for all LangChain response types:
	- Streaming AI Tutor responses
	- Event-triggered responses
	- Synchronous API responses

	Args:
		user_id: The user who receives the response
		content: The AI-generated content/response text
		response_mode: Mode of response ("sync", "streaming", "event")
		request_id: Unique request identifier (optional)
		event_type: Type of triggering event (optional)
		course: Course reference (optional)
		lesson: Lesson reference (optional)
		timestamp: Response timestamp (optional)

	Returns:
		Document name if saved successfully, None if doctype doesn't exist or on error
	"""
	try:
		if not frappe.db.exists("DocType", "Langchain Responses"):
			frappe.logger("langchain").debug(
				"Langchain Responses doctype not found, skipping save"
			)
			return None

		doc_data = {
			"doctype": "Langchain Responses",
			"user": user_id,
			"response_mode": response_mode,
		}

		# Add content - field name varies by usage
		# Some callers use 'content', others use 'response'
		if content:
			doc_data["content"] = content
			doc_data["response"] = content

		# Add optional fields if provided
		if request_id:
			doc_data["request_id"] = request_id
		if event_type:
			doc_data["event_type"] = event_type
		if course:
			doc_data["course"] = course
		if lesson:
			doc_data["lesson"] = lesson
		if timestamp:
			doc_data["timestamp"] = timestamp

		doc = frappe.get_doc(doc_data)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.logger("langchain").debug(
			f"Saved langchain response: user={user_id} mode={response_mode} "
			f"request_id={request_id}"
		)

		return doc.name

	except Exception as e:
		frappe.logger("langchain").error(
			f"Failed to save langchain response: {e}", exc_info=True
		)
		return None


def response_exists(request_id: str) -> bool:
	"""Check if a response with the given request_id already exists.

	Args:
		request_id: The request identifier to check

	Returns:
		True if response exists, False otherwise
	"""
	if not frappe.db.exists("DocType", "Langchain Responses"):
		return False

	return frappe.db.exists("Langchain Responses", {"request_id": request_id})


def get_response_by_request_id(request_id: str) -> dict[str, Any] | None:
	"""Retrieve a response by its request_id.

	Args:
		request_id: The request identifier

	Returns:
		Response document as dict, or None if not found
	"""
	if not frappe.db.exists("DocType", "Langchain Responses"):
		return None

	doc_name = frappe.db.get_value(
		"Langchain Responses",
		{"request_id": request_id},
		"name"
	)

	if doc_name:
		return frappe.get_doc("Langchain Responses", doc_name).as_dict()

	return None
