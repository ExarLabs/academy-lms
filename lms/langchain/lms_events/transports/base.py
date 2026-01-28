"""Abstract base class for event transports.

Defines the contract that all transport implementations must follow,
enabling the Strategy pattern for pluggable event delivery.
"""

from abc import ABC, abstractmethod
from typing import Any


class EventTransport(ABC):
	"""Abstract base class for event transport implementations.

	Transports are responsible for delivering events from the LMS
	to the LangChain service. Different implementations can use
	different protocols (HTTP, Redis, etc.) while maintaining
	a consistent interface.

	Example usage:
		transport = HttpEventTransport()
		if transport.is_available():
			transport.send("quiz_submission", user="user@example.com", score=85)
	"""

	@abstractmethod
	def send(self, event_type: str, **kwargs: Any) -> bool:
		"""Send an event via this transport.

		Args:
			event_type: Type of event (e.g., "quiz_submission", "enrollment")
			**kwargs: Event payload data specific to the event type

		Returns:
			True if the event was sent successfully, False otherwise.

		"""
		pass

	@abstractmethod
	def is_available(self) -> bool:
		"""Check if this transport is currently available.

		Implementations should perform a lightweight check to determine
		if the transport can accept events. This may check configuration,
		connectivity, or other prerequisites.

		Returns:
			True if the transport is ready to send events, False otherwise.
		"""
		pass

	@property
	@abstractmethod
	def name(self) -> str:
		"""Human-readable name for this transport.

		Returns:
			A string identifying this transport (e.g., "HTTP", "Redis").
		"""
		pass

	def get_diagnostics(self) -> dict[str, Any]:
		"""Get diagnostic information about this transport.

		Override in subclasses to provide transport-specific diagnostics
		useful for debugging and monitoring.

		Returns:
			Dictionary with diagnostic information.
		"""
		return {
			"transport": self.name,
			"available": self.is_available(),
		}
