"""序列化器

提供统一的序列化和反序列化功能。
"""

import json
import pickle
import hashlib
import time
import threading
from typing import Dict, Any, Union, Optional, cast
from datetime import datetime
from enum import Enum
from collections import OrderedDict

from src.interfaces.common_domain import ISerializable


class SerializationError(Exception):
    """序列化错误"""
    pass


class Serializer:
    """统一序列化器
    
    提供JSON、Pickle和Compact JSON格式的序列化功能。
    增强特性：
    - 轻量级缓存机制（可选）
    - 性能统计
    - 增强的特殊类型处理
    - 线程安全
    """
    
    FORMAT_JSON = "json"
    FORMAT_PICKLE = "pickle"
    FORMAT_COMPACT_JSON = "compact_json"
    
    def __init__(self, enable_cache: bool = False, cache_size: int = 1000):
        """初始化序列化器
        
        Args:
            enable_cache: 是否启用缓存
            cache_size: 缓存大小限制
        """
        self._enable_cache = enable_cache
        self._cache_size = cache_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._cache_lock = threading.RLock()
        
        # 性能统计
        self._stats = {
            "total_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_time": 0.0
        }
        self._stats_lock = threading.Lock()
    
    def serialize(self, data: Any, format: str = FORMAT_JSON, enable_cache: bool = True, **kwargs: Any) -> Union[str, bytes]:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            format: 序列化格式 ("json", "pickle", 或 "compact_json")
            enable_cache: 是否启用缓存（仅当全局缓存启用时有效）
            **kwargs: 其他参数
            
        Returns:
            序列化后的数据
            
        Raises:
            ValueError: 当格式不支持时
            SerializationError: 当序列化失败时
        """
        start_time = time.time()
        
        # 计算数据哈希用于缓存
        data_hash = self._calculate_hash(data) if (self._enable_cache and enable_cache) else None
        
        # 检查缓存
        if data_hash:
            cached_result = self._get_from_cache(data_hash)
            if cached_result is not None:
                self._update_stats(True, time.time() - start_time)
                return cast(Union[str, bytes], cached_result)
        
        # 检查格式
        if format not in [self.FORMAT_JSON, self.FORMAT_COMPACT_JSON, self.FORMAT_PICKLE]:
            raise SerializationError(f"不支持的序列化格式: {format}")
        
        try:
            # 预处理数据
            processed_data = self._preprocess_data(data)
            
            if format == self.FORMAT_JSON:
                result: Union[str, bytes] = json.dumps(processed_data, ensure_ascii=False, indent=2)
            elif format == self.FORMAT_COMPACT_JSON:
                result = json.dumps(processed_data, ensure_ascii=False, separators=(',', ':'))
            elif format == self.FORMAT_PICKLE:
                result = pickle.dumps(processed_data)
            else:
                # 这个分支实际上不会执行，因为上面已经检查了格式
                raise ValueError(f"不支持的序列化格式: {format}")
            
            # 缓存结果
            if data_hash:
                self._add_to_cache(data_hash, result)
            
            self._update_stats(False, time.time() - start_time)
            return result
            
        except Exception as e:
            raise SerializationError(f"序列化失败: {e}") from e
    
    def deserialize(self, data: Union[str, bytes], format: str = FORMAT_JSON, enable_cache: bool = True, **kwargs: Any) -> Any:
        """反序列化数据
        
        Args:
            data: 要反序列化的数据
            format: 数据格式 ("json", "pickle", 或 "compact_json")
            enable_cache: 是否启用缓存（仅当全局缓存启用时有效）
            **kwargs: 其他参数
            
        Returns:
            反序列化后的数据
            
        Raises:
            ValueError: 当格式不支持时
            SerializationError: 当反序列化失败时
        """
        start_time = time.time()
        
        # 检查格式
        if format not in [self.FORMAT_JSON, self.FORMAT_COMPACT_JSON, self.FORMAT_PICKLE]:
            raise SerializationError(f"不支持的格式: {format}")
        
        # 计算数据哈希用于缓存
        data_hash = self._calculate_hash(data) if (self._enable_cache and enable_cache) else None
        
        # 检查缓存
        if data_hash:
            cached_result = self._get_from_cache(f"deserialize_{data_hash}")
            if cached_result is not None:
                self._update_stats(True, time.time() - start_time)
                return cached_result
        
        try:
            if format == self.FORMAT_JSON or format == self.FORMAT_COMPACT_JSON:
                if isinstance(data, bytes):
                    json_str = data.decode('utf-8')
                else:
                    json_str = data
                loaded_data = json.loads(json_str)
                result = self._postprocess_data(loaded_data)
            elif format == self.FORMAT_PICKLE:
                if isinstance(data, str):
                    pickle_data = data.encode('utf-8')
                else:
                    pickle_data = data
                result = pickle.loads(pickle_data)
            else:
                # 这个分支实际上不会执行，因为上面已经检查了格式
                raise ValueError(f"不支持的格式: {format}")
            
            # 缓存结果
            if data_hash:
                self._add_to_cache(f"deserialize_{data_hash}", result)
            
            self._update_stats(False, time.time() - start_time)
            return result
            
        except Exception as e:
            raise SerializationError(f"反序列化失败: {e}") from e
            
    def _preprocess_data(self, data: Any) -> Any:
        """预处理数据以进行序列化
        
        Args:
            data: 原始数据
            
        Returns:
            预处理后的数据
        """
        if data is None:
            return None
        elif isinstance(data, dict):
            return {k: self._preprocess_data(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._preprocess_data(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, Enum):
            return data.value
        elif hasattr(data, 'to_dict'):
            return data.to_dict()
        elif hasattr(data, '__dict__'):
            # 处理普通对象
            result = {}
            for key, value in data.__dict__.items():
                if not key.startswith('_'):  # 跳过私有属性
                    result[key] = self._preprocess_data(value)
            return result
        elif isinstance(data, (str, int, float, bool)):
            return data
        else:
            # 其他类型，转换为字符串
            return str(data)
    
    def _postprocess_data(self, data: Any) -> Any:
        """后处理反序列化后的数据
        
        Args:
            data: 反序列化后的数据
            
        Returns:
            处理后的数据
        """
        # 这里可以添加特定的反序列化逻辑
        # 例如：将ISO格式的字符串转换回datetime对象
        # 将枚举值转换回枚举对象等
        return data
    
    def _handle_datetime(self, dt: datetime) -> str:
        """处理日期时间"""
        return dt.isoformat()
    
    def _handle_enum(self, enum_obj: Enum) -> str:
        """处理枚举类型"""
        return f"{enum_obj.__class__.__name__}.{enum_obj.name}"
    
    def _handle_serializable(self, obj: ISerializable) -> Dict[str, Any]:
        """处理可序列化对象"""
        return {
            "__type__": obj.__class__.__name__,
            "__module__": obj.__class__.__module__,
            "data": obj.to_dict()
        }
    
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
    
    def _calculate_hash(self, data: Any) -> str:
        """计算数据的哈希值
        
        Args:
            data: 要计算哈希的数据
            
        Returns:
            哈希值
        """
        try:
            serialized = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
            return hashlib.md5(serialized.encode('utf-8')).hexdigest()
        except (TypeError, ValueError):
            return hashlib.md5(str(data).encode('utf-8')).hexdigest()
    
    def calculate_hash(self, data: Any) -> str:
        """计算数据的哈希值（公共接口）
        
        Args:
            data: 要计算哈存的数据
            
        Returns:
            哈希值
        """
        return self._calculate_hash(data)
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在则返回None
        """
        if not self._enable_cache:
            return None
        
        with self._cache_lock:
            if key in self._cache:
                # 移动到末尾（LRU）
                self._cache.move_to_end(key)
                return self._cache[key]
            return None
    
    def _add_to_cache(self, key: str, value: Any) -> None:
        """添加数据到缓存
        
        Args:
            key: 缓存键
            value: 要缓存的值
        """
        if not self._enable_cache:
            return
        
        with self._cache_lock:
            # 如果缓存已满，删除最旧的条目
            if len(self._cache) >= self._cache_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = value
            self._cache.move_to_end(key)
    
    def _update_stats(self, is_cache_hit: bool, duration: float) -> None:
        """更新性能统计
        
        Args:
            is_cache_hit: 是否为缓存命中
            duration: 操作耗时
        """
        with self._stats_lock:
            self._stats["total_operations"] += 1
            if is_cache_hit:
                self._stats["cache_hits"] += 1
            else:
                self._stats["cache_misses"] += 1
            self._stats["total_time"] += duration
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            统计信息字典
        """
        with self._stats_lock:
            stats = self._stats.copy()
            
        if stats["total_operations"] > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_operations"]
            stats["average_time"] = stats["total_time"] / stats["total_operations"]
        else:
            stats["cache_hit_rate"] = 0.0
            stats["average_time"] = 0.0
        
        stats["cache_size"] = len(self._cache)
        stats["cache_capacity"] = self._cache_size
        
        return stats
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self._cache_lock:
            self._cache.clear()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self._stats_lock:
            self._stats = {
                "total_operations": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "total_time": 0.0
            }