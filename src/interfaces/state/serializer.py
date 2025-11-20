"""状态序列化接口定义

定义状态序列化和反序列化的标准接口。
"""

from abc import ABC, abstractmethod
from typing import Union

from .core import IState


class IStateSerializer(ABC):
    """状态序列化器接口
    
    定义状态序列化和反序列化的标准接口。
    """
    
    @abstractmethod
    def serialize_state(self, state: dict) -> bytes:
        """序列化状态
        
        Args:
            state: 状态字典
            
        Returns:
            序列化后的字节数据
        """
        pass
    
    @abstractmethod
    def deserialize_state(self, data: bytes) -> dict:
        """反序列化状态
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            反序列化后的状态字典
        """
        pass
    
    @abstractmethod
    def compress_data(self, data: bytes) -> bytes:
        """压缩数据
        
        Args:
            data: 要压缩的数据
            
        Returns:
            压缩后的数据
        """
        pass
    
    @abstractmethod
    def decompress_data(self, compressed_data: bytes) -> bytes:
        """解压缩数据
        
        Args:
            compressed_data: 压缩的数据
            
        Returns:
            解压缩后的数据
        """
        pass
    
    @abstractmethod
    def serialize(self, state: IState) -> Union[str, bytes]:
        """序列化状态到字符串或字节
        
        Args:
            state: 要序列化的状态
            
        Returns:
            序列化的状态数据
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: Union[str, bytes]) -> IState:
        """从字符串或字节反序列化状态
        
        Args:
            data: 序列化的状态数据
            
        Returns:
            反序列化的状态实例
        """
        pass