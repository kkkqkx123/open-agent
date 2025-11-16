"""通用序列化器"""

from typing import Any, Dict, Union, List
import json
import pickle
from datetime import datetime
import enum
import dataclasses

from .base_serializer import BaseSerializer, SerializationError
from ..interfaces import ISerializable


class UniversalSerializer(BaseSerializer):
    """通用序列化器"""
    
    def __init__(self):
        self._type_handlers = {
            datetime: self._handle_datetime,
            'enum': self._handle_enum,
            'serializable': self._handle_serializable,
        }
    
    def serialize(self, data: Any, format: str = BaseSerializer.FORMAT_JSON, **kwargs) -> Union[str, bytes]:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            format: 序列化格式
            **kwargs: 其他参数
            
        Returns:
            序列化后的数据
        """
        try:
            processed_data = self._preprocess_data(data)
            
            if format == self.FORMAT_JSON:
                return json.dumps(processed_data, ensure_ascii=False, indent=2, default=str)
            elif format == self.FORMAT_COMPACT_JSON:
                return json.dumps(processed_data, ensure_ascii=False, separators=(',', ':'))
            elif format == self.FORMAT_PICKLE:
                return pickle.dumps(processed_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise SerializationError(f"Serialization failed: {e}")
    
    def deserialize(self, data: Union[str, bytes], format: str = BaseSerializer.FORMAT_JSON, **kwargs) -> Any:
        """反序列化数据
        
        Args:
            data: 要反序列化的数据
            format: 序列化格式
            **kwargs: 其他参数
            
        Returns:
            反序列化后的数据
        """
        try:
            if format == self.FORMAT_JSON or format == self.FORMAT_COMPACT_JSON:
                result = json.loads(data)
                return self._postprocess_data(result)
            elif format == self.FORMAT_PICKLE:
                return pickle.loads(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise SerializationError(f"Deserialization failed: {e}")
    
    def _preprocess_data(self, data: Any) -> Any:
        """预处理数据"""
        if isinstance(data, dict):
            return {k: self._preprocess_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._preprocess_data(item) for item in data]
        elif isinstance(data, datetime):
            return self._handle_datetime(data)
        elif isinstance(data, enum.Enum):  # 更准确的枚举检测
            return self._handle_enum(data)
        elif isinstance(data, ISerializable):
            return self._handle_serializable(data)
        elif dataclasses.is_dataclass(data) and not isinstance(data, type):
            # 处理实现了ISerializable的dataclass对象
            if isinstance(data, ISerializable):
                return data.to_dict()
            else:
                # 对于普通dataclass，使用asdict转换为字典
                return dataclasses.asdict(data)
        else:
            return data
    
    def _postprocess_data(self, data: Any) -> Any:
        """后处理数据"""
        # 这里可以添加特定的反序列化逻辑
        return data
    
    def _handle_datetime(self, dt: datetime) -> str:
        """处理日期时间"""
        return dt.isoformat()
    
    def _handle_enum(self, enum_obj: enum.Enum) -> str:
        """处理枚举类型"""
        return f"{enum_obj.__class__.__name__}.{enum_obj.name}"
    
    def _handle_serializable(self, obj: ISerializable) -> Dict[str, Any]:
        """处理可序列化对象"""
        return {
            "__type__": obj.__class__.__name__,
            "__module__": obj.__class__.__module__,
            "data": obj.to_dict()
        }