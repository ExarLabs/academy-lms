"""Shared Data Service client module for Frappe LMS.

This module provides HTTP client functions for communicating with the
academy-shared-data-service (MongoDB-backed) for cross-service data
like user profiles.

Configuration (site_config.json):
	{
		"shared_data_service_url": "http://shared-data-service:8001",
		"shared_data_api_key": "your-api-key"
	}

Example usage:
	from lms.shared_data import get_user_profile, create_user_profile

	# Get a user profile
	profile = get_user_profile("user@example.com")
	if profile:
		print(profile["full_name"])

	# Create a new profile
	new_profile = create_user_profile(
		frappe_user_id="user@example.com",
		email="user@example.com",
		full_name="John Doe",
		metadata={"preferences": {"theme": "dark"}}
	)
"""

from lms.shared_data.client import (
	create_user_profile,
	delete_user_profile,
	get_user_profile,
	update_user_profile,
)

__all__ = [
	"get_user_profile",
	"create_user_profile",
	"update_user_profile",
	"delete_user_profile",
]
