"""状态序列化器接口定义

定义状态序列化的契约，提供序列化和反序列化功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Union, Dict

from .base import IState


class IStateSerializer(ABC):
    """状态序列化器接口
    
    定义状态序列化实现的契约，提供序列化和反序列化功能。
    """
    
    @abstractmethod
    def serialize(self, state: IState) -> Union[str, bytes]:
        """序列化状态到字符串或字节
        
        Args:
            state: 要序列化的状态
            
        Returns:
            序列化后的数据
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: Union[str, bytes]) -> IState:
        """从字符串或字节反序列化状态
        
        Args:
            data: 序列化的数据
            
        Returns:
            反序列化后的状态
        """
        pass
    
    @abstractmethod
    def serialize_state(self, state: Dict[str, Any]) -> bytes:
        """序列化状态字典到字节
        
        Args:
            state: 状态字典
            
        Returns:
            序列化后的字节数据
        """
        pass
    
    @abstractmethod
    def deserialize_state(self, data: bytes) -> Dict[str, Any]:
        """从字节反序列化状态字典
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            反序列化后的状态字典
        """
        pass