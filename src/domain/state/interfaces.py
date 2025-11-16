from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
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


class IStateLifecycleManager(ABC):
    """状态生命周期管理器接口 - 合并IEnhancedStateManager和IStateCollaborationManager
    
    管理状态的完整生命周期，包括验证、快照、历史记录和协作执行等高级功能。
    """
    
    @property
    @abstractmethod
    def crud_manager(self) -> IStateCrudManager:
        """获取底层状态管理器实例
        
        Returns:
            状态管理器实例
        """
        pass
    
    @abstractmethod
    def execute_with_state_management(
        self,
        domain_state: Any,
        executor: Callable[[Any], Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """带状态管理的执行
        
        Args:
            domain_state: 域状态对象
            executor: 执行函数，接收状态并返回修改后的状态
            context: 执行上下文
            
        Returns:
            执行后的状态对象
        """
        pass
    
    @abstractmethod
    def validate_domain_state(self, domain_state: Any) -> List[str]:
        """验证域层状态完整性"""
        pass
    
    @abstractmethod
    def create_snapshot(self, domain_state: Any, description: str = "") -> str:
        """创建状态快照"""
        pass
    
    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> Optional[Any]:
        """恢复状态快照"""
        pass
    
    @abstractmethod
    def get_snapshot_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取快照历史"""
        pass
    
    @abstractmethod
    def record_state_change(self, agent_id: str, action: str,
                          old_state: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """记录状态变化"""
        pass
    
    @abstractmethod
    def get_state_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取状态历史"""
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            性能统计字典
        """
        pass