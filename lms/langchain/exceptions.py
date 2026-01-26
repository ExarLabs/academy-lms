"""Custom exceptions for LangChain integration.

Provides a hierarchy of exceptions for consistent error handling
across the LangChain module.
"""


class LangchainError(Exception):
	"""Base exception for all LangChain integration errors.

	All custom exceptions in this module should inherit from this class
	to enable catching all LangChain-related errors with a single handler.
	"""

	pass


class ServiceUnavailableError(LangchainError):
	"""Raised when the LangChain service is unavailable.

	This can occur when:
	- The service is down or unreachable
	- Connection timeout occurs
	- DNS resolution fails
	"""

	pass


class StreamingError(LangchainError):
	"""Raised when an error occurs during streaming response.

	This can occur when:
	- Redis connection fails during streaming
	- Stream timeout is reached
	- Invalid message format received
	- Callback execution fails
	"""

	pass


class PersistenceError(LangchainError):
	"""Raised when database persistence fails.

	This can occur when:
	- Database connection fails
	- Doctype doesn't exist
	- Validation errors on document creation
	"""

	pass


class ConfigurationError(LangchainError):
	"""Raised when configuration is invalid or missing.

	This can occur when:
	- Required config keys are missing
	- Invalid URL format in configuration
	- Incompatible configuration values
	"""

	pass
