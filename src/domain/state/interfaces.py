"""统一状态管理器接口"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ...infrastructure.graph.state import AgentState


class IStateManager(ABC):
    """统一状态管理器接口"""
    
    @abstractmethod
    def serialize_state(self, state: AgentState) -> bytes:
        """序列化状态
        
        Args:
            state: Agent状态
            
        Returns:
            bytes: 序列化后的状态数据
        """
        pass

    @abstractmethod
    def deserialize_state(self, data: bytes) -> AgentState:
        """反序列化状态
        
        Args:
            data: 序列化后的状态数据
            
        Returns:
            AgentState: 反序列化后的状态
        """
        pass

    @abstractmethod
    def validate_state(self, state: AgentState) -> bool:
        """验证状态完整性
        
        Args:
            state: 要验证的状态
            
        Returns:
            bool: 状态是否有效
        """
        pass

    @abstractmethod
    def serialize_state_dict(self, state: Dict[str, Any]) -> bytes:
        """序列化状态字典
        
        Args:
            state: 状态字典
            
        Returns:
            bytes: 序列化后的状态数据
        """
        pass

    @abstractmethod
    def deserialize_state_dict(self, data: bytes) -> Dict[str, Any]:
        """反序列化状态字典
        
        Args:
            data: 序列化后的状态数据
            
        Returns:
            Dict[str, Any]: 反序列化后的状态字典
        """
        pass