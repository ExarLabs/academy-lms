"""HTTP client for the Shared Data Service.

Provides CRUD operations for user profiles stored in the shared data service
(MongoDB-backed). All functions include automatic retry with exponential backoff
for transient network failures.

Configuration (site_config.json):
	{
		"shared_data_service_url": "http://shared-data-service:8001",
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
def _make_request(
	method: str,
	path: str,
	params: dict | None = None,
	json_data: dict | None = None,
) -> dict | None:
	"""Generic request helper for the shared data service.

	Args:
		method: HTTP method (GET, POST, PATCH, DELETE).
		path: API path (e.g., "/api/v1/stats/overview").
		params: Query parameters (optional).
		json_data: JSON body payload (optional).

	Returns:
		Response JSON dict, or None if not found (404).

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	url = f"{get_shared_data_service_url()}{path}"
	response = requests.request(
		method,
		url,
		headers=_get_headers(),
		params=params,
		json=json_data,
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
def get_user_profile(frappe_user_id: str) -> dict | None:
	"""Get a user profile by Frappe user ID.

	Args:
		frappe_user_id: The Frappe user ID (typically email).

	Returns:
		Profile data dict if found, None if not found (404).

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	return _make_request("GET", f"/api/v1/profiles/{frappe_user_id}")


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
	payload = {"frappe_user_id": frappe_user_id}
	if email is not None:
		payload["email"] = email
	if full_name is not None:
		payload["full_name"] = full_name
	if metadata is not None:
		payload["metadata"] = metadata

	return _make_request("POST", f"/api/v1/profiles", None, payload)


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
	payload = {}
	if email is not None:
		payload["email"] = email
	if full_name is not None:
		payload["full_name"] = full_name
	if metadata is not None:
		payload["metadata"] = metadata

	return _make_request("PATCH", f"/api/v1/profiles/{frappe_user_id}", None, payload)


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
	_make_request("DELETE", f"/api/v1/profiles/{frappe_user_id}")
	return True



# Statistics API functions


def get_stats_overview() -> dict | None:
	"""Get aggregated statistics from shared-data-service.

	Returns:
		Dict with total_learners, average_quiz_score, total_quizzes_taken,
		total_certificates_issued, or None if service unavailable.

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	return _make_request("GET", "/api/v1/stats/overview")


def get_learners_stats(
	skip: int = 0,
	limit: int = 50,
	search: str = "",
	sort_by: str = "last_activity",
) -> dict | None:
	"""Get paginated learner list with basic metrics.

	Args:
		skip: Number of records to skip (pagination offset).
		limit: Maximum number of records to return (1-100).
		search: Search string for name/email (case-insensitive).
		sort_by: Sort field (last_activity, full_name, email).

	Returns:
		Dict with learners list, total count, skip, and limit,
		or None if service unavailable.

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	params = {
		"skip": skip,
		"limit": limit,
		"search": search,
		"sort_by": sort_by,
	}
	return _make_request("GET", "/api/v1/stats/learners", params=params)


def get_learner_detail(user_id: str) -> dict | None:
	"""Get single learner detail by user ID.

	Args:
		user_id: The Frappe user ID (typically email).

	Returns:
		Learner detail dict, or None if not found.

	Raises:
		requests.exceptions.RequestException: On network/HTTP errors after retries.
	"""
	return _make_request("GET", f"/api/v1/stats/learners/{user_id}")
