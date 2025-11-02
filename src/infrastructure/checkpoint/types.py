"""Checkpoint类型定义

定义checkpoint系统中使用的类型和协议。
"""

from typing import Protocol, Union, Dict, Any, Optional, List, Tuple, runtime_checkable, TypedDict
from datetime import datetime

from langgraph.checkpoint.base import CheckpointTuple, Checkpoint
from langchain_core.runnables.config import RunnableConfig
@runtime_checkable
class CheckpointerProtocol(Protocol):
    """Checkpointer协议定义
    
    定义LangGraph checkpointer需要实现的基本方法。
    """
    
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
            metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> None:
        """保存checkpoint"""
        ...
    
    def get(self, config: Dict[str, Any]) -> Optional[Union[Dict[str, Any], CheckpointTuple]]:
        """获取checkpoint"""
        ...
    
    def list(self, config: Dict[str, Any], limit: Optional[int] = None) -> List[CheckpointTuple]:
        """列出checkpoint"""
        ...
    
    def delete_thread(self, thread_id: str) -> None:
        """删除线程"""
        ...
        """删除线程"""
        ...


class CheckpointData(TypedDict, total=False):
    """Checkpoint数据类型定义"""
    
    id: str
    thread_id: str
    session_id: str
    workflow_id: str
    state_data: Any
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class CheckpointConfig(TypedDict, total=False):
    """Checkpoint配置类型定义"""
    
    max_checkpoints_per_thread: int
    enable_compression: bool
    enable_performance_monitoring: bool
    cleanup_threshold: int


class CheckpointError(Exception):
    """Checkpoint操作基础异常"""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint未找到异常"""
    pass


class CheckpointStorageError(CheckpointError):
    """Checkpoint存储异常"""
    pass


class CheckpointValidationError(CheckpointError):
    """Checkpoint验证异常"""
    pass