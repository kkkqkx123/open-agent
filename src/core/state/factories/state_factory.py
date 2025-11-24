"""状态工厂

提供创建各种状态对象的统一工厂类。
"""

from typing import Any, Dict, List, Optional, Type, Union

from ..interfaces.base import IState
from ..interfaces.workflow import IWorkflowState
from ..interfaces.tools import IToolState
from ..interfaces.sessions import ISessionState
from ..interfaces.threads import IThreadState
from ..interfaces.checkpoints import ICheckpointState

from ..implementations.workflow_state import WorkflowState
from ..implementations.tool_state import ToolState
from ..implementations.session_state import SessionState
from ..implementations.thread_state import ThreadState
from ..implementations.checkpoint_state import CheckpointState


class StateFactory:
    """状态工厂类
    
    提供创建各种状态对象的统一接口。
    """
    
    # 状态类型映射
    _state_registry: Dict[str, Type[IState]] = {
        "workflow": WorkflowState,
        "tool": ToolState,
        "session": SessionState,
        "thread": ThreadState,
        "checkpoint": CheckpointState
    }
    
    @classmethod
    def create_state(cls, state_type: str, **kwargs) -> IState:
        """创建状态对象
        
        Args:
            state_type: 状态类型
            **kwargs: 状态参数
            
        Returns:
            IState: 状态对象
            
        Raises:
            ValueError: 当状态类型不支持时
        """
        # 处理枚举类型
        if hasattr(state_type, 'value'):
            state_type_str = state_type.value
        else:
            state_type_str = str(state_type)
        
        # 检查状态类型是否支持
        if state_type_str not in cls._state_registry:
            raise ValueError(f"Unsupported state type: {state_type_str}")
        
        # 获取状态类
        state_class = cls._state_registry[state_type_str]
        
        # 创建状态实例
        return state_class(**kwargs)
    
    @classmethod
    def create_workflow_state(cls, **kwargs) -> IWorkflowState:
        """创建工作流状态
        
        Args:
            **kwargs: 工作流状态参数
            
        Returns:
            IWorkflowState: 工作流状态对象
        """
        return WorkflowState(**kwargs)
    
    @classmethod
    def create_tool_state(cls, **kwargs) -> IToolState:
        """创建工具状态
        
        Args:
            **kwargs: 工具状态参数
            
        Returns:
            IToolState: 工具状态对象
        """
        return ToolState(**kwargs)
    
    @classmethod
    def create_session_state(cls, **kwargs) -> ISessionState:
        """创建会话状态
        
        Args:
            **kwargs: 会话状态参数
            
        Returns:
            ISessionState: 会话状态对象
        """
        return SessionState(**kwargs)
    
    @classmethod
    def create_thread_state(cls, **kwargs) -> IThreadState:
        """创建线程状态
        
        Args:
            **kwargs: 线程状态参数
            
        Returns:
            IThreadState: 线程状态对象
        """
        return ThreadState(**kwargs)
    
    @classmethod
    def create_checkpoint_state(cls, **kwargs) -> ICheckpointState:
        """创建检查点状态
        
        Args:
            **kwargs: 检查点状态参数
            
        Returns:
            ICheckpointState: 检查点状态对象
        """
        return CheckpointState(**kwargs)
    
    @classmethod
    def create_state_from_dict(cls, state_type: str, data: Dict[str, Any]) -> IState:
        """从字典创建状态对象
        
        Args:
            state_type: 状态类型
            data: 状态数据
            
        Returns:
            IState: 状态对象
            
        Raises:
            ValueError: 当状态类型不支持时
        """
        # 处理枚举类型
        if hasattr(state_type, 'value'):
            state_type_str = state_type.value
        else:
            state_type_str = str(state_type)
        
        # 检查状态类型是否支持
        if state_type_str not in cls._state_registry:
            raise ValueError(f"Unsupported state type: {state_type_str}")
        
        # 获取状态类
        state_class = cls._state_registry[state_type_str]
        
        # 从字典创建状态实例
        if hasattr(state_class, 'from_dict'):
            return state_class.from_dict(data)
        else:
            # 如果没有from_dict方法，使用构造函数
            return state_class(**data)
    
    @classmethod
    def register_state_type(cls, state_type: str, state_class: Type[IState]) -> None:
        """注册新的状态类型
        
        Args:
            state_type: 状态类型名称
            state_class: 状态类
            
        Raises:
            TypeError: 当状态类不是IState的子类时
        """
        if not issubclass(state_class, IState):
            raise TypeError(f"State class must inherit from IState: {state_class}")
        
        cls._state_registry[state_type] = state_class
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的状态类型列表
        
        Returns:
            List[str]: 支持的状态类型列表
        """
        return list(cls._state_registry.keys())
    
    @classmethod
    def is_type_supported(cls, state_type: str) -> bool:
        """检查状态类型是否支持
        
        Args:
            state_type: 状态类型
            
        Returns:
            bool: 是否支持
        """
        # 处理枚举类型
        if hasattr(state_type, 'value'):
            state_type_str = state_type.value
        else:
            state_type_str = str(state_type)
        
        return state_type_str in cls._state_registry


# 便捷函数
def create_state(state_type: str, **kwargs) -> IState:
    """创建状态对象的便捷函数
    
    Args:
        state_type: 状态类型
        **kwargs: 状态参数
        
    Returns:
        IState: 状态对象
    """
    return StateFactory.create_state(state_type, **kwargs)


def create_workflow_state(**kwargs) -> IWorkflowState:
    """创建工作流状态的便捷函数
    
    Args:
        **kwargs: 工作流状态参数
        
    Returns:
        IWorkflowState: 工作流状态对象
    """
    return StateFactory.create_workflow_state(**kwargs)


def create_tool_state(**kwargs) -> IToolState:
    """创建工具状态的便捷函数
    
    Args:
        **kwargs: 工具状态参数
        
    Returns:
        IToolState: 工具状态对象
    """
    return StateFactory.create_tool_state(**kwargs)


def create_session_state(**kwargs) -> ISessionState:
    """创建会话状态的便捷函数
    
    Args:
        **kwargs: 会话状态参数
        
    Returns:
        ISessionState: 会话状态对象
    """
    return StateFactory.create_session_state(**kwargs)


def create_thread_state(**kwargs) -> IThreadState:
    """创建线程状态的便捷函数
    
    Args:
        **kwargs: 线程状态参数
        
    Returns:
        IThreadState: 线程状态对象
    """
    return StateFactory.create_thread_state(**kwargs)


def create_checkpoint_state(**kwargs) -> ICheckpointState:
    """创建检查点状态的便捷函数
    
    Args:
        **kwargs: 检查点状态参数
        
    Returns:
        ICheckpointState: 检查点状态对象
    """
    return StateFactory.create_checkpoint_state(**kwargs)