"""核心状态管理接口定义

定义状态管理系统的核心接口，扩展基础状态接口以支持历史记录和快照功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from src.state.interfaces import IState, IStateManager


class IStateHistoryManager(ABC):
    """状态历史管理器接口
    
    负责管理状态变更历史，包括记录、查询和回放功能。
    """
    
    @abstractmethod
    def record_state_change(self, agent_id: str, old_state: Dict[str, Any], 
                          new_state: Dict[str, Any], action: str) -> str:
        """记录状态变化
        
        Args:
            agent_id: 代理ID
            old_state: 旧状态
            new_state: 新状态
            action: 执行的动作
            
        Returns:
            历史记录ID
        """
        pass
    
    @abstractmethod
    def get_state_history(self, agent_id: str, limit: int = 100) -> List['StateHistoryEntry']:
        """获取状态历史
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            状态历史记录列表
        """
        pass
    
    @abstractmethod
    def replay_history(self, agent_id: str, base_state: Dict[str, Any], 
                      until_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """重放历史记录到指定时间点
        
        Args:
            agent_id: 代理ID
            base_state: 基础状态
            until_timestamp: 重放到的指定时间点
            
        Returns:
            重放后的状态
        """
        pass
    
    @abstractmethod
    def cleanup_old_entries(self, agent_id: str, max_entries: int = 1000) -> int:
        """清理旧的历史记录
        
        Args:
            agent_id: 代理ID
            max_entries: 保留的最大记录数
            
        Returns:
            清理的记录数量
        """
        pass


class IStateSnapshotManager(ABC):
    """状态快照管理器接口
    
    负责管理状态快照，包括创建、恢复和清理功能。
    """
    
    @abstractmethod
    def create_snapshot(self, agent_id: str, domain_state: Dict[str, Any], 
                       snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建状态快照
        
        Args:
            agent_id: 代理ID
            domain_state: 域状态
            snapshot_name: 快照名称
            metadata: 元数据
            
        Returns:
            快照ID
        """
        pass
    
    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> Optional['StateSnapshot']:
        """恢复状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复的快照，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List['StateSnapshot']:
        """获取指定代理的快照列表
        
        Args:
            agent_id: 代理ID
            limit: 返回快照数限制
            
        Returns:
            快照列表
        """
        pass
    
    @abstractmethod
    def cleanup_old_snapshots(self, agent_id: str, max_snapshots: int = 50) -> int:
        """清理旧快照
        
        Args:
            agent_id: 代理ID
            max_snapshots: 保留的最大快照数
            
        Returns:
            清理的快照数量
        """
        pass


class IStateSerializer(ABC):
    """状态序列化器接口
    
    定义状态序列化和反序列化的标准接口。
    """
    
    @abstractmethod
    def serialize_state(self, state: Dict[str, Any]) -> bytes:
        """序列化状态
        
        Args:
            state: 状态字典
            
        Returns:
            序列化后的字节数据
        """
        pass
    
    @abstractmethod
    def deserialize_state(self, data: bytes) -> Dict[str, Any]:
        """反序列化状态
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            反序列化后的状态字典
        """
        pass
    
    @abstractmethod
    def compress_data(self, data: bytes) -> bytes:
        """压缩数据
        
        Args:
            data: 要压缩的数据
            
        Returns:
            压缩后的数据
        """
        pass
    
    @abstractmethod
    def decompress_data(self, compressed_data: bytes) -> bytes:
        """解压缩数据
        
        Args:
            compressed_data: 压缩的数据
            
        Returns:
            解压缩后的数据
        """
        pass


class IEnhancedStateManager(IStateManager):
    """增强的状态管理器接口
    
    扩展基础状态管理器，添加历史记录和快照功能。
    """
    
    @property
    @abstractmethod
    def history_manager(self) -> IStateHistoryManager:
        """获取历史管理器"""
        pass
    
    @property
    @abstractmethod
    def snapshot_manager(self) -> IStateSnapshotManager:
        """获取快照管理器"""
        pass
    
    @property
    @abstractmethod
    def serializer(self) -> IStateSerializer:
        """获取序列化器"""
        pass
    
    @abstractmethod
    def create_state_with_history(self, state_id: str, initial_state: Dict[str, Any], 
                                 agent_id: str) -> IState:
        """创建状态并启用历史记录
        
        Args:
            state_id: 状态ID
            initial_state: 初始状态
            agent_id: 代理ID
            
        Returns:
            创建的状态实例
        """
        pass
    
    @abstractmethod
    def update_state_with_history(self, state_id: str, updates: Dict[str, Any], 
                                 agent_id: str, action: str = "update") -> IState:
        """更新状态并记录历史
        
        Args:
            state_id: 状态ID
            updates: 更新内容
            agent_id: 代理ID
            action: 执行的动作
            
        Returns:
            更新后的状态实例
        """
        pass
    
    @abstractmethod
    def create_state_snapshot(self, state_id: str, agent_id: str, 
                             snapshot_name: str = "") -> str:
        """为状态创建快照
        
        Args:
            state_id: 状态ID
            agent_id: 代理ID
            snapshot_name: 快照名称
            
        Returns:
            快照ID
        """
        pass
    
    @abstractmethod
    def restore_state_from_snapshot(self, snapshot_id: str, state_id: str) -> Optional[IState]:
        """从快照恢复状态
        
        Args:
            snapshot_id: 快照ID
            state_id: 要恢复的状态ID
            
        Returns:
            恢复的状态实例，如果失败则返回None
        """
        pass