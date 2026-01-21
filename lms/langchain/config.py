"""Configuration helpers for LangChain service integration."""

import frappe


def get_langchain_service_url():
	"""Get LangChain service URL from site config, with localhost default for development."""
	base_url = frappe.conf.get("langchain_service_url", "http://localhost:7999")
	return f"{base_url}/api/v1/ai/tutor/chat"


def get_ai_tutor_url():
	"""Get AI Tutor API URL from site config, with localhost default for development."""
	base_url = frappe.conf.get("ai_tutor_api_url", "http://localhost:7999")
	return f"{base_url}/api/v1/ai-tutor/chat"
