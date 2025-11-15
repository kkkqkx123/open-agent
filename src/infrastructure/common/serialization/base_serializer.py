"""序列化器基类"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union
import json
import pickle
import hashlib
from datetime import datetime

from ..interfaces import ISerializable


class BaseSerializer(ABC):
    """序列化器基类"""
    
    FORMAT_JSON = "json"
    FORMAT_PICKLE = "pickle"
    FORMAT_COMPACT_JSON = "compact_json"
    
    @abstractmethod
    def serialize(self, data: Any, format: str = FORMAT_JSON, **kwargs) -> Union[str, bytes]:
        """序列化数据"""
        pass
    
    @abstractmethod
    def deserialize(self, data: Union[str, bytes], format: str = FORMAT_JSON, **kwargs) -> Any:
        """反序列化数据"""
        pass
    
    def handle_enums(self, data: Any) -> Any:
        """处理枚举类型"""
        if hasattr(data, 'value'):
            return data.value
        return data
    
    def handle_datetime(self, data: Any) -> Any:
        """处理日期时间类型"""
        if isinstance(data, datetime):
            return data.isoformat()
        return data
    
    def calculate_hash(self, data: Any) -> str:
        """计算数据哈希"""
        try:
            serialized = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(serialized.encode()).hexdigest()
        except (TypeError, ValueError):
            return hashlib.md5(str(data).encode()).hexdigest()


class SerializationError(Exception):
    """序列化错误"""
    pass