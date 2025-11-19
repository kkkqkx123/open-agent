"""内存存储后端

提供基于内存的存储后端实现，支持线程安全、TTL、压缩等功能。
"""

import asyncio
import time
import uuid
import threading
import logging
from typing import Dict, Any, Optional, List, Union

from src.core.state.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageCapacityError
)
from .base import BaseStorageBackend
from .utils.memory_utils import MemoryStorageUtils


logger = logging.getLogger(__name__)


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


class MemoryStorageBackend(BaseStorageBackend):
    """内存存储后端实现
    
    提供基于内存的存储后端，支持线程安全、TTL、压缩等功能。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化内存存储
        
        Args:
            **config: 配置参数
        """
        super().__init__(**config)
        
        # 解析配置
        self.max_size = config.get("max_size")
        self.max_memory_mb = config.get("max_memory_mb")
        self.enable_ttl = config.get("enable_ttl", False)
        self.default_ttl_seconds = config.get("default_ttl_seconds", 3600)
        self.cleanup_interval_seconds = config.get("cleanup_interval_seconds", 300)
        self.enable_compression = config.get("enable_compression", False)
        self.compression_threshold = config.get("compression_threshold", 1024)
        self.enable_metrics = config.get("enable_metrics", True)
        self.enable_persistence = config.get("enable_persistence", False)
        self.persistence_path = config.get("persistence_path")
        self.persistence_interval_seconds = config.get("persistence_interval_seconds", 600)
        
        # 存储数据
        self._storage: Dict[str, MemoryStorageItem] = {}
        
        # 线程锁
        self._lock = asyncio.Lock()
        self._thread_lock = threading.RLock()
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._persistence_task: Optional[asyncio.Task] = None
        
        # 持久化相关
        self._persistence_lock = threading.Lock()
        self._last_persistence_time = 0
        
        # 扩展统计信息
        self._stats["expired_items_cleaned"] = 0
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
            
            # 启动清理任务
            if self.enable_ttl:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_items())
            
            # 启动持久化任务
            if self.enable_persistence:
                self._persistence_task = asyncio.create_task(self._persistence_worker())
            
            self._connected = True
            logger.info("MemoryStorageBackend connected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect MemoryStorageBackend: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 停止清理任务
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
                self._cleanup_task = None
            
            # 停止持久化任务
            if self._persistence_task:
                self._persistence_task.cancel()
                try:
                    await self._persistence_task
                except asyncio.CancelledError:
                    pass
                self._persistence_task = None
            
            # 保存持久化数据
            if self.enable_persistence:
                await self._save_persistence()
            
            # 清理数据
            with self._thread_lock:
                self._storage.clear()
            
            self._connected = False
            logger.info("MemoryStorageBackend disconnected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect MemoryStorageBackend: {e}")
    
    async def save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        try:
            # 检查容量限制
            MemoryStorageUtils.validate_capacity(self._storage, self.max_size, self.max_memory_mb)
            
            # 生成ID（如果没有）
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            item_id: str = data["id"]
            
            # 压缩数据（如果需要）
            compressed = False
            processed_data: Union[Dict[str, Any], bytes] = data
            if (self.enable_compression and 
                MemoryStorageUtils.should_compress_data(data, self.compression_threshold)):
                processed_data = MemoryStorageUtils.compress_data(data)
                compressed = True
            
            # 创建存储项
            ttl_seconds = self.default_ttl_seconds if self.enable_ttl else None
            item = MemoryStorageItem(processed_data, ttl_seconds, compressed)
            
            # 保存数据
            async with self._lock:
                with self._thread_lock:
                    self._storage[item_id] = item
                    self._update_stats("save")
            
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
                        return None
                    
                    # 访问数据
                    data = item.access()
                    self._update_stats("load")
            
            # 解压缩数据（如果需要）
            if item.compressed:
                # 确保传入的是 bytes 类型
                if isinstance(data, bytes):
                    data = MemoryStorageUtils.decompress_data(data)
                else:
                    # 如果不是 bytes 类型，说明数据有问题，记录错误并返回 None
                    logger.error(f"Expected compressed data to be bytes, got {type(data)}")
                    return None
            
            # 确保返回的是 Dict[str, Any] 类型
            if isinstance(data, dict):
                return data
            else:
                logger.error(f"Expected data to be dict, got {type(data)}")
                return None
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
    
    async def update_impl(self, id: str, updates: Dict[str, Any]) -> bool:
        """实际更新实现"""
        try:
            async with self._lock:
                with self._thread_lock:
                    item = self._storage.get(id)
                    if item is None:
                        return False
                    
                    # 检查是否过期
                    if item.is_expired():
                        del self._storage[id]
                        self._stats["expired_items_cleaned"] += 1
                        return False
                    
                    # 更新数据
                    if isinstance(updates, dict):
                        # 合并更新
                        current_data = item.access()
                        if item.compressed:
                            # 确保传入的是 bytes 类型
                            if isinstance(current_data, bytes):
                                current_data = MemoryStorageUtils.decompress_data(current_data)
                            else:
                                # 如果不是 bytes 类型，说明数据有问题，记录错误并返回 False
                                logger.error(f"Expected compressed data to be bytes, got {type(current_data)}")
                                return False
                        
                        # 确保 current_data 是 Dict[str, Any] 类型
                        if isinstance(current_data, dict):
                            current_data.update(updates)
                            
                            # 压缩数据（如果需要）
                            processed_data: Union[Dict[str, Any], bytes] = current_data
                            if (self.enable_compression and 
                                MemoryStorageUtils.should_compress_data(current_data, self.compression_threshold)):
                                processed_data = MemoryStorageUtils.compress_data(current_data)
                                item.compressed = True
                            else:
                                item.compressed = False
                            
                            item.update_data(processed_data)
                        else:
                            logger.error(f"Expected current_data to be dict, got {type(current_data)}")
                            return False
                    else:
                        # 直接替换
                        item.update_data(updates)
                    
                    self._update_stats("update")
            
            return True
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update data {id}: {e}")
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        try:
            async with self._lock:
                with self._thread_lock:
                    if id in self._storage:
                        del self._storage[id]
                        self._update_stats("delete")
                        return True
                    return False
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
    
    async def list_impl(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """实际列表实现"""
        try:
            results = []
            
            async with self._lock:
                with self._thread_lock:
                    # 清理过期项
                    await self._cleanup_expired_items_sync()
                    
                    # 应用过滤器
                    for item_id, item in self._storage.items():
                        # 检查是否过期
                        if item.is_expired():
                            del self._storage[item_id]
                            self._stats["expired_items_cleaned"] += 1
                            continue
                        
                        # 获取数据
                        data = item.access()
                        if item.compressed:
                            # 确保传入的是 bytes 类型
                            if isinstance(data, bytes):
                                data = MemoryStorageUtils.decompress_data(data)
                            else:
                                # 如果不是 bytes 类型，说明数据有问题，跳过此项
                                logger.error(f"Expected compressed data to be bytes, got {type(data)}")
                                continue
                        
                        # 确保 data 是 Dict[str, Any] 类型
                        if isinstance(data, dict) and MemoryStorageUtils.matches_filters(data, filters):
                            results.append(data)
                            
                            # 检查限制
                            if limit and len(results) >= limit:
                                break
                    
                    self._update_stats("list")
            
            return results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
    
    async def query_impl(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """实际查询实现"""
        try:
            # 简单的查询实现（基于过滤器）
            if query.startswith("filters:"):
                filters_str = query[8:]  # 移除 "filters:" 前缀
                import json
                filters = json.loads(filters_str) if filters_str else {}
                return await self.list_impl(filters, params.get("limit"))
            
            # 其他查询类型暂不支持
            raise StorageError(f"Unsupported query type: {query}")
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to execute query: {e}")
    
    async def exists_impl(self, id: str) -> bool:
        """实际存在检查实现"""
        try:
            async with self._lock:
                with self._thread_lock:
                    item = self._storage.get(id)
                    if item is None:
                        return False
                    
                    # 检查是否过期
                    if item.is_expired():
                        del self._storage[id]
                        self._stats["expired_items_cleaned"] += 1
                        return False
                    
                    return True
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to check existence of data {id}: {e}")
    
    async def count_impl(self, filters: Dict[str, Any]) -> int:
        """实际计数实现"""
        try:
            count = 0
            
            async with self._lock:
                with self._thread_lock:
                    # 清理过期项
                    await self._cleanup_expired_items_sync()
                    
                    # 应用过滤器计数
                    for item_id, item in self._storage.items():
                        # 检查是否过期
                        if item.is_expired():
                            del self._storage[item_id]
                            self._stats["expired_items_cleaned"] += 1
                            continue
                        
                        # 获取数据
                        data = item.access()
                        if item.compressed:
                            # 确保传入的是 bytes 类型
                            if isinstance(data, bytes):
                                data = MemoryStorageUtils.decompress_data(data)
                            else:
                                # 如果不是 bytes 类型，说明数据有问题，跳过此项
                                logger.error(f"Expected compressed data to be bytes, got {type(data)}")
                                continue
                        
                        # 确保 data 是 Dict[str, Any] 类型
                        if isinstance(data, dict) and MemoryStorageUtils.matches_filters(data, filters):
                            count += 1
            
            return count
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to count data: {e}")
    
    async def transaction_impl(self, operations: List[Dict[str, Any]]) -> bool:
        """实际事务实现"""
        try:
            # 简单的事务实现（按顺序执行）
            async with self._lock:
                for operation in operations:
                    op_type = operation.get("type")
                    
                    if op_type == "save":
                        await self.save_impl(operation["data"])
                    elif op_type == "update":
                        await self.update_impl(operation["id"], operation["data"])
                    elif op_type == "delete":
                        await self.delete_impl(operation["id"])
                    else:
                        raise StorageTransactionError(f"Unknown operation type: {op_type}")
                
                self._update_stats("transaction")
            
            return True
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageTransactionError(f"Transaction failed: {e}")
    
    async def batch_save_impl(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """实际批量保存实现"""
        try:
            ids = []
            
            async with self._lock:
                for data in data_list:
                    # 检查容量限制
                    MemoryStorageUtils.validate_capacity(self._storage, self.max_size, self.max_memory_mb)
                    
                    # 生成ID（如果没有）
                    if "id" not in data:
                        data["id"] = str(uuid.uuid4())
                    
                    item_id = data["id"]
                    
                    # 压缩数据（如果需要）
                    compressed = False
                    processed_data: Union[Dict[str, Any], bytes] = data
                    if (self.enable_compression and 
                        MemoryStorageUtils.should_compress_data(data, self.compression_threshold)):
                        processed_data = MemoryStorageUtils.compress_data(data)
                        compressed = True
                    
                    # 创建存储项
                    ttl_seconds = self.default_ttl_seconds if self.enable_ttl else None
                    item = MemoryStorageItem(processed_data, ttl_seconds, compressed)
                    
                    # 保存数据
                    with self._thread_lock:
                        self._storage[item_id] = item
                    
                    ids.append(item_id)
                
                self._update_stats("save")
            
            return ids
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch save data: {e}")
    
    async def batch_delete_impl(self, ids: List[str]) -> int:
        """实际批量删除实现"""
        try:
            count = 0
            
            async with self._lock:
                with self._thread_lock:
                    for id in ids:
                        if id in self._storage:
                            del self._storage[id]
                            count += 1
                
                self._update_stats("delete")
            
            return count
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch delete data: {e}")
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        try:
            cutoff_time = time.time() - (retention_days * 24 * 3600)
            count = 0
            
            async with self._lock:
                with self._thread_lock:
                    items_to_delete = []
                    
                    for item_id, item in self._storage.items():
                        if item.created_at < cutoff_time:
                            items_to_delete.append(item_id)
                    
                    for item_id in items_to_delete:
                        del self._storage[item_id]
                        count += 1
            
            return count
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
    
    def stream_list_impl(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> Any:
        """实际流式列表实现"""
        async def _stream() -> Any:
            try:
                batch = []
                
                async with self._lock:
                    with self._thread_lock:
                        # 清理过期项
                        await self._cleanup_expired_items_sync()
                        
                        # 应用过滤器
                        for item_id, item in self._storage.items():
                            # 检查是否过期
                            if item.is_expired():
                                del self._storage[item_id]
                                self._stats["expired_items_cleaned"] += 1
                                continue
                            
                            # 获取数据
                            data = item.access()
                            if item.compressed:
                                # 确保传入的是 bytes 类型
                                if isinstance(data, bytes):
                                    data = MemoryStorageUtils.decompress_data(data)
                                else:
                                    # 如果不是 bytes 类型，说明数据有问题，跳过此项
                                    logger.error(f"Expected compressed data to be bytes, got {type(data)}")
                                    continue
                            
                            # 确保 data 是 Dict[str, Any] 类型
                            if isinstance(data, dict) and MemoryStorageUtils.matches_filters(data, filters):
                                batch.append(data)
                                
                                # 检查批次大小
                                if len(batch) >= batch_size:
                                    yield batch
                                    batch = []
                        
                        # 返回最后一批
                        if batch:
                            yield batch
                
            except Exception as e:
                if isinstance(e, StorageError):
                    raise
                raise StorageError(f"Failed to stream list data: {e}")
        
        return _stream()
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        try:
            with self._thread_lock:
                # 计算内存使用量
                total_size = MemoryStorageUtils.calculate_memory_usage(self._storage)
                
                # 计算压缩比
                compression_ratio = MemoryStorageUtils.calculate_compression_ratio(self._storage)
                
                # 更新统计信息
                self._stats["memory_usage_bytes"] = total_size
                self._stats["compression_ratio"] = compression_ratio
            
            return {
                "status": "healthy",
                "item_count": len(self._storage),
                "memory_usage_bytes": self._stats["memory_usage_bytes"],
                "compression_ratio": self._stats["compression_ratio"],
                "total_operations": self._stats["total_operations"],
                "expired_items_cleaned": self._stats["expired_items_cleaned"],
                "config": {
                    "max_size": self.max_size,
                    "max_memory_mb": self.max_memory_mb,
                    "enable_ttl": self.enable_ttl,
                    "enable_compression": self.enable_compression,
                    "enable_persistence": self.enable_persistence
                }
            }
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
    
    async def _cleanup_expired_items(self) -> None:
        """清理过期项（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                
                async with self._lock:
                    await self._cleanup_expired_items_sync()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _cleanup_expired_items_sync(self) -> None:
        """同步清理过期项"""
        expired_items = MemoryStorageUtils.get_expired_items(self._storage)
        
        with self._thread_lock:
            for item_id in expired_items:
                del self._storage[item_id]
                self._stats["expired_items_cleaned"] += 1
        
        if expired_items:
            logger.debug(f"Cleaned up {len(expired_items)} expired items")
    
    async def _persistence_worker(self) -> None:
        """持久化工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.persistence_interval_seconds)
                
                current_time = time.time()
                if current_time - self._last_persistence_time >= self.persistence_interval_seconds:
                    await self._save_persistence()
                    self._last_persistence_time = int(current_time)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in persistence task: {e}")
    
    async def _save_persistence(self) -> None:
        """保存持久化数据"""
        if not self.persistence_path:
            return
        
        try:
            with self._persistence_lock:
                # 准备持久化数据
                persistence_data = MemoryStorageUtils.prepare_persistence_data(self._storage)
                
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
                    # 恢复数据
                    self._storage = MemoryStorageUtils.restore_persistence_data(persistence_data)
                    
                    logger.debug(f"Loaded {len(self._storage)} items from persistence file")
                
        except Exception as e:
            logger.error(f"Failed to load persistence data: {e}")