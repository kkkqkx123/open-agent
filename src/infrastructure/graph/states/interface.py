"""Compatibility interface module for state management following the new architecture.

This module provides backward compatibility by re-exporting the new state interfaces
from the core module, allowing existing code to continue working during the migration.
"""
from src.core.workflow.interfaces import IStateCrudManager

__all__ = ["IStateCrudManager"]