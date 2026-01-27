"""Resilience utilities for fault-tolerant operations.

Provides decorators and helpers for handling transient failures
through retry logic with exponential backoff.
"""

import functools
import time
from collections.abc import Callable

import frappe


def retry_on_exception(
	max_attempts: int = 3,
	delay: float = 1.0,
	backoff: float = 2.0,
	exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
	on_retry: Callable[[Exception, int], None] = None,
) -> Callable:
	"""Decorator that retries a function on specified exceptions.

	Implements exponential backoff between retry attempts. Useful for
	handling transient failures in network calls, database operations,
	or other unreliable operations.

	Args:
		max_attempts: Maximum number of attempts (including the first).
			Must be >= 1. Default: 3
		delay: Initial delay in seconds between retries. Default: 1.0
		backoff: Multiplier applied to delay after each retry.
			Use 1.0 for constant delay. Default: 2.0
		exceptions: Exception type(s) to catch and retry on.
			Can be a single exception class or tuple of classes.
			Default: Exception (retries on any exception)
		on_retry: Optional callback called before each retry.
			Receives (exception, attempt_number) as arguments.
			Useful for logging or metrics.

	Returns:
		Decorated function with retry behavior.

	Example:
		@retry_on_exception(max_attempts=3, delay=2, backoff=2)
		def fetch_data():
			return requests.get(url)

		# With specific exceptions:
		@retry_on_exception(
			max_attempts=5,
			exceptions=(ConnectionError, TimeoutError),
			on_retry=lambda e, n: logger.warning(f"Retry {n}: {e}")
		)
		def connect_to_service():
			...

	Raises:
		The last exception if all retry attempts fail.
	"""
	if max_attempts < 1:
		raise ValueError("max_attempts must be >= 1")

	def decorator(func: Callable) -> Callable:
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			current_delay = delay
			last_exception = None

			for attempt in range(1, max_attempts + 1):
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					last_exception = e

					if attempt == max_attempts:
						frappe.logger("langchain").error(
							f"{func.__name__} failed after {max_attempts} attempts: {e}"
						)
						raise

					if on_retry:
						try:
							on_retry(e, attempt)
						except Exception as callback_error:
							frappe.logger("langchain").warning(
								f"on_retry callback failed: {callback_error}"
							)

					frappe.logger("langchain").warning(
						f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
						f"Retrying in {current_delay:.1f}s..."
					)

					time.sleep(current_delay)
					current_delay *= backoff

			# Should not reach here, but just in case
			if last_exception:
				raise last_exception

		return wrapper

	return decorator


class RetryContext:
	"""Context manager for retry operations with explicit control.

	Use when you need more control over retry logic than the decorator
	provides, such as conditional retries or custom error handling.

	Example:
		with RetryContext(max_attempts=3) as retry:
			while retry.should_continue():
				try:
					result = risky_operation()
					break
				except TransientError as e:
					retry.record_failure(e)
	"""

	def __init__(
		self,
		max_attempts: int = 3,
		delay: float = 1.0,
		backoff: float = 2.0,
	):
		self.max_attempts = max_attempts
		self.delay = delay
		self.backoff = backoff
		self._attempt = 0
		self._current_delay = delay
		self._last_exception = None

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return False

	def should_continue(self) -> bool:
		"""Check if more attempts are available."""
		return self._attempt < self.max_attempts

	@property
	def attempt(self) -> int:
		"""Current attempt number (1-indexed)."""
		return self._attempt

	@property
	def last_exception(self) -> Exception:
		"""Last recorded exception, if any."""
		return self._last_exception

	def record_failure(self, exception: Exception, wait: bool = True) -> None:
		"""Record a failure and optionally wait before next attempt.

		Args:
			exception: The exception that occurred.
			wait: If True, sleep for the current backoff delay.
		"""
		self._attempt += 1
		self._last_exception = exception

		if wait and self._attempt < self.max_attempts:
			time.sleep(self._current_delay)
			self._current_delay *= self.backoff
