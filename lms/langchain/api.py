"""API endpoints for LangChain service integration."""

import frappe

from lms.langchain.repositories import save_langchain_response


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
	from lms.langchain.broker import broker

	# Add current user if not provided
	if "user" not in kwargs:
		kwargs["user"] = frappe.session.user

	broker.send(event_type=event_type, **kwargs)
	return {"status": "queued", "event_type": event_type}


@frappe.whitelist(allow_guest=False)
def post_langchain_response(request_id, user, content, course=None, lesson=None):
	"""
	Callback API endpoint to receive responses from the LangChain service.

	Requires API Key/Secret authentication.

	Args:
		request_id: Unique identifier for the request
		user: The user who will receive the response
		content: The AI-generated content/feedback
		course: Optional course reference
		lesson: Optional lesson reference
	"""
	try:
		# Save using repository
		doc_name = save_langchain_response(
			user_id=user,
			content=content,
			response_mode="sync",
			request_id=request_id,
			course=course,
			lesson=lesson,
		)

		frappe.publish_realtime(
			event="langchain_response_received",
			message={
				"request_id": request_id,
				"content": content,
				"course": course,
				"lesson": lesson,
			},
			user=user,
			after_commit=True,
		)

		frappe.logger("langchain").info(
			f"LangChain response received and stored: {request_id} doc={doc_name}"
		)
		return {"status": "success", "request_id": request_id}

	except Exception as e:
		frappe.log_error(
			title="LangChain Callback Error",
			message=f"Failed to process LangChain response for request {request_id}: {str(e)}",
		)
		frappe.throw(f"Failed to process response: {str(e)}")
