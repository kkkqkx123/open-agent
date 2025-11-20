"""Workflow execution interfaces.

This module contains interfaces related to workflow execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import IWorkflow
    from ..state.interfaces import IWorkflowState


class IWorkflowExecutor(ABC):
    """工作流执行器接口"""

    @abstractmethod
    def execute(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState', 
                context: Optional[Dict[str, Any]] = None) -> 'IWorkflowState':
        """同步执行工作流"""
        pass

    @abstractmethod
    async def execute_async(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState',
                           context: Optional[Dict[str, Any]] = None) -> 'IWorkflowState':
        """异步执行工作流"""
        pass

    @abstractmethod
    def execute_stream(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState',
                      context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """流式执行工作流"""
        pass

    @abstractmethod
    async def execute_stream_async(self, workflow: 'IWorkflow', initial_state: 'IWorkflowState',
                                 context: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流"""
        pass