"""缓存键生成器
提供通用的缓存键生成功能。
"""

import hashlib
import json
from typing import Any, Dict, Optional, Sequence
from src.interfaces.llm import ICacheKeyGenerator


class BaseKeySerializer:
    """基础键序列化器，提供通用的序列化功能"""
    
    @staticmethod
    def serialize_value(value: Any) -> str:
        """
        序列化值为字符串
        
        Args:
            value: 要序列化的值
            
        Returns:
            序列化后的字符串
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return f"[{','.join(BaseKeySerializer.serialize_value(v) for v in value)}]"
        elif isinstance(value, dict):
            items = []
            for k, v in sorted(value.items()):
                items.append(f"{k}:{BaseKeySerializer.serialize_value(v)}")
            return f"{{{','.join(items)}}}"
        elif isinstance(value, Sequence) and not isinstance(value, str):
            return f"[{','.join(BaseKeySerializer.serialize_value(v) for v in value)}]"
        else:
            # 对于复杂对象，使用JSON序列化
            try:
                return json.dumps(value, sort_keys=True, default=str)
            except (TypeError, ValueError):
                return str(value)
    
    @staticmethod
    def hash_string(text: str) -> str:
        """生成字符串哈希"""
        return hashlib.md5(text.encode()).hexdigest()
    
    @staticmethod
    def json_dumps(obj: Any) -> str:
        """JSON序列化"""
        return json.dumps(obj, sort_keys=True)


class DefaultCacheKeyGenerator(ICacheKeyGenerator):
    """默认缓存键生成器"""
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        # 将所有参数序列化为字符串
        key_parts = []
        
        # 处理位置参数
        for arg in args:
            key_parts.append(BaseKeySerializer.serialize_value(arg))
        
        # 处理关键字参数
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{BaseKeySerializer.serialize_value(value)}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return BaseKeySerializer.hash_string(key_string)
