"""通用核心模块

提供系统核心的通用工具和实体。
"""

from .entities import BaseContext, ExecutionContext, WorkflowExecutionContext

__all__ = [
    "BaseContext",
    "ExecutionContext",
    "WorkflowExecutionContext",
]
