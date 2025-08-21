"""
ConvoHub Python SDK

A minimal Python client for the ConvoHub API.
"""

from .client import ConvoHubClient
from .models import (
    Thread, Branch, Message, Merge, DiffResponse,
    DiffMode, MemoryDiff, SummaryDiff, MessageRange
)

__version__ = "0.1.0"
__all__ = [
    "ConvoHubClient",
    "Thread", "Branch", "Message", "Merge", "DiffResponse",
    "DiffMode", "MemoryDiff", "SummaryDiff", "MessageRange"
]
