"""内存存储工具类

提供内存存储相关的工具函数和静态方法。
"""

import os
import pickle
import time
from typing import Dict, Any, Optional, List, Union

from src.interfaces.storage.exceptions import StorageError

class MemoryStorageItem:
    """内存存储项
    
    封装存储的数据和元数据。
    """
    
    def __init__(
        self,
        data: Union[Dict[str, Any], bytes],
        ttl_seconds: Optional[int] = None,
        compressed: bool = False
    ):
        """初始化存储项
        
        Args:
            data: 存储的数据
            ttl_seconds: 生存时间（秒）
            compressed: 是否已压缩
        """
        self.data = data
        self.created_at = time.time()
        self.expires_at = None
        self.compressed = compressed
        self.access_count = 0
        self.last_accessed = self.created_at
        self.size = len(str(data)) if isinstance(data, dict) else len(data)
        
        if ttl_seconds:
            self.expires_at = self.created_at + ttl_seconds
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> Union[Dict[str, Any], bytes]:
        """访问数据"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data
    
    def update_data(self, data: Union[Dict[str, Any], bytes]) -> None:
        """更新数据"""
        self.data = data
        self.size = len(str(data)) if isinstance(data, dict) else len(data)
        self.last_accessed = time.time()


class MemoryStorageUtils:
    """内存存储工具类
    
    提供内存存储特定的静态工具方法。
    """
    
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
                result = pickle.load(f)
                if isinstance(result, dict):
                    return result
                else:
                    raise StorageError(f"Loaded data is not a dict: {type(result)}")
        except Exception as e:
            raise StorageError(f"Failed to load persistence data: {e}")
    
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
        from src.interfaces.storage.exceptions import StorageCapacityError
        
        # 检查条目数量限制
        if max_size and len(storage_items) >= max_size:
            raise StorageCapacityError(
                f"Storage capacity exceeded: max_size={max_size}",
                details={
                    "required_size": 1,
                    "available_size": max_size - len(storage_items)
                }
            )
        
        # 检查内存使用限制
        if max_memory_mb:
            total_size = MemoryStorageUtils.calculate_memory_usage(storage_items)
            max_bytes = max_memory_mb * 1024 * 1024
            if total_size >= max_bytes:
                raise StorageCapacityError(
                    f"Memory capacity exceeded: max_memory_mb={max_memory_mb}",
                    details={
                        "required_size": 1024,  # 估算1KB
                        "available_size": max_bytes - total_size
                    }
                )
    
    @staticmethod
    def prepare_persistence_data(storage_items: Dict[str, Any]) -> Dict[str, Any]:
        """准备持久化数据
        
        将内存存储项转换为可持久化的数据格式。
        
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