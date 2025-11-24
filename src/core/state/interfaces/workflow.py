"""工作流状态特化接口定义

定义专门用于工作流执行的状态接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .base import IState


class IWorkflowState(IState):
    """工作流状态接口
    
    继承自基础状态接口，添加工作流特定的功能。
    这个接口专门用于与 LangGraph 等工作流引擎交互。
    """
    
    # 工作流特定属性
    @property
    @abstractmethod
    def messages(self) -> List[Any]:
        """消息列表"""
        pass
    
    @property
    @abstractmethod
    def fields(self) -> Dict[str, Any]:
        """工作流字段"""
        pass
    
    @property
    @abstractmethod
    def values(self) -> Dict[str, Any]:
        """所有状态值"""
        pass
    
    # 工作流特定方法
    @abstractmethod
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        pass
    
    @abstractmethod
    def set_field(self, key: str, value: Any) -> 'IWorkflowState':
        """设置字段值"""
        pass
    
    @abstractmethod
    def add_message(self, message: Any) -> None:
        """添加消息"""
        pass
    
    @abstractmethod
    def get_messages(self) -> List[Any]:
        """获取消息列表"""
        pass
    
    @abstractmethod
    def with_messages(self, messages: List[Any]) -> 'IWorkflowState':
        """创建包含新消息的状态"""
        pass
    
    @abstractmethod
    def get_current_node(self) -> Optional[str]:
        """获取当前节点"""
        pass
    
    @abstractmethod
    def set_current_node(self, node: str) -> None:
        """设置当前节点"""
        pass
    
    @abstractmethod
    def get_iteration_count(self) -> int:
        """获取迭代计数"""
        pass
    
    @abstractmethod
    def increment_iteration(self) -> None:
        """增加迭代计数"""
        pass
    
    @abstractmethod
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID"""
        pass
    
    @abstractmethod
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID"""
        pass
    
    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """获取会话ID"""
        pass
    
    @abstractmethod
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID"""
        pass
    
    @abstractmethod
    def get_last_message(self) -> Any:
        """获取最后一条消息"""
        pass
    
    @abstractmethod
    def copy(self) -> 'IWorkflowState':
        """创建状态副本"""
        pass
    
    @abstractmethod
    def with_metadata(self, metadata: Dict[str, Any]) -> 'IWorkflowState':
        """创建包含新元数据的状态"""
        pass
    
    # 字典式接口支持
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值（字典式访问）"""
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """设置状态值"""
        pass


class IWorkflowStateBuilder(ABC):
    """工作流状态构建器接口
    
    用于构建工作流状态的工具接口。
    """
    
    @abstractmethod
    def with_id(self, state_id: str) -> 'IWorkflowStateBuilder':
        """设置状态ID"""
        pass
    
    @abstractmethod
    def with_data(self, data: Dict[str, Any]) -> 'IWorkflowStateBuilder':
        """设置状态数据"""
        pass
    
    @abstractmethod
    def with_metadata(self, metadata: Dict[str, Any]) -> 'IWorkflowStateBuilder':
        """设置元数据"""
        pass
    
    @abstractmethod
    def with_current_node(self, node: str) -> 'IWorkflowStateBuilder':
        """设置当前节点"""
        pass
    
    @abstractmethod
    def with_thread_id(self, thread_id: str) -> 'IWorkflowStateBuilder':
        """设置线程ID"""
        pass
    
    @abstractmethod
    def with_session_id(self, session_id: str) -> 'IWorkflowStateBuilder':
        """设置会话ID"""
        pass
    
    @abstractmethod
    def with_max_iterations(self, max_iterations: int) -> 'IWorkflowStateBuilder':
        """设置最大迭代次数"""
        pass
    
    @abstractmethod
    def add_message(self, message: Union[Any, str]) -> 'IWorkflowStateBuilder':
        """添加消息"""
        pass
    
    @abstractmethod
    def with_messages(self, messages: List[Union[Any, str]]) -> 'IWorkflowStateBuilder':
        """设置消息列表"""
        pass
    
    @abstractmethod
    def with_human_message(self, content: str) -> 'IWorkflowStateBuilder':
        """添加人类消息"""
        pass
    
    @abstractmethod
    def with_ai_message(self, content: str) -> 'IWorkflowStateBuilder':
        """添加AI消息"""
        pass
    
    @abstractmethod
    def build(self) -> IWorkflowState:
        """构建工作流状态"""
        pass