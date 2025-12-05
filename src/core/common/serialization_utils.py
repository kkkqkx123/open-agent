"""序列化工具类

提供通用的序列化和反序列化功能，减少实体类中的重复代码。
"""

from datetime import datetime
from typing import Dict, Any, Optional, Type, TypeVar, Union
from enum import Enum
import json

T = TypeVar('T')


class SerializationUtils:
    """序列化工具类"""
    
    @staticmethod
    def serialize_datetime(dt: datetime) -> str:
        """序列化datetime对象为ISO格式字符串"""
        return dt.isoformat()
    
    @staticmethod
    def deserialize_datetime(dt_str: str) -> datetime:
        """反序列化ISO格式字符串为datetime对象"""
        return datetime.fromisoformat(dt_str)
    
    @staticmethod
    def serialize_enum(enum_value: Enum) -> str:
        """序列化枚举值为字符串"""
        return str(enum_value.value)
    
    @staticmethod
    def serialize_value(value: Any) -> Any:
        """序列化任意值"""
        if isinstance(value, datetime):
            return SerializationUtils.serialize_datetime(value)
        elif isinstance(value, Enum):
            return SerializationUtils.serialize_enum(value)
        elif isinstance(value, dict):
            return {k: SerializationUtils.serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [SerializationUtils.serialize_value(item) for item in value]
        else:
            return value
    
    @staticmethod
    def to_dict(obj: Any, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """将对象转换为字典"""
        if exclude_fields is None:
            exclude_fields = []
            
        result = {}
        for key, value in obj.__dict__.items():
            # 跳过私有字段和排除的字段
            if key.startswith('_') or key in exclude_fields:
                continue
                
            # 序列化值
            serialized_value = SerializationUtils.serialize_value(value)
            result[key] = serialized_value
            
        return result
    
    @staticmethod
    def from_dict(cls: Type[T], data: Dict[str, Any],
                  field_mappings: Optional[Dict[str, str]] = None,
                  datetime_fields: Optional[list] = None,
                  enum_fields: Optional[Dict[str, Type[Enum]]] = None) -> T:
        """从字典创建类实例"""
        if field_mappings is None:
            field_mappings = {}
        if datetime_fields is None:
            datetime_fields = []
        if enum_fields is None:
            enum_fields = {}
        
        # 处理字段映射
        processed_data: Dict[str, Any] = {}
        for key, value in data.items():
            # 应用字段映射
            mapped_key = field_mappings.get(key, key)
            
            # 处理datetime字段
            if mapped_key in datetime_fields and value is not None:
                if isinstance(value, str):
                    processed_data[mapped_key] = SerializationUtils.deserialize_datetime(value)
                else:
                    processed_data[mapped_key] = value
            # 处理枚举字段
            elif mapped_key in enum_fields and value is not None:
                enum_type = enum_fields[mapped_key]
                if isinstance(value, str):
                    processed_data[mapped_key] = enum_type(value)
                elif isinstance(value, enum_type):
                    processed_data[mapped_key] = value
                else:
                    processed_data[mapped_key] = value  # 保持原值，让类构造函数处理
            else:
                processed_data[mapped_key] = value
        
        return cls(**processed_data)


class BaseEntity:
    """基础实体类，提供通用的序列化功能"""
    
    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """转换为字典"""
        return SerializationUtils.to_dict(self, exclude_fields)
    
    @classmethod
    def get_field_mappings(cls) -> Dict[str, str]:
        """获取字段映射（子类可重写）"""
        return {}
    
    @classmethod
    def get_datetime_fields(cls) -> list:
        """获取datetime字段列表（子类可重写）"""
        return []
    
    @classmethod
    def get_enum_fields(cls) -> Dict[str, Type[Enum]]:
        """获取枚举字段映射（子类可重写）"""
        return {}