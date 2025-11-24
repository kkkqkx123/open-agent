"""优化的内存存储后端

提供基于内存的存储后端实现，使用新的通用工具和基类。
"""

import time
import uuid
import threading
import logging
from typing import Dict, Any, Optional, List, Union

from core.common.exceptions.state import (
    StorageError,
    StorageConnectionError,
    StorageCapacityError
)
from ..adapters.base import StorageBackend
from ..utils.common_utils import StorageCommonUtils
from ..utils.memory_utils import MemoryStorageUtils, MemoryStorageItem


logger = logging.getLogger(__name__)




class MemoryStorageBackend(StorageBackend):
    """优化的内存存储后端实现
    
    提供基于内存的存储后端，使用新的通用工具减少重复代码。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化内存存储
        
        Args:
            **config: 配置参数
        """
        super().__init__(**config)
        
        # 内存存储特定配置
        self.max_size = config.get("max_size")
        self.max_memory_mb = config.get("max_memory_mb")
        self.enable_persistence = config.get("enable_persistence", False)
        self.persistence_path = config.get("persistence_path")
        self.persistence_interval_seconds = config.get("persistence_interval_seconds", 600)
        
        # 存储数据
        self._storage: Dict[str, MemoryStorageItem] = {}
        
        # 持久化相关
        self._persistence_lock = threading.Lock()
        self._last_persistence_time = 0
        
        # 扩展统计信息
        self._stats["memory_usage_bytes"] = 0
        self._stats["compression_ratio"] = 0.0
        
        logger.info("MemoryStorageBackend initialized")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 加载持久化数据
            if self.enable_persistence:
                await self._load_persistence()
            
            # 调用父类的连接逻辑（启动清理和备份任务）
            await super().connect()
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect MemoryStorageBackend: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 保存持久化数据
            if self.enable_persistence:
                await self._save_persistence()
            
            # 清理数据
            with self._thread_lock:
                self._storage.clear()
            
            # 调用父类的断开逻辑
            await super().disconnect()
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect MemoryStorageBackend: {e}")
    
    async def save_impl(self, data: Union[Dict[str, Any], bytes], compressed: bool = False) -> str:
        """实际保存实现"""
        try:
            # 检查容量限制
            self._validate_capacity()
            
            # 生成ID（如果没有）
            if isinstance(data, dict) and "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            item_id: str = data["id"] if isinstance(data, dict) else str(uuid.uuid4())
            
            # 创建存储项
            ttl_seconds = self.default_ttl_seconds if self.enable_ttl else None
            item = MemoryStorageItem(data, ttl_seconds, compressed)
            
            # 保存数据
            async with self._lock:
                with self._thread_lock:
                    self._storage[item_id] = item
                    self._update_memory_stats()
            
            return item_id
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
    
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        try:
            async with self._lock:
                with self._thread_lock:
                    item = self._storage.get(id)
                    if item is None:
                        return None
                    
                    # 检查是否过期
                    if item.is_expired():
                        del self._storage[id]
                        self._stats["expired_items_cleaned"] += 1
                        self._update_memory_stats()
                        return None
                    
                    # 访问数据
                    data = item.access()
            
            # 解压缩数据（如果需要）
            if item.compressed and isinstance(data, bytes):
                from src.core.state.base import BaseStateSerializer
                serializer = BaseStateSerializer(compression=True)
                data = serializer.deserialize_state(data)
            
            # 确保返回值是 Dict[str, Any] 或 None
            if isinstance(data, dict):
                return data
            else:
                # 如果数据不是字典，返回 None 以符合接口
                logger.warning(f"Unexpected data type loaded: {type(data)}")
                return None
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        try:
            async with self._lock:
                with self._thread_lock:
                    if id in self._storage:
                        del self._storage[id]
                        self._update_memory_stats()
                        return True
                    return False
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
    
    async def list_impl(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """实际列表实现"""
        try:
            results = []
            
            async with self._lock:
                with self._thread_lock:
                    # 应用过滤器
                    for item_id, item in self._storage.items():
                        # 检查是否过期
                        if item.is_expired():
                            del self._storage[item_id]
                            self._stats["expired_items_cleaned"] += 1
                            self._update_memory_stats()
                            continue
                        
                        # 获取数据
                        data = item.access()
                        
                        # 解压缩数据（如果需要）
                        if item.compressed and isinstance(data, bytes):
                            from src.core.state.base import BaseStateSerializer
                            serializer = BaseStateSerializer(compression=True)
                            data = serializer.deserialize_state(data)
                        
                        # 检查过滤器
                        if isinstance(data, dict) and StorageCommonUtils.matches_filters(data, filters):
                            results.append(data)
                            
                            # 检查限制
                            if limit and len(results) >= limit:
                                break
            
            return results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        try:
            with self._thread_lock:
                # 计算内存使用量
                total_size = self._calculate_memory_usage()
                
                # 计算压缩比
                compression_ratio = self._calculate_compression_ratio()
                
                # 更新统计信息
                self._stats["memory_usage_bytes"] = total_size
                self._stats["compression_ratio"] = compression_ratio
            
            # 使用健康检查助手准备响应
            from src.core.state.statistics import StorageStatistics, HealthCheckHelper
            stats = StorageStatistics(
                status="healthy",
                timestamp=time.time(),
                total_size_bytes=total_size,
                total_items=len(self._storage),
                total_records=len(self._storage),
                total_operations=self._stats.get("operations", 0),
                total_reads=self._stats.get("reads", 0),
                total_writes=self._stats.get("writes", 0),
                total_deletes=self._stats.get("deletes", 0),
            )
            return HealthCheckHelper.prepare_health_check_response(
                status="healthy",
                stats=stats,
                config={
                    "max_size": self.max_size,
                    "max_memory_mb": self.max_memory_mb,
                    "enable_ttl": self.enable_ttl,
                    "enable_compression": self.enable_compression,
                    "enable_persistence": self.enable_persistence,
                },
                item_count=len(self._storage),
                memory_usage_bytes=self._stats["memory_usage_bytes"],
                compression_ratio=self._stats["compression_ratio"],
            )
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
    
    # 内部辅助方法
    def _validate_capacity(self) -> None:
        """验证容量限制"""
        if self.max_size and len(self._storage) >= self.max_size:
            raise StorageCapacityError(
                f"Storage capacity exceeded: max_size={self.max_size}",
                required_size=1,
                available_size=self.max_size - len(self._storage)
            )
        
        if self.max_memory_mb:
            total_size = self._calculate_memory_usage()
            max_bytes = self.max_memory_mb * 1024 * 1024
            if total_size >= max_bytes:
                raise StorageCapacityError(
                    f"Memory capacity exceeded: max_memory_mb={self.max_memory_mb}",
                    required_size=1024,
                    available_size=max_bytes - total_size
                )
    
    def _calculate_memory_usage(self) -> int:
        """计算内存使用量"""
        total_size = 0
        for item in self._storage.values():
            total_size += item.size
        return total_size
    
    def _calculate_compression_ratio(self) -> float:
        """计算压缩比"""
        if not self._storage:
            return 0.0
        
        compressed_items = sum(1 for item in self._storage.values() if item.compressed)
        return compressed_items / len(self._storage)
    
    def _update_memory_stats(self) -> None:
        """更新内存统计信息"""
        self._stats["memory_usage_bytes"] = self._calculate_memory_usage()
        self._stats["compression_ratio"] = self._calculate_compression_ratio()
    
    async def _cleanup_expired_items_impl(self) -> None:
        """清理过期项的内存存储特定实现
        
        使用内存优化的方式一次性删除所有过期项。
        """
        try:
            expired_items = []
            
            async with self._lock:
                with self._thread_lock:
                    # 首先收集所有过期项
                    for item_id, item in self._storage.items():
                        if item.is_expired():
                            expired_items.append(item_id)
                    
                    # 然后删除所有过期项
                    for item_id in expired_items:
                        del self._storage[item_id]
                        self._stats["expired_items_cleaned"] += 1
                    
                    # 更新统计信息
                    if expired_items:
                        self._update_memory_stats()
                        logger.debug(f"Cleaned {len(expired_items)} expired items from memory storage")
                        
        except Exception as e:
            logger.error(f"Error cleaning expired items in memory storage: {e}")
    
    async def _save_persistence(self) -> None:
        """保存持久化数据"""
        if not self.persistence_path:
            return
        
        try:
            with self._persistence_lock:
                # 准备持久化数据
                persistence_data = {}
                for item_id, item in self._storage.items():
                    persistence_data[item_id] = {
                        "data": item.data,
                        "created_at": item.created_at,
                        "expires_at": item.expires_at,
                        "compressed": item.compressed,
                        "access_count": item.access_count,
                        "last_accessed": item.last_accessed,
                        "size": item.size,
                    }
                
                # 保存到文件
                MemoryStorageUtils.save_persistence_data(persistence_data, self.persistence_path)
                
                logger.debug(f"Saved {len(persistence_data)} items to persistence file")
                
        except Exception as e:
            logger.error(f"Failed to save persistence data: {e}")
    
    async def _load_persistence(self) -> None:
        """加载持久化数据"""
        if not self.persistence_path:
            return
        
        try:
            with self._persistence_lock:
                # 加载持久化数据
                persistence_data = MemoryStorageUtils.load_persistence_data(self.persistence_path)
                
                if persistence_data:
                    current_time = time.time()
                    
                    # 恢复数据
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
                        item.size = item_data.get("size", 0)
                        
                        self._storage[item_id] = item
                    
                    self._update_memory_stats()
                    logger.debug(f"Loaded {len(self._storage)} items from persistence file")
                
        except Exception as e:
            logger.error(f"Failed to load persistence data: {e}")
    
    async def _create_backup_impl(self) -> None:
        """创建备份的具体实现
        
        对于内存存储，备份是指保存持久化数据。
        """
        if not self.persistence_path:
            logger.warning("Persistence path not configured, skipping backup")
            return
        
        try:
            await self._save_persistence()
            logger.info(f"Created memory storage backup at {self.persistence_path}")
        except Exception as e:
            raise StorageError(f"Failed to create memory storage backup: {e}")