"""Configuration helpers for LangChain service integration."""

import frappe


def use_redis_mode() -> bool:
	"""Check if Redis mode is enabled for LangChain communication.

	When enabled, the module uses Redis pub/sub for event communication
	and Redis Streams for AI Tutor streaming responses.

	Returns:
		True if Redis mode should be used, False for HTTP fallback.
	"""
	return frappe.conf.get("langchain_use_redis", False)


def get_langchain_service_url():
	"""Get LangChain service URL from site config, with localhost default for development."""
	base_url = frappe.conf.get("langchain_service_url", "http://localhost:7999")
	return f"{base_url}/api/v1/events/lms"


def get_ai_tutor_url():
	"""Get AI Tutor API URL from site config, with localhost default for development."""
	base_url = frappe.conf.get("ai_tutor_api_url", "http://localhost:7999")
	return f"{base_url}/api/v1/ai/tutor/chat"
