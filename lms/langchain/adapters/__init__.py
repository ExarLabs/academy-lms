"""Adapters for LangChain integration.

This package contains adapter classes that bridge the streaming
response system with various output channels (Socket.IO, webhooks, etc.).
"""

from .socketio import SocketIOStreamAdapter

__all__ = [
	"SocketIOStreamAdapter",
]
