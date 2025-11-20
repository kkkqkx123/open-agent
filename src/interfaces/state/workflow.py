"""工作流状态接口定义

定义工作流特定的状态接口，扩展基础状态接口以支持工作流功能。
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from .core import IState


class IWorkflowState(IState):
    """工作流状态接口
    
    扩展基础状态接口，添加工作流特定的方法和属性。
    """
    
    @abstractmethod
    def get_messages(self) -> List[Any]:
        """获取工作流状态中的消息列表
        
        Returns:
            消息列表
        """
        pass
    
    @abstractmethod
    def add_message(self, message: Any) -> None:
        """向工作流状态添加消息
        
        Args:
            message: 要添加的消息
        """
        pass
    
    @abstractmethod
    def get_last_message(self) -> Optional[Any]:
        """获取工作流状态中的最后一条消息
        
        Returns:
            最后一条消息，如果没有消息则返回None
        """
        pass
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """从状态获取值
        
        Args:
            key: 要获取的键
            default: 如果键不存在时返回的默认值
            
        Returns:
            与键关联的值，如果未找到则返回默认值
        """
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """在状态中设置值
        
        Args:
            key: 要设置的键
            value: 要与键关联的值
        """
        pass
    
    @abstractmethod
    def get_current_node(self) -> Optional[str]:
        """获取工作流中的当前节点
        
        Returns:
            当前节点名称，如果未设置则返回None
        """
        pass
    
    @abstractmethod
    def set_current_node(self, node: str) -> None:
        """设置工作流中的当前节点
        
        Args:
            node: 要设置的节点名称
        """
        pass
    
    @abstractmethod
    def get_iteration_count(self) -> int:
        """获取当前迭代次数
        
        Returns:
            当前迭代次数
        """
        pass
    
    @abstractmethod
    def increment_iteration(self) -> None:
        """增加迭代次数"""
        pass
    
    @abstractmethod
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID
        
        Returns:
            线程ID，如果未设置则返回None
        """
        pass
    
    @abstractmethod
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID
        
        Args:
            thread_id: 要设置的线程ID
        """
        pass
    
    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """获取会话ID
        
        Returns:
            会话ID，如果未设置则返回None
        """
        pass
    
    @abstractmethod
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID
        
        Args:
            session_id: 要设置的会话ID
        """
        pass