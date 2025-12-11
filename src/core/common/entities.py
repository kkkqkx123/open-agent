"""通用数据实体定义

提供系统中使用的上下文和状态管理相关的数据类。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class BaseContext:
    """基础上下文数据类"""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ExecutionContext(BaseContext):
    """应用层执行上下文"""
    operation_id: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class WorkflowExecutionContext(BaseContext):
    """工作流执行上下文"""
    workflow_id: str = ""
    execution_id: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
