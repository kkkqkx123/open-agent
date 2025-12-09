"""状态管理接口定义

定义状态管理接口，提供CRUD操作、历史记录、快照和高级执行功能。
此接口用于需要完整状态追踪、快照恢复和事务性状态操作的场景。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Tuple

from .base import IState
from .history import IStateHistoryManager
from .snapshot import IStateSnapshotManager
from .serializer import IStateSerializer

class IStateManager(ABC):
    """状态管理器接口
    
    定义状态管理实现的契约，提供CRUD操作、历史记录、快照和事务性操作。
    
    用于复杂场景：
    - 需要完整状态审计日志的系统
    - 需要回滚/恢复功能的应用
    - 需要事务性状态更新的场景
    """
    
    # 基础CRUD操作
    @abstractmethod
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> IState:
        """创建新状态
        
        Args:
            state_id: 状态的唯一标识符
            initial_state: 初始状态数据
            
        Returns:
            创建的状态实例
        """
        pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> Optional[IState]:
        """根据ID获取状态
        
        Args:
            state_id: 状态的唯一标识符
            
        Returns:
            状态实例，如果未找到则返回None
        """
        pass
    
    @abstractmethod
    def update_state(self, state_id: str, updates: Dict[str, Any]) -> IState:
        """更新状态
        
        Args:
            state_id: 状态的唯一标识符
            updates: 要应用的更新字典
            
        Returns:
            更新后的状态实例
        """
        pass
    
    @abstractmethod
    def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态的唯一标识符
            
        Returns:
            如果状态被删除则返回True，如果未找到则返回False
        """
        pass
    
    @abstractmethod
    def list_states(self) -> List[str]:
        """列出所有状态ID
        
        Returns:
            状态ID列表
        """
        pass
    
    # 增强功能方法
    @abstractmethod
    def create_state_with_history(self, state_id: str, initial_state: Dict[str, Any],
                                 thread_id: str) -> IState:
        """创建状态并启用历史记录
        
        Args:
            state_id: 状态ID
            initial_state: 初始状态
            thread_id: 线程ID
            
        Returns:
            创建的状态实例
        """
        pass
    
    @abstractmethod
    def update_state_with_history(self, state_id: str, updates: Dict[str, Any],
                                 thread_id: str, action: str = "update") -> IState:
        """更新状态并记录历史
        
        Args:
            state_id: 状态ID
            updates: 更新内容
            thread_id: 线程ID
            action: 执行的动作
            
        Returns:
            更新后的状态实例
        """
        pass
    
    @abstractmethod
    def create_state_snapshot(self, state_id: str, thread_id: str,
                             snapshot_name: str = "") -> str:
        """为状态创建快照
        
        Args:
            state_id: 状态ID
            thread_id: 线程ID
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
    
    @abstractmethod
    def cleanup_cache(self) -> int:
        """清理过期缓存
        
        Returns:
            清理的缓存项数量
        """
        pass

# 向后兼容性别名
IEnhancedStateManager = IStateManager