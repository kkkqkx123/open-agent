"""状态管理器接口定义

定义统一的状态管理器接口，支持功能模块的灵活组合。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Callable, Any as AnyType
from datetime import datetime
from enum import Enum


class ConflictType(Enum):
    """冲突类型枚举"""
    FIELD_MODIFICATION = "field_modification"      # 字段修改冲突
    LIST_OPERATION = "list_operation"             # 列表操作冲突
    STRUCTURE_CHANGE = "structure_change"         # 结构变化冲突
    VERSION_MISMATCH = "version_mismatch"         # 版本不匹配冲突


class ConflictResolutionStrategy(Enum):
    """冲突解决策略"""
    LAST_WRITE_WINS = "last_write_wins"           # 最后写入获胜
    FIRST_WRITE_WINS = "first_write_wins"         # 首次写入获胜
    MANUAL_RESOLUTION = "manual_resolution"       # 手动解决
    MERGE_CHANGES = "merge_changes"               # 合并变更
    REJECT_CONFLICT = "reject_conflict"           # 拒绝冲突变更


class IStateCrudManager(ABC):
    """状态CRUD管理器接口
    
    定义状态的基础CRUD操作和序列化功能，提供状态数据的基本操作能力。
    """
    
    @abstractmethod
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态
        
        Args:
            state_id: 状态ID
            initial_state: 初始状态
            
        Returns:
            创建的状态副本
        """
        pass

    @abstractmethod
    def serialize_state_to_bytes(self, state: Dict[str, Any]) -> bytes:
        """序列化状态字典为字节数据

        Args:
            state: 要序列化的状态字典

        Returns:
            序列化后的字节数据
        """
        pass

    @abstractmethod
    def deserialize_state_from_bytes(self, data: bytes) -> Dict[str, Any]:
        """从字节数据反序列化状态字典

        Args:
            data: 序列化的字节数据

        Returns:
            反序列化后的状态字典
        """
        pass
    
    @abstractmethod
    def update_state(self, state_id: str, current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态
        
        Args:
            state_id: 状态ID
            current_state: 当前状态
            updates: 更新内容
            
        Returns:
            更新后的状态
        """
        pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个状态的差异
        
        Args:
            state1: 第一个状态
            state2: 第二个状态
            
        Returns:
            差异字典
        """
        pass
    
    @abstractmethod
    def serialize_state(self, state: Dict[str, Any]) -> str:
        """序列化状态
        
        Args:
            state: 要序列化的状态
            
        Returns:
            序列化后的字符串
        """
        pass
    
    @abstractmethod
    def deserialize_state(self, serialized_data: str) -> Dict[str, Any]:
        """反序列化状态
        
        Args:
            serialized_data: 序列化的数据
            
        Returns:
            反序列化后的状态
        """
        pass


class IStateManager(IStateCrudManager):
    """状态管理器接口
    
    继承自IStateCrudManager，提供完整的状态管理功能。
    """
    pass