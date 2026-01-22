"""Shared Redis client singleton for LangChain integration.

Uses Frappe's Redis instance for pub/sub communication with LangChain service.
Both services MUST connect to the same Redis for pub/sub to work.
"""

import json
from typing import Any, Dict, Optional

import frappe
import redis


_redis_client: Optional[redis.Redis] = None


def get_redis_url() -> str:
	"""Get Redis URL from Frappe's configuration.

	Uses Frappe's redis_queue by default, which is the same Redis instance
	that LangChain connects to via host.docker.internal.

	Configuration priority:
	1. redis_pubsub_url - Optional dedicated pub/sub URL override
	2. redis_queue - Frappe's queue Redis (default, recommended)

	Returns:
		Redis connection URL string
	"""
	# Allow explicit override if needed
	url = frappe.conf.get("redis_pubsub_url")
	if url:
		return url

	# Use Frappe's queue Redis (default behavior)
	url = frappe.conf.get("redis_queue")
	if url:
		return url

	# Fallback for edge cases (should not happen in properly configured Frappe)
	return "redis://localhost:11000"


def get_redis_client() -> redis.Redis:
	"""Get or create Redis client singleton.

	Returns:
		redis.Redis: Configured Redis client instance
	"""
	global _redis_client

	if _redis_client is None:
		url = get_redis_url()
		_redis_client = redis.from_url(
			url,
			encoding="utf-8",
			decode_responses=True,
		)

	return _redis_client


def publish_message(channel: str, message: Dict[str, Any]) -> int:
	"""Publish a message to a Redis channel.

	Args:
		channel: Target channel name
		message: Message payload as dictionary

	Returns:
		Number of subscribers that received the message
	"""
	client = get_redis_client()
	payload = json.dumps(message, default=str)
	return client.publish(channel, payload)


def close_redis_client() -> None:
	"""Close the Redis client connection."""
	global _redis_client

	if _redis_client is not None:
		_redis_client.close()
		_redis_client = None
