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


def get_shared_data_service_url():
	"""Get Shared Data Service URL from site config.

	Used for communicating with the shared data service (MongoDB-backed)
	for cross-service data like user profiles.

	Site config keys:
		shared_data_service_url: Base URL (default: http://localhost:8002)

	Returns:
		Base URL for the shared data service.
	"""
	return frappe.conf.get("shared_data_service_url", "http://localhost:8002")


def get_shared_data_api_key():
	"""Get Shared Data Service API key from site config.

	Site config keys:
		shared_data_api_key: API key for X-API-Key authentication

	Returns:
		API key string, or empty string if not configured.
	"""
	return frappe.conf.get("shared_data_api_key", "")
