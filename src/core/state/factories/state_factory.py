"""状态工厂

提供创建各种状态对象的统一工厂类。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Any, Dict, List, Optional, Type, Union, TYPE_CHECKING
from enum import Enum

# 定义状态类型的类型别名
StateType = Union[str, Enum]

from src.interfaces.state.base import IState
from src.interfaces.state.workflow import IWorkflowState
from src.interfaces.state.session import ISessionState

# 由于中央接口层没有工具、线程、检查点的特化接口，我们需要创建这些接口
# 或者使用基础接口作为替代
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 类型检查时使用这些接口，但实际运行时使用基础接口
    class IToolState(IState):
        """工具状态接口（临时定义）"""
        pass
    
    class IThreadState(IState):
        """线程状态接口（临时定义）"""
        pass
    
    class ICheckpointState(IState):
        """检查点状态接口（临时定义）"""
        pass
else:
    # 运行时使用基础接口作为替代
    IToolState = IState
    IThreadState = IState
    ICheckpointState = IState

from ..implementations.workflow_state import WorkflowState
from ..implementations.tool_state import ToolState
from ..implementations.session_state import SessionStateImpl as SessionState
from ..implementations.thread_state import ThreadState
from ..implementations.checkpoint_state import CheckpointState
from src.interfaces.state.exceptions import StateError, StateValidationError
from src.infrastructure.error_management import handle_error, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


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
    def create_state(cls, state_type: StateType, **kwargs) -> IState:
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
        if isinstance(state_type, Enum):
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
    def create_tool_state(cls, **kwargs) -> IState:
         """创建工具状态
         
         Args:
             **kwargs: 工具状态参数
             
         Returns:
             IState: 工具状态对象
         """
         return ToolState(**kwargs)
    
    @classmethod
    def create_session_state(cls, **kwargs) -> IState:
         """创建会话状态
         
         Args:
             **kwargs: 会话状态参数
             
         Returns:
             IState: 会话状态对象
         """
         return SessionState(**kwargs)  # type: ignore[abstract]
    
    @classmethod
    def create_thread_state(cls, **kwargs) -> IState:
         """创建线程状态
         
         Args:
             **kwargs: 线程状态参数
             
         Returns:
             IState: 线程状态对象
         """
         return ThreadState(**kwargs)
    
    @classmethod
    def create_checkpoint_state(cls, **kwargs) -> IState:
         """创建检查点状态
         
         Args:
             **kwargs: 检查点状态参数
             
         Returns:
             IState: 检查点状态对象
         """
         return CheckpointState(**kwargs)
    
    @classmethod
    def create_state_from_dict(cls, state_type: StateType, data: Dict[str, Any]) -> IState:
        """从字典创建状态对象
        
        Args:
            state_type: 状态类型
            data: 状态数据
            
        Returns:
            IState: 状态对象
            
        Raises:
            StateValidationError: 输入验证失败
            StateError: 创建操作失败
        """
        try:
            # 输入验证
            if state_type is None:
                raise StateValidationError("状态类型不能为None")
            
            if data is None:
                raise StateValidationError("状态数据不能为None")
            
            if not isinstance(data, dict):
                raise StateValidationError(
                    f"状态数据必须是字典类型，实际类型: {type(data).__name__}"
                )
            
            # 处理枚举类型
            if isinstance(state_type, Enum):
                state_type_str = state_type.value
            else:
                state_type_str = str(state_type)
            
            if not state_type_str:
                raise StateValidationError("状态类型不能为空字符串")
            
            # 检查状态类型是否支持
            if state_type_str not in cls._state_registry:
                supported_types = list(cls._state_registry.keys())
                raise StateValidationError(
                    f"不支持的状态类型: {state_type_str}",
                    details={
                        "state_type": state_type_str,
                        "supported_types": supported_types
                    }
                )
            
            # 获取状态类
            state_class = cls._state_registry[state_type_str]
            
            # 验证状态类
            if not isinstance(state_class, type):
                raise StateError(f"状态注册项不是有效的类类型: {state_class}")
            
            # 验证状态类是否实现了IState接口
            if not issubclass(state_class, IState):
                raise StateError(
                    f"状态类 {state_class.__name__} 必须实现 IState 接口"
                )
            
            # 从字典创建状态实例
            try:
                if hasattr(state_class, 'from_dict'):
                    # 使用from_dict方法
                    state_instance = state_class.from_dict(data)
                else:
                    # 使用构造函数
                    state_instance = state_class(**data)
                
                # 验证创建的实例
                if not isinstance(state_instance, IState):
                    raise StateError(
                        f"创建的状态实例不是IState类型: {type(state_instance).__name__}"
                    )
                
                # 验证实例的基本功能
                if not hasattr(state_instance, 'to_dict'):
                    logger.warning(f"状态类 {state_class.__name__} 缺少 to_dict 方法")
                
                logger.info(f"成功从字典创建状态: {state_type_str} -> {state_class.__name__}")
                return state_instance
                
            except StateValidationError:
                # 重新抛出验证错误
                raise
            except Exception as e:
                raise StateError(
                    f"实例化状态类 {state_class.__name__} 失败: {e}",
                    details={
                        "state_type": state_type_str,
                        "state_class": state_class.__name__,
                        "data_keys": list(data.keys())
                    }
                ) from e
                
        except StateValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "state_type": str(state_type) if state_type else None,
                "data_type": type(data).__name__ if data else None,
                "operation": "create_state_from_dict",
                "factory_class": cls.__name__
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise StateError(
                f"从字典创建状态失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e
    
    @classmethod
    def register_state_type(cls, state_type: StateType, state_class: Type[IState]) -> None:
        """注册新的状态类型
        
        Args:
            state_type: 状态类型名称
            state_class: 状态类
            
        Raises:
            TypeError: 当状态类不是IState的子类时
        """
        if not issubclass(state_class, IState):
            raise TypeError(f"State class must inherit from IState: {state_class}")
        
        # 处理枚举类型
        if isinstance(state_type, Enum):
            state_type_str = state_type.value
        else:
            state_type_str = str(state_type)
        
        cls._state_registry[state_type_str] = state_class
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的状态类型列表
        
        Returns:
            List[str]: 支持的状态类型列表
        """
        return list(cls._state_registry.keys())
    
    @classmethod
    def is_type_supported(cls, state_type: StateType) -> bool:
        """检查状态类型是否支持
        
        Args:
            state_type: 状态类型
            
        Returns:
            bool: 是否支持
        """
        # 处理枚举类型
        if isinstance(state_type, Enum):
            state_type_str = state_type.value
        else:
            state_type_str = str(state_type)
        
        return state_type_str in cls._state_registry


# 便捷函数
def create_state(state_type: StateType, **kwargs) -> IState:
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


def create_tool_state(**kwargs) -> IState:
     """创建工具状态的便捷函数
     
     Args:
         **kwargs: 工具状态参数
         
     Returns:
         IState: 工具状态对象
     """
     return StateFactory.create_tool_state(**kwargs)


def create_session_state(**kwargs) -> IState:
     """创建会话状态的便捷函数
     
     Args:
         **kwargs: 会话状态参数
         
     Returns:
         IState: 会话状态对象
     """
     return StateFactory.create_session_state(**kwargs)


def create_thread_state(**kwargs) -> IState:
     """创建线程状态的便捷函数
     
     Args:
         **kwargs: 线程状态参数
         
     Returns:
         IState: 线程状态对象
     """
     return StateFactory.create_thread_state(**kwargs)


def create_checkpoint_state(**kwargs) -> IState:
     """创建检查点状态的便捷函数
     
     Args:
         **kwargs: 检查点状态参数
         
     Returns:
         IState: 检查点状态对象
     """
     return StateFactory.create_checkpoint_state(**kwargs)