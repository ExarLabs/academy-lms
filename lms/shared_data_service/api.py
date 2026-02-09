"""Frappe API endpoints for user profile statistics.

Provides whitelisted endpoints that proxy to the shared-data-service statistics API.
Access is restricted to administrators and instructors.
"""

import frappe

from lms.shared_data_service.client import get_learner_detail, get_learners_stats, get_stats_overview


def _check_admin_access() -> None:
	"""Check if current user has admin/instructor access.

	Authorized roles:
	- Administrator (user)
	- System Manager (role)
	- Moderator (role)
	- Course Creator (role)

	Raises:
		frappe.PermissionError: If user lacks required permissions.
	"""
	user = frappe.session.user
	if user == "Administrator":
		return

	roles = frappe.get_roles(user)
	allowed_roles = ["System Manager", "Moderator", "Course Creator"]
	if not any(role in roles for role in allowed_roles):
		frappe.throw("Insufficient permissions", frappe.PermissionError)


@frappe.whitelist()
def get_profile_stats_overview() -> dict | None:
	"""Get aggregated statistics overview.

	Access: System Manager, Moderator, Course Creator, or Administrator.

	Returns:
		Dict with total_learners, average_quiz_score, total_quizzes_taken,
		total_certificates_issued.
	"""
	_check_admin_access()
	return get_stats_overview()


@frappe.whitelist()
def get_profile_learners_stats(
	skip: int | str = 0,
	limit: int | str = 50,
	sort_by: str = "last_activity",
	search: str = "",
) -> dict | None:
	"""Get paginated learner list with metrics.

	Access: System Manager, Moderator, Course Creator, or Administrator.

	Args:
		skip: Pagination offset (default 0).
		limit: Page size, max 100 (default 50).
		sort_by: Sort field - last_activity, full_name, or email.
		search: Search string for name/email filtering.

	Returns:
		Dict with learners list, total count, skip, and limit.
	"""
	_check_admin_access()
	return get_learners_stats(int(skip), int(limit), search, sort_by)


@frappe.whitelist()
def get_profile_learner_detail(user_id: str) -> dict | None:
	"""Get detailed statistics for a single learner.

	Access: System Manager, Moderator, Course Creator, or Administrator.

	Args:
		user_id: The Frappe user ID (typically email).

	Returns:
		Learner detail dict with full profile and statistics.
	"""
	_check_admin_access()
	return get_learner_detail(user_id)
