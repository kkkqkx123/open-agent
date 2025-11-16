"""
序列化器适配器

将通用 Serializer 适配为 IStorageSerializer 接口。
"""

from typing import Any

from ..common.serialization.serializer import Serializer
from .interfaces import IStorageSerializer


class SerializerAdapter(IStorageSerializer):
    """序列化器适配器
    
    将 Serializer 适配为 IStorageSerializer 接口。
    """
    
    def __init__(self, serializer: Serializer):
        """初始化适配器
        
        Args:
            serializer: 底层序列化器实例
        """
        self._serializer = serializer
    
    def serialize(self, data: Any) -> str:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            
        Returns:
            序列化后的字符串
        """
        result = self._serializer.serialize(data, format=self._serializer.FORMAT_JSON)
        if isinstance(result, bytes):
            return result.decode('utf-8')
        return result
    
    def deserialize(self, data: str) -> Any:
        """反序列化数据
        
        Args:
            data: 要反序列化的字符串
            
        Returns:
            反序列化后的数据
        """
        return self._serializer.deserialize(data, format=self._serializer.FORMAT_JSON)
