"""API endpoints for LMS event integration with LangChain."""

import frappe


@frappe.whitelist(allow_guest=False)
def send_frontend_event(event_type, **kwargs):
	"""
	API endpoint to send events to LangChain service from frontend.

	Args:
		event_type: Type of event (e.g., "custom_question", "user_action")
		**kwargs: Event-specific data (course, lesson, message, etc.)

	Returns:
		dict: {"status": "queued", "event_type": event_type}
	"""
	from lms.langchain.lms_events.broker import broker

	# Add current user if not provided
	if "user" not in kwargs:
		kwargs["user"] = frappe.session.user

	broker.send(event_type=event_type, **kwargs)
	return {"status": "queued", "event_type": event_type}
