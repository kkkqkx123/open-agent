"""Checkpoint核心层接口定义

定义checkpoint核心层内部使用的接口。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .entities import CheckpointData


class IInternalCheckpointStorage(ABC):
    """内部Checkpoint存储接口
    
    定义核心层内部使用的checkpoint存储接口。
    """
    
    @abstractmethod
    async def save_checkpoint(self, checkpoint_data: CheckpointData) -> bool:
        """保存checkpoint数据"""
        pass
    
    @abstractmethod
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointData]:
        """加载checkpoint数据"""
        pass
    
    @abstractmethod
    async def list_checkpoints(self, thread_id: str) -> List[CheckpointData]:
        """列出指定thread的所有checkpoint"""
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的checkpoint"""
        pass
    
    @abstractmethod
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[CheckpointData]:
        """获取thread的最新checkpoint"""
        pass