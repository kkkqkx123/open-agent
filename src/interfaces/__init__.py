"""Interfaces module for the application.

This module contains all interface definitions used throughout the application.
Interfaces are organized by domain and should not depend on concrete implementations.
"""

from .workflow import *
from .state import *

__all__ = [
    # Workflow interfaces will be exported from workflow.__init__.py
    # State interfaces will be exported from state.__init__.py
]