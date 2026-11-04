"""Exception types shared by seekport modules."""
from __future__ import annotations


class SeekportError(Exception):
    """Base class; str(e) is safe to show to a user or an agent."""


class ConfigError(SeekportError):
    """Bad input or missing configuration — retrying will not help."""


class APIError(SeekportError):
    """The API rejected the request, the transport failed, or it kept failing."""
