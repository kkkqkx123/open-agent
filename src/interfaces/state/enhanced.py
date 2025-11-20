"""增强状态管理接口定义

定义增强的状态管理接口，扩展基础状态管理器以支持历史记录、快照和高级执行功能。
此接口用于需要完整状态追踪、快照恢复和事务性状态操作的场景。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Tuple

from .interfaces import IState, IStateManager
from .history import IStateHistoryManager
from .snapshot import IStateSnapshotManager
from .serializer import IStateSerializer


class IEnhancedStateManager(IStateManager):
    """增强的状态管理器接口
    
    扩展基础状态管理器（IStateManager），添加历史记录、快照和事务性操作。
    
    用于复杂场景：
    - 需要完整状态审计日志的系统
    - 需要回滚/恢复功能的应用
    - 需要事务性状态更新的场景
    
    简单CRUD系统可直接使用基础IStateManager，无需此接口。
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
    
    @abstractmethod
    def execute_with_state_management(
        self,
        state_id: str,
        executor: Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bool]],  # 返回(新状态, 是否成功)
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[IState], bool]:
        """带状态管理的执行
        
        Args:
            state_id: 状态ID
            executor: 执行函数，接收当前状态并返回(新状态, 是否成功)
            context: 执行上下文
            
        Returns:
            (执行后的状态, 是否成功)
        """
        pass