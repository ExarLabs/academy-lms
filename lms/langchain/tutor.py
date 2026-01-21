"""AI Tutor chat endpoint for interactive tutoring."""

import frappe
import requests

from lms.langchain.config import get_ai_tutor_url


@frappe.whitelist(allow_guest=False)
def ask_tutor(message, current_lesson, course_name, user_id=None):
	"""
	Proxy to LangChain AI tutor service.

	Args:
		message: User's question
		current_lesson: Lesson name for context
		course_name: Course name for context
		user_id: Optional user ID (defaults to session user)

	Returns:
		dict: {"response": "<tutor_message>"}
	"""
	if not user_id:
		user_id = frappe.session.user

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
			return {"response": api_response.get("response", "How can I help you with this lesson?")}
		else:
			frappe.log_error(
				f"AI Tutor API Error: {response.status_code} - {response.text}",
				"AI Tutor Error",
			)
			return {"response": "I'm having trouble connecting to the AI service. Please try again later."}

	except requests.exceptions.RequestException as e:
		frappe.log_error(str(e), "AI Tutor Connection Error")
		return {"response": "The AI tutor service is currently unavailable. Please try again later."}
	except Exception as e:
		frappe.log_error(str(e), "AI Tutor General Error")
		return {"response": "I encountered an error. Please try again."}
