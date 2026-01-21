"""API endpoints for LangChain service integration."""

import frappe


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
		doc = frappe.get_doc(
			{
				"doctype": "Langchain Responses",
				"user": user,
				"course": course,
				"lesson": lesson,
				"content": content,
				"request_id": request_id,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

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

		frappe.logger().info(f"LangChain response received and stored: {request_id}")
		return {"status": "success", "request_id": request_id}

	except Exception as e:
		frappe.log_error(
			title="LangChain Callback Error",
			message=f"Failed to process LangChain response for request {request_id}: {str(e)}",
		)
		frappe.throw(f"Failed to process response: {str(e)}")
