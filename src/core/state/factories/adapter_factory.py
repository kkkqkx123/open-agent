"""适配器工厂

提供创建各种适配器的工厂类，用于与现有系统集成。
"""

from typing import Any, Dict, Optional, Type, cast

from src.interfaces.state.base import IState
from src.interfaces.state.manager import IStateManager
from src.interfaces.state.workflow import IWorkflowState

# 由于中央接口层没有工具状态特化接口，使用基础接口作为替代
IToolState = IState


class StateAdapterFactory:
    """状态适配器工厂类
    
    提供创建各种适配器的统一接口，用于与现有系统集成。
    """
    
    @classmethod
    def create_workflow_adapter(cls, 
                               new_state: Optional[IWorkflowState] = None,
                               legacy_state: Optional[Any] = None) -> Any:
        """创建工作流状态适配器
        
        Args:
            new_state: 新的状态管理系统的状态对象
            legacy_state: 遗留系统的状态对象
            
        Returns:
            工作流状态适配器实例
        """
        # 动态导入以避免循环依赖
        # 工作流状态适配器暂时返回原始状态
        return new_state or legacy_state
    
    @classmethod
    def create_tool_adapter(cls,
                           new_state: Optional[IToolState] = None,
                           legacy_state: Optional[Any] = None) -> Any:
        """创建工具状态适配器
        
        Args:
            new_state: 新的状态管理系统的状态对象
            legacy_state: 遗留系统的状态对象
            
        Returns:
            工具状态适配器实例
        """
        # 动态导入以避免循环依赖
        try:
            # 创建一个简单的状态管理器包装器
            class SimpleStateManager:
                def __init__(self) -> None:
                    self._states: Dict[str, Any] = {}
                
                def get_state(self, state_id: str) -> Optional[Any]:
                    return self._states.get(state_id)
                
                def set_state(self, state_id: str, state_data: Any) -> None:
                    self._states[state_id] = state_data
                
                @classmethod
                def from_new_state(cls, new_state: Any) -> 'SimpleStateManager':
                    """从新状态创建管理器"""
                    manager = cls()
                    manager.set_state("default", new_state)
                    return manager
            
            if new_state:
                # 创建一个新的内存状态管理器来包装新状态
                return SimpleStateManager.from_new_state(new_state)
            elif legacy_state:
                return legacy_state  # 已经是遗留状态
            else:
                return SimpleStateManager()
        except ImportError:
            # 如果无法导入工具适配器，返回原始状态
            return new_state or legacy_state
    
    @classmethod
    def create_session_adapter(cls,
                              new_state: Optional[IState] = None,
                              legacy_state: Optional[Any] = None) -> Any:
        """创建会话状态适配器
        
        Args:
            new_state: 新的状态管理系统的状态对象
            legacy_state: 遗留系统的状态对象
            
        Returns:
            会话状态适配器实例
        """
        # 这里可以根据需要实现会话状态适配器
        # 目前返回原始状态
        return new_state or legacy_state
    
    @classmethod
    def create_thread_adapter(cls,
                             new_state: Optional[IState] = None,
                             legacy_state: Optional[Any] = None) -> Any:
        """创建线程状态适配器
        
        Args:
            new_state: 新的状态管理系统的状态对象
            legacy_state: 遗留系统的状态对象
            
        Returns:
            线程状态适配器实例
        """
        # 这里可以根据需要实现线程状态适配器
        # 目前返回原始状态
        return new_state or legacy_state
    
    @classmethod
    def create_manager_adapter(cls,
                              new_manager: Optional[IStateManager] = None,
                              legacy_manager: Optional[Any] = None) -> Any:
        """创建状态管理器适配器
        
        Args:
            new_manager: 新的状态管理器
            legacy_manager: 遗留的状态管理器
            
        Returns:
            状态管理器适配器实例
        """
        # 这里可以根据需要实现管理器适配器
        # 目前返回原始管理器
        return new_manager or legacy_manager
    
    @classmethod
    def adapt_legacy_to_new(cls, 
                           legacy_state: Any,
                           state_type: str) -> IState:
        """将遗留状态适配到新状态管理系统
        
        Args:
            legacy_state: 遗留状态对象
            state_type: 状态类型
            
        Returns:
            IState: 新的状态管理系统的状态对象
            
        Raises:
            ValueError: 当状态类型不支持时
        """
        # 将遗留状态转换为字典
        if hasattr(legacy_state, 'to_dict'):
            state_dict = legacy_state.to_dict()
        elif isinstance(legacy_state, dict):
            state_dict = legacy_state
        else:
            # 尝试将对象转换为字典
            state_dict = vars(legacy_state) if hasattr(legacy_state, '__dict__') else {}
        
        # 使用状态工厂创建新状态
        from .state_factory import StateFactory
        return StateFactory.create_state_from_dict(state_type, state_dict)
    
    @classmethod
    def adapt_new_to_legacy(cls,
                           new_state: IState,
                           target_type: Optional[Type] = None) -> Any:
        """将新状态管理系统适配到遗留系统
        
        Args:
            new_state: 新的状态管理系统的状态对象
            target_type: 目标类型（可选）
            
        Returns:
            遗留状态对象
        """
        # 获取状态数据
        state_dict = new_state.to_dict()
        
        # 如果指定了目标类型，尝试创建该类型的实例
        if target_type:
            if hasattr(target_type, 'from_dict'):
                return target_type.from_dict(state_dict)
            else:
                try:
                    return target_type(**state_dict)
                except TypeError:
                    # 如果构造函数不匹配，返回字典
                    return state_dict
        
        # 根据状态类型返回适当的适配器
        state_type = getattr(new_state, 'state_type', 'unknown')
        
        if state_type == 'workflow':
            return cls.create_workflow_adapter(cast(IWorkflowState, new_state) if new_state else None)
        elif state_type == 'tool':
            return cls.create_tool_adapter(cast(IToolState, new_state) if new_state else None)
        elif state_type == 'session':
            return cls.create_session_adapter(new_state)
        elif state_type == 'thread':
            return cls.create_thread_adapter(new_state)
        else:
            # 默认返回字典
            return state_dict
    
    @classmethod
    def create_bidirectional_adapter(cls,
                                    new_state: Optional[IState] = None,
                                    legacy_state: Optional[Any] = None,
                                    state_type: str = "workflow") -> Any:
        """创建双向适配器
        
        Args:
            new_state: 新的状态管理系统的状态对象
            legacy_state: 遗留系统的状态对象
            state_type: 状态类型
            
        Returns:
            双向适配器实例
        """
        if state_type == "workflow":
            return cls.create_workflow_adapter(cast(IWorkflowState, new_state) if new_state else None, legacy_state)
        elif state_type == "tool":
            return cls.create_tool_adapter(cast(IToolState, new_state) if new_state else None, legacy_state)
        elif state_type == "session":
            return cls.create_session_adapter(new_state, legacy_state)
        elif state_type == "thread":
            return cls.create_thread_adapter(new_state, legacy_state)
        else:
            # 默认返回新状态或遗留状态
            return new_state or legacy_state


# 便捷函数
def adapt_workflow_state(new_state: Optional[IWorkflowState] = None,
                        legacy_state: Optional[Any] = None) -> Any:
    """适配工作流状态的便捷函数
    
    Args:
        new_state: 新的状态管理系统的状态对象
        legacy_state: 遗留系统的状态对象
        
    Returns:
        工作流状态适配器实例
    """
    return StateAdapterFactory.create_workflow_adapter(new_state, legacy_state)


def adapt_tool_state(new_state: Optional[IToolState] = None,
                    legacy_state: Optional[Any] = None) -> Any:
    """适配工具状态的便捷函数
    
    Args:
        new_state: 新的状态管理系统的状态对象
        legacy_state: 遗留系统的状态对象
        
    Returns:
        工具状态适配器实例
    """
    return StateAdapterFactory.create_tool_adapter(new_state, legacy_state)


def migrate_legacy_to_new(legacy_state: Any, state_type: str) -> IState:
    """迁移遗留状态到新状态管理系统的便捷函数
    
    Args:
        legacy_state: 遗留状态对象
        state_type: 状态类型
        
    Returns:
        IState: 新的状态管理系统的状态对象
    """
    return StateAdapterFactory.adapt_legacy_to_new(legacy_state, state_type)


def migrate_new_to_legacy(new_state: IState, target_type: Optional[Type] = None) -> Any:
    """迁移新状态管理系统到遗留系统的便捷函数
    
    Args:
        new_state: 新的状态管理系统的状态对象
        target_type: 目标类型（可选）
        
    Returns:
        遗留状态对象
    """
    return StateAdapterFactory.adapt_new_to_legacy(new_state, target_type)