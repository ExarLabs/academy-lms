import uuid

import frappe
import requests


LANGCHAIN_SERVICE_URL = "http://langchain-service:5000/webhook"


def handle_course_progress_update(doc, method):
	"""Handler for LMS Course Progress on_update event."""
	frappe.enqueue(
		send_to_langchain_service,
		queue="default",
		enqueue_after_commit=True,
		event_type="course_progress",
		user=doc.member,
		course=doc.course,
		lesson=doc.lesson,
		chapter=doc.chapter,
		status=doc.status,
	)


def handle_quiz_submission(doc, method):
	"""Handler for LMS Quiz Submission after_insert event."""
	frappe.enqueue(
		send_to_langchain_service,
		queue="default",
		enqueue_after_commit=True,
		event_type="quiz_submission",
		user=doc.member,
		course=doc.course,
		quiz=doc.quiz,
		quiz_title=doc.quiz_title,
		score=doc.score,
		score_out_of=doc.score_out_of,
		percentage=doc.percentage,
		passing_percentage=doc.passing_percentage,
	)


def handle_assignment_submission(doc, method):
	"""Handler for LMS Assignment Submission after_insert event."""
	frappe.enqueue(
		send_to_langchain_service,
		queue="default",
		enqueue_after_commit=True,
		event_type="assignment_submission",
		user=doc.member,
		course=doc.course,
		lesson=doc.lesson,
		assignment=doc.assignment,
		assignment_title=doc.assignment_title,
		answer=doc.answer,
		question=doc.question,
		submission_type=doc.type,
	)


def handle_assignment_status_update(doc, method):
	"""Handler for LMS Assignment Submission on_update event.

	Only triggers if the status field has changed.
	"""
	if not doc.has_value_changed("status"):
		return

	frappe.enqueue(
		send_to_langchain_service,
		queue="default",
		enqueue_after_commit=True,
		event_type="assignment_status_update",
		user=doc.member,
		course=doc.course,
		lesson=doc.lesson,
		assignment=doc.assignment,
		assignment_title=doc.assignment_title,
		status=doc.status,
		comments=doc.comments,
	)


def handle_enrollment(doc, method):
	"""Handler for LMS Enrollment after_insert event."""
	frappe.enqueue(
		send_to_langchain_service,
		queue="default",
		enqueue_after_commit=True,
		event_type="enrollment",
		user=doc.member,
		course=doc.course,
		member_name=doc.member_name,
		member_type=doc.member_type,
	)


def handle_certificate_issued(doc, method):
	"""Handler for LMS Certificate after_insert event."""
	frappe.enqueue(
		send_to_langchain_service,
		queue="default",
		enqueue_after_commit=True,
		event_type="certificate_issued",
		user=doc.member,
		course=doc.course,
		course_title=doc.course_title,
		issue_date=str(doc.issue_date) if doc.issue_date else None,
		batch_name=doc.batch_name,
	)


def send_to_langchain_service(**kwargs):
	"""Background job to send data to the LangChain service."""
	request_id = str(uuid.uuid4())
	site_name = frappe.local.site
	callback_url = f"https://{site_name}/api/method/lms.lms.langchain_integrations.post_langchain_response"

	payload = {
		"request_id": request_id,
		"callback_url": callback_url,
		**kwargs,
	}

	# Mock response for testing - LangChain service not ready yet
	frappe.logger().info(f"Returning mock response for request_id: {request_id}")
	mock_content = "This is a mock AI tutor response. The LangChain service is not yet available."
	post_langchain_response(
		request_id=request_id,
		user=kwargs.get("user"),
		content=mock_content,
		course=kwargs.get("course"),
		lesson=kwargs.get("lesson"),
	)
	return

	# TODO: Uncomment when LangChain service is ready
	# try:
	# 	response = requests.post(
	# 		LANGCHAIN_SERVICE_URL,
	# 		json=payload,
	# 		timeout=30,
	# 	)
	# 	response.raise_for_status()
	# 	frappe.logger().info(f"LangChain request sent successfully: {request_id}")
	# except requests.exceptions.RequestException as e:
	# 	frappe.log_error(
	# 		title="LangChain Integration Error",
	# 		message=f"Failed to send request {request_id} to LangChain service: {str(e)}\nPayload: {payload}",
	# 	)


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
