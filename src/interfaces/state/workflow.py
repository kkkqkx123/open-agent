"""工作流状态接口定义

定义专门用于工作流执行的状态接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

from .base import IState


class IWorkflowState(IState):
    """工作流状态接口
    
    继承自基础状态接口，添加工作流特定的功能。
    """
    
    # 工作流特定属性
    @property
    @abstractmethod
    def messages(self) -> List[Any]:
        """消息列表
        
        工作流执行过程中的消息序列
        """
        pass
    
    @property
    @abstractmethod
    def fields(self) -> Dict[str, Any]:
        """字段字典
        
        工作流执行过程中的状态数据，用于节点间传递信息。
        """
        pass
    
    @property
    @abstractmethod
    def values(self) -> Dict[str, Any]:
        """状态值字典
        
        所有状态数据的字典表示，支持字典式访问。
        """
        pass
    
    @property
    @abstractmethod
    def iteration_count(self) -> int:
        """迭代计数
        
        工作流执行过程中的迭代次数。
        """
        pass
    
    # 工作流特定方法
    @abstractmethod
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值
        
        Args:
            key: 字段键
            default: 默认值
            
        Returns:
            字段值
        """
        pass
    
    @abstractmethod
    def set_field(self, key: str, value: Any) -> 'IWorkflowState':
        """创建包含新字段值的状态
        
        Args:
            key: 字段键
            value: 字段值
            
        Returns:
            新的工作流状态实例
        """
        pass
    
    @abstractmethod
    def with_messages(self, messages: List[Any]) -> 'IWorkflowState':
        """创建包含新消息的状态
        
        Args:
            messages: 新的消息列表
            
        Returns:
            新的工作流状态实例
        """
        pass
    
    @abstractmethod
    def with_metadata(self, metadata: Dict[str, Any]) -> 'IWorkflowState':
        """创建包含新元数据的状态
        
        Args:
            metadata: 新的元数据字典
            
        Returns:
            新的工作流状态实例
        """
        pass
    
    @abstractmethod
    def add_message(self, message: Any) -> None:
        """添加消息
        
        Args:
            message: 要添加的消息
        """
        pass
    
    @abstractmethod
    def get_messages(self) -> List[Any]:
        """获取消息列表
        
        Returns:
            List[Any]: 消息列表
        """
        pass
    
    @abstractmethod
    def get_last_message(self) -> Any | None:
        """获取最后一条消息
        
        Returns:
            Any | None: 最后一条消息，如果没有则返回None
        """
        pass
    
    @abstractmethod
    def copy(self) -> 'IWorkflowState':
        """创建状态的深拷贝
        
        Returns:
            新的工作流状态实例
        """
        pass
    
    # 字典式接口支持
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值（字典式访问）
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            状态值
        """
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """设置状态值
        
        Args:
            key: 键
            value: 值
        """
        pass
    
    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        """获取状态值（字典式索引访问）
        
        Args:
            key: 键
            
        Returns:
            状态值
        """
        pass
    
    @abstractmethod
    def __setitem__(self, key: str, value: Any) -> None:
        """设置状态值（字典式索引赋值）
        
        Args:
            key: 键
            value: 值
        """
        pass


class IWorkflowStateBuilder(ABC):
    """工作流状态构建器接口
    
    用于构建工作流状态的工具接口。
    """
    
    @abstractmethod
    def add_message(self, message: Any) -> 'IWorkflowStateBuilder':
        """添加消息
        
        Args:
            message: 要添加的消息
            
        Returns:
            构建器实例
        """
        pass
    
    @abstractmethod
    def add_messages(self, messages: List[Any]) -> 'IWorkflowStateBuilder':
        """添加多个消息
        
        Args:
            messages: 要添加的消息列表
            
        Returns:
            构建器实例
        """
        pass
    
    @abstractmethod
    def set_field(self, key: str, value: Any) -> 'IWorkflowStateBuilder':
        """设置字段
        
        Args:
            key: 字段键
            value: 字段值
            
        Returns:
            构建器实例
        """
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> 'IWorkflowStateBuilder':
        """设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
            
        Returns:
            构建器实例
        """
        pass
    
    @abstractmethod
    def build(self) -> IWorkflowState:
        """构建工作流状态
        
        Returns:
            构建的工作流状态实例
        """
        pass