"""内存存储工具类

提供内存存储相关的工具函数和静态方法。
"""

import gzip
import json
import os
import pickle
import time
from typing import Dict, Any, Optional, List, Union

from src.core.state.exceptions import StorageError


class MemoryStorageUtils:
    """内存存储工具类
    
    提供内存存储相关的静态工具方法。
    """
    
    @staticmethod
    def compress_data(data: Dict[str, Any]) -> bytes:
        """压缩数据
        
        Args:
            data: 要压缩的数据
            
        Returns:
            压缩后的数据
            
        Raises:
            StorageError: 压缩失败时抛出
        """
        try:
            # 序列化为JSON
            json_str = json.dumps(data, default=str)
            # 压缩
            return gzip.compress(json_str.encode('utf-8'))
        except Exception as e:
            raise StorageError(f"Failed to compress data: {e}")
    
    @staticmethod
    def decompress_data(compressed_data: bytes) -> Dict[str, Any]:
        """解压缩数据
        
        Args:
            compressed_data: 压缩的数据
            
        Returns:
            解压缩后的数据
            
        Raises:
            StorageError: 解压缩失败时抛出
        """
        try:
            # 解压缩
            json_str = gzip.decompress(compressed_data).decode('utf-8')
            # 反序列化
            result = json.loads(json_str)
            # 确保返回的是 Dict[str, Any] 类型
            if isinstance(result, dict):
                return result
            else:
                raise StorageError(f"Decompressed data is not a dict: {type(result)}")
        except Exception as e:
            raise StorageError(f"Failed to decompress data: {e}")
    
    @staticmethod
    def matches_filters(data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配过滤器
        """
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in data:
                return False
            
            if isinstance(value, dict):
                # 支持操作符
                if "$eq" in value and data[key] != value["$eq"]:
                    return False
                elif "$ne" in value and data[key] == value["$ne"]:
                    return False
                elif "$in" in value and data[key] not in value["$in"]:
                    return False
                elif "$nin" in value and data[key] in value["$nin"]:
                    return False
                elif "$gt" in value and data[key] <= value["$gt"]:
                    return False
                elif "$gte" in value and data[key] < value["$gte"]:
                    return False
                elif "$lt" in value and data[key] >= value["$lt"]:
                    return False
                elif "$lte" in value and data[key] > value["$lte"]:
                    return False
            elif data[key] != value:
                return False
        
        return True
    
    @staticmethod
    def save_persistence_data(storage_data: Dict[str, Any], persistence_path: str) -> None:
        """保存持久化数据
        
        Args:
            storage_data: 存储数据
            persistence_path: 持久化文件路径
            
        Raises:
            StorageError: 保存失败时抛出
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(persistence_path), exist_ok=True)
            
            # 保存到文件
            with open(persistence_path, 'wb') as f:
                pickle.dump(storage_data, f)
        except Exception as e:
            raise StorageError(f"Failed to save persistence data: {e}")
    
    @staticmethod
    def load_persistence_data(persistence_path: str) -> Optional[Dict[str, Any]]:
        """加载持久化数据
        
        Args:
            persistence_path: 持久化文件路径
            
        Returns:
            加载的数据，如果文件不存在则返回None
            
        Raises:
            StorageError: 加载失败时抛出
        """
        if not os.path.exists(persistence_path):
            return None
        
        try:
            # 从文件加载
            with open(persistence_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            raise StorageError(f"Failed to load persistence data: {e}")
    
    @staticmethod
    def should_compress_data(data: Dict[str, Any], threshold: int) -> bool:
        """判断是否应该压缩数据
        
        Args:
            data: 要检查的数据
            threshold: 压缩阈值
            
        Returns:
            是否应该压缩
        """
        return len(str(data)) > threshold
    
    @staticmethod
    def calculate_memory_usage(storage_items: Dict[str, Any]) -> int:
        """计算内存使用量
        
        Args:
            storage_items: 存储项字典
            
        Returns:
            内存使用量（字节）
        """
        total_size = 0
        for item in storage_items.values():
            if hasattr(item, 'size'):
                total_size += item.size
            else:
                # 估算大小
                total_size += len(str(item))
        return total_size
    
    @staticmethod
    def calculate_compression_ratio(storage_items: Dict[str, Any]) -> float:
        """计算压缩比
        
        Args:
            storage_items: 存储项字典
            
        Returns:
            压缩比（0-1之间）
        """
        if not storage_items:
            return 0.0
        
        compressed_items = sum(1 for item in storage_items.values() 
                            if hasattr(item, 'compressed') and item.compressed)
        return compressed_items / len(storage_items)
    
    @staticmethod
    def get_expired_items(storage_items: Dict[str, Any]) -> List[str]:
        """获取过期的项ID列表
        
        Args:
            storage_items: 存储项字典
            
        Returns:
            过期项的ID列表
        """
        expired_items = []
        current_time = time.time()
        
        for item_id, item in storage_items.items():
            if (hasattr(item, 'expires_at') and 
                item.expires_at is not None and 
                current_time > item.expires_at):
                expired_items.append(item_id)
        
        return expired_items
    
    @staticmethod
    def validate_capacity(
        storage_items: Dict[str, Any], 
        max_size: Optional[int] = None, 
        max_memory_mb: Optional[int] = None
    ) -> None:
        """验证容量限制
        
        Args:
            storage_items: 存储项字典
            max_size: 最大条目数量
            max_memory_mb: 最大内存使用量（MB）
            
        Raises:
            StorageCapacityError: 超过容量限制时抛出
        """
        from src.core.state.exceptions import StorageCapacityError
        
        # 检查条目数量限制
        if max_size and len(storage_items) >= max_size:
            raise StorageCapacityError(
                f"Storage capacity exceeded: max_size={max_size}",
                required_size=1,
                available_size=max_size - len(storage_items)
            )
        
        # 检查内存使用限制
        if max_memory_mb:
            total_size = MemoryStorageUtils.calculate_memory_usage(storage_items)
            max_bytes = max_memory_mb * 1024 * 1024
            if total_size >= max_bytes:
                raise StorageCapacityError(
                    f"Memory capacity exceeded: max_memory_mb={max_memory_mb}",
                    required_size=1024,  # 估算1KB
                    available_size=max_bytes - total_size
                )
    
    @staticmethod
    def prepare_persistence_data(storage_items: Dict[str, Any]) -> Dict[str, Any]:
        """准备持久化数据
        
        Args:
            storage_items: 存储项字典
            
        Returns:
            准备好的持久化数据
        """
        persistence_data = {}
        for item_id, item in storage_items.items():
            persistence_data[item_id] = {
                "data": item.data,
                "created_at": item.created_at,
                "expires_at": getattr(item, 'expires_at', None),
                "compressed": getattr(item, 'compressed', False),
                "access_count": getattr(item, 'access_count', 0),
                "last_accessed": getattr(item, 'last_accessed', item.created_at),
                "size": getattr(item, 'size', len(str(item.data)) if isinstance(item.data, dict) else len(item.data))
            }
        return persistence_data
    
    @staticmethod
    def restore_persistence_data(persistence_data: Dict[str, Any]) -> Dict[str, Any]:
        """恢复持久化数据
        
        Args:
            persistence_data: 持久化数据
            
        Returns:
            恢复的存储项字典
        """
        from .memory_backend import MemoryStorageItem
        
        storage_items = {}
        current_time = time.time()
        
        for item_id, item_data in persistence_data.items():
            # 检查是否过期
            if item_data.get("expires_at") and current_time > item_data["expires_at"]:
                continue
            
            # 创建存储项
            item = MemoryStorageItem(
                item_data["data"],
                None,  # TTL已包含在expires_at中
                item_data.get("compressed", False)
            )
            item.created_at = item_data["created_at"]
            item.expires_at = item_data.get("expires_at")
            item.access_count = item_data.get("access_count", 0)
            item.last_accessed = item_data.get("last_accessed", item.created_at)
            item.size = item_data.get("size", len(str(item_data["data"])) if isinstance(item_data["data"], dict) else len(item_data["data"]))
            
            storage_items[item_id] = item
        
        return storage_items