"""检查点状态特化接口定义

定义专门用于检查点状态管理的接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import IState


class ICheckpointState(IState):
    """检查点状态接口
    
    继承自基础状态接口，添加检查点特定的功能。
    """
    
    @abstractmethod
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID"""
        pass
    
    @abstractmethod
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID"""
        pass
    
    @abstractmethod
    def get_checkpoint_data(self) -> Dict[str, Any]:
        """获取检查点数据"""
        pass
    
    @abstractmethod
    def set_checkpoint_data(self, checkpoint_data: Dict[str, Any]) -> None:
        """设置检查点数据"""
        pass
    
    @abstractmethod
    def get_step_number(self) -> int:
        """获取步骤编号"""
        pass
    
    @abstractmethod
    def set_step_number(self, step_number: int) -> None:
        """设置步骤编号"""
        pass
    
    @abstractmethod
    def get_node_name(self) -> Optional[str]:
        """获取节点名称"""
        pass
    
    @abstractmethod
    def set_node_name(self, node_name: str) -> None:
        """设置节点名称"""
        pass
    
    @abstractmethod
    def is_checkpoint_valid(self) -> bool:
        """检查检查点是否有效"""
        pass
    
    @abstractmethod
    def validate_checkpoint(self) -> List[str]:
        """验证检查点，返回错误列表"""
        pass
    
    @abstractmethod
    def get_config_snapshot(self) -> Dict[str, Any]:
        """获取配置快照"""
        pass
    
    @abstractmethod
    def set_config_snapshot(self, config_snapshot: Dict[str, Any]) -> None:
        """设置配置快照"""
        pass
    
    @abstractmethod
    def get_pending_writes(self) -> List[Dict[str, Any]]:
        """获取待写入操作"""
        pass
    
    @abstractmethod
    def add_pending_write(self, write_op: Dict[str, Any]) -> None:
        """添加待写入操作"""
        pass
    
    @abstractmethod
    def clear_pending_writes(self) -> None:
        """清除待写入操作"""
        pass


class ICheckpointStateManager(ABC):
    """检查点状态管理器接口"""
    
    @abstractmethod
    def create_checkpoint(self, thread_id: str, step_number: int, **kwargs) -> ICheckpointState:
        """创建检查点"""
        pass
    
    @abstractmethod
    def get_checkpoint(self, checkpoint_id: str) -> Optional[ICheckpointState]:
        """获取检查点"""
        pass
    
    @abstractmethod
    def get_thread_checkpoints(self, thread_id: str) -> List[ICheckpointState]:
        """获取线程的所有检查点"""
        pass
    
    @abstractmethod
    def get_latest_checkpoint(self, thread_id: str) -> Optional[ICheckpointState]:
        """获取最新检查点"""
        pass
    
    @abstractmethod
    def get_checkpoint_at_step(self, thread_id: str, step_number: int) -> Optional[ICheckpointState]:
        """获取指定步骤的检查点"""
        pass
    
    @abstractmethod
    def save_checkpoint(self, checkpoint: ICheckpointState) -> bool:
        """保存检查点"""
        pass
    
    @abstractmethod
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        pass
    
    @abstractmethod
    def delete_checkpoints_before(self, thread_id: str, step_number: int) -> int:
        """删除指定步骤之前的检查点，返回删除的数量"""
        pass
    
    @abstractmethod
    def cleanup_old_checkpoints(self, max_checkpoints_per_thread: int) -> int:
        """清理旧检查点，返回清理的数量"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass