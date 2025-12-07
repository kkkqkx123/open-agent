"""Infrastructure layer graph edges.

This module provides base implementations for graph edges in the infrastructure layer.
"""

from .base import BaseEdge
from .simple_edge import SimpleEdge

__all__ = [
    "BaseEdge",
    "SimpleEdge",
]