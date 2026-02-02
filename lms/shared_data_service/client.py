"""HTTP client for the Shared Data Service.

Provides CRUD operations for user profiles stored in the shared data service
(MongoDB-backed). All functions include automatic retry with exponential backoff
for transient network failures.

Configuration (site_config.json):
	{
		"shared_data_service_url": "http://shared-data-service:8000",
		"shared_data_api_key": "your-api-key"
	}
"""

import frappe
import requests

from lms.langchain.config import get_shared_data_api_key, get_shared_data_service_url
from lms.langchain.utils.resilience import retry_on_exception

# Retry configuration for HTTP requests
HTTP_RETRY_ATTEMPTS = 3
HTTP_RETRY_DELAY = 2.0
HTTP_RETRY_BACKOFF = 2.0
HTTP_TIMEOUT = 10


def _get_headers() -> dict:
	"""Build request headers with API key authentication."""
	return {"X-API-Key": get_shared_data_api_key()}


def _log_retry(exception: Exception, attempt: int) -> None:
	"""Log retry attempts for monitoring."""
	frappe.logger("shared_data").warning(
		f"Shared Data Service request retry attempt {attempt}: {exception}"
	)


@retry_on_exception(
	max_attempts=HTTP_RETRY_ATTEMPTS,
	delay=HTTP_RETRY_DELAY,
	backoff=HTTP_RETRY_BACKOFF,
	exceptions=(
		requests.exceptions.ConnectionError,
		requests.exceptions.Timeout,
	),
	on_retry=_log_retry,
)
def get_user_profile(frappe_user_id: str) -> dict | None:
	"""Get a user profile by Frappe user ID.

	Args:
		frappe_user_id: The Frappe user ID (typically email).

	Returns:
		Profile data dict if found, None if not found (404).

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	url = f"{get_shared_data_service_url()}/api/v1/profiles/{frappe_user_id}"
	response = requests.get(
		url,
		headers=_get_headers(),
		timeout=HTTP_TIMEOUT,
	)
	if response.status_code == 404:
		return None
	response.raise_for_status()
	return response.json()


@retry_on_exception(
	max_attempts=HTTP_RETRY_ATTEMPTS,
	delay=HTTP_RETRY_DELAY,
	backoff=HTTP_RETRY_BACKOFF,
	exceptions=(
		requests.exceptions.ConnectionError,
		requests.exceptions.Timeout,
	),
	on_retry=_log_retry,
)
def create_user_profile(
	frappe_user_id: str,
	email: str | None = None,
	full_name: str | None = None,
	metadata: dict | None = None,
) -> dict:
	"""Create a new user profile.

	Args:
		frappe_user_id: The Frappe user ID (required, must be unique).
		email: User email address.
		full_name: User's full name.
		metadata: Additional dynamic data to store with the profile.

	Returns:
		Created profile data dict.

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	url = f"{get_shared_data_service_url()}/api/v1/profiles"
	payload = {"frappe_user_id": frappe_user_id}
	if email is not None:
		payload["email"] = email
	if full_name is not None:
		payload["full_name"] = full_name
	if metadata is not None:
		payload["metadata"] = metadata

	response = requests.post(
		url,
		json=payload,
		headers=_get_headers(),
		timeout=HTTP_TIMEOUT,
	)
	response.raise_for_status()
	return response.json()


@retry_on_exception(
	max_attempts=HTTP_RETRY_ATTEMPTS,
	delay=HTTP_RETRY_DELAY,
	backoff=HTTP_RETRY_BACKOFF,
	exceptions=(
		requests.exceptions.ConnectionError,
		requests.exceptions.Timeout,
	),
	on_retry=_log_retry,
)
def update_user_profile(
	frappe_user_id: str,
	email: str | None = None,
	full_name: str | None = None,
	metadata: dict | None = None,
) -> dict | None:
	"""Update an existing user profile (partial update).

	Only provided fields will be updated. The metadata field is merged
	with existing metadata (not replaced).

	Args:
		frappe_user_id: The Frappe user ID of the profile to update.
		email: New email address (optional).
		full_name: New full name (optional).
		metadata: Additional metadata to merge with existing (optional).

	Returns:
		Updated profile data dict, or None if not found (404).

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	url = f"{get_shared_data_service_url()}/api/v1/profiles/{frappe_user_id}"
	payload = {}
	if email is not None:
		payload["email"] = email
	if full_name is not None:
		payload["full_name"] = full_name
	if metadata is not None:
		payload["metadata"] = metadata

	response = requests.patch(
		url,
		json=payload,
		headers=_get_headers(),
		timeout=HTTP_TIMEOUT,
	)
	if response.status_code == 404:
		return None
	response.raise_for_status()
	return response.json()


@retry_on_exception(
	max_attempts=HTTP_RETRY_ATTEMPTS,
	delay=HTTP_RETRY_DELAY,
	backoff=HTTP_RETRY_BACKOFF,
	exceptions=(
		requests.exceptions.ConnectionError,
		requests.exceptions.Timeout,
	),
	on_retry=_log_retry,
)
def delete_user_profile(frappe_user_id: str) -> bool:
	"""Delete a user profile.

	Args:
		frappe_user_id: The Frappe user ID of the profile to delete.

	Returns:
		True if deleted successfully, False if not found (404).

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	url = f"{get_shared_data_service_url()}/api/v1/profiles/{frappe_user_id}"
	response = requests.delete(
		url,
		headers=_get_headers(),
		timeout=HTTP_TIMEOUT,
	)
	if response.status_code == 404:
		return False
	response.raise_for_status()
	return True
