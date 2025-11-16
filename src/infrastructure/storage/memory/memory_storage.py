"""
内存存储实现

提供基于内存的存储后端实现，支持线程安全、TTL、压缩等功能。
"""

import asyncio
import time
import uuid
import gzip
import pickle
import json
from typing import Dict, Any, Optional, List, AsyncIterator, Union
from datetime import datetime, timedelta
import threading
import weakref
import gc
import os
import logging

from ....domain.storage.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageValidationError,
    StorageNotFoundError,
    StorageTimeoutError,
    StorageCapacityError
)
from ..interfaces import IStorageBackend
from .memory_config import MemoryStorageConfig


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


class MemoryStorage(IStorageBackend):
    """内存存储实现
    
    提供基于内存的存储后端，支持线程安全、TTL、压缩等功能。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化内存存储
        
        Args:
            **config: 配置参数
        """
        # 解析配置
        self.config = MemoryStorageConfig(**config)
        
        # 存储数据
        self._storage: Dict[str, MemoryStorageItem] = {}
        
        # 线程锁
        self._lock = asyncio.Lock()
        self._thread_lock = threading.RLock()
        
        # 连接状态
        self._connected = False
        
        # 统计信息
        self._stats = {
            "total_operations": 0,
            "save_operations": 0,
            "load_operations": 0,
            "update_operations": 0,
            "delete_operations": 0,
            "list_operations": 0,
            "query_operations": 0,
            "transaction_operations": 0,
            "expired_items_cleaned": 0,
            "memory_usage_bytes": 0,
            "compression_ratio": 0.0
        }
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._persistence_task: Optional[asyncio.Task] = None
        
        # 持久化相关
        self._persistence_lock = threading.Lock()
        self._last_persistence_time = 0
        
        logger.info("MemoryStorage initialized")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 加载持久化数据
            if self.config.enable_persistence:
                await self._load_persistence()
            
            # 启动清理任务
            if self.config.enable_ttl:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_items())
            
            # 启动持久化任务
            if self.config.enable_persistence:
                self._persistence_task = asyncio.create_task(self._persistence_worker())
            
            self._connected = True
            logger.info("MemoryStorage connected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect MemoryStorage: {e}")
    
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
            if self.config.enable_persistence:
                await self._save_persistence()
            
            # 清理数据
            with self._thread_lock:
                self._storage.clear()
            
            self._connected = False
            logger.info("MemoryStorage disconnected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect MemoryStorage: {e}")
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    async def save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        try:
            # 检查容量限制
            await self._check_capacity()
            
            # 生成ID（如果没有）
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            item_id: str = data["id"]
            
            # 压缩数据（如果需要）
            compressed = False
            processed_data: Union[Dict[str, Any], bytes] = data
            if (self.config.enable_compression and 
                len(str(data)) > self.config.compression_threshold):
                processed_data = await self._compress_data(data)
                compressed = True
            
            # 创建存储项
            ttl_seconds = self.config.default_ttl_seconds if self.config.enable_ttl else None
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
                    data = await self._decompress_data(data)
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
                                current_data = await self._decompress_data(current_data)
                            else:
                                # 如果不是 bytes 类型，说明数据有问题，记录错误并返回 False
                                logger.error(f"Expected compressed data to be bytes, got {type(current_data)}")
                                return False
                        
                        # 确保 current_data 是 Dict[str, Any] 类型
                        if isinstance(current_data, dict):
                            current_data.update(updates)
                            
                            # 压缩数据（如果需要）
                            processed_data: Union[Dict[str, Any], bytes] = current_data
                            if (self.config.enable_compression and 
                                len(str(current_data)) > self.config.compression_threshold):
                                processed_data = await self._compress_data(current_data)
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
                                data = await self._decompress_data(data)
                            else:
                                # 如果不是 bytes 类型，说明数据有问题，跳过此项
                                logger.error(f"Expected compressed data to be bytes, got {type(data)}")
                                continue
                        
                        # 确保 data 是 Dict[str, Any] 类型
                        if isinstance(data, dict) and self._matches_filters(data, filters):
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
                                data = await self._decompress_data(data)
                            else:
                                # 如果不是 bytes 类型，说明数据有问题，跳过此项
                                logger.error(f"Expected compressed data to be bytes, got {type(data)}")
                                continue
                        
                        # 确保 data 是 Dict[str, Any] 类型
                        if isinstance(data, dict) and self._matches_filters(data, filters):
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
                    await self._check_capacity()
                    
                    # 生成ID（如果没有）
                    if "id" not in data:
                        data["id"] = str(uuid.uuid4())
                    
                    item_id = data["id"]
                    
                    # 压缩数据（如果需要）
                    compressed = False
                    processed_data: Union[Dict[str, Any], bytes] = data
                    if (self.config.enable_compression and 
                        len(str(data)) > self.config.compression_threshold):
                        processed_data = await self._compress_data(data)
                        compressed = True
                    
                    # 创建存储项
                    ttl_seconds = self.config.default_ttl_seconds if self.config.enable_ttl else None
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
    
    async def get_by_session_impl(self, session_id: str) -> List[Dict[str, Any]]:
        """实际根据会话ID获取数据实现"""
        filters = {"session_id": session_id}
        return await self.list_impl(filters)
    
    async def get_by_thread_impl(self, thread_id: str) -> List[Dict[str, Any]]:
        """实际根据线程ID获取数据实现"""
        filters = {"thread_id": thread_id}
        return await self.list_impl(filters)
    
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
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """实际流式列表实现"""
        async def _stream() -> AsyncIterator[List[Dict[str, Any]]]:
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
                                    data = await self._decompress_data(data)
                                else:
                                    # 如果不是 bytes 类型，说明数据有问题，跳过此项
                                    logger.error(f"Expected compressed data to be bytes, got {type(data)}")
                                    continue
                            
                            # 确保 data 是 Dict[str, Any] 类型
                            if isinstance(data, dict) and self._matches_filters(data, filters):
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
                total_size = sum(item.size for item in self._storage.values())
                
                # 计算压缩比
                compressed_items = sum(1 for item in self._storage.values() if item.compressed)
                compression_ratio = compressed_items / len(self._storage) if self._storage else 0
                
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
                "config": self.config.to_dict()
            }
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
    
    async def _check_capacity(self) -> None:
        """检查容量限制"""
        with self._thread_lock:
            # 检查条目数量限制
            if self.config.max_size and len(self._storage) >= self.config.max_size:
                raise StorageCapacityError(
                    f"Storage capacity exceeded: max_size={self.config.max_size}",
                    required_size=1,
                    available_size=self.config.max_size - len(self._storage)
                )
            
            # 检查内存使用限制
            if self.config.max_memory_mb:
                total_size = sum(item.size for item in self._storage.values())
                max_bytes = self.config.max_memory_mb * 1024 * 1024
                if total_size >= max_bytes:
                    raise StorageCapacityError(
                        f"Memory capacity exceeded: max_memory_mb={self.config.max_memory_mb}",
                        required_size=1024,  # 估算1KB
                        available_size=max_bytes - total_size
                    )
    
    async def _compress_data(self, data: Dict[str, Any]) -> bytes:
        """压缩数据"""
        try:
            # 序列化为JSON
            json_str = json.dumps(data, default=str)
            # 压缩
            return gzip.compress(json_str.encode('utf-8'))
        except Exception as e:
            raise StorageError(f"Failed to compress data: {e}")
    
    async def _decompress_data(self, compressed_data: bytes) -> Dict[str, Any]:
        """解压缩数据"""
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
    
    def _matches_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器"""
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
    
    def _update_stats(self, operation: str) -> None:
        """更新统计信息"""
        self._stats["total_operations"] += 1
        if f"{operation}_operations" in self._stats:
            self._stats[f"{operation}_operations"] += 1
    
    async def _cleanup_expired_items(self) -> None:
        """清理过期项（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                
                async with self._lock:
                    await self._cleanup_expired_items_sync()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _cleanup_expired_items_sync(self) -> None:
        """同步清理过期项"""
        items_to_delete = []
        
        for item_id, item in self._storage.items():
            if item.is_expired():
                items_to_delete.append(item_id)
        
        for item_id in items_to_delete:
            del self._storage[item_id]
            self._stats["expired_items_cleaned"] += 1
        
        if items_to_delete:
            logger.debug(f"Cleaned up {len(items_to_delete)} expired items")
    
    async def _persistence_worker(self) -> None:
        """持久化工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.config.persistence_interval_seconds)
                
                current_time = time.time()
                if current_time - self._last_persistence_time >= self.config.persistence_interval_seconds:
                    await self._save_persistence()
                    self._last_persistence_time = int(current_time)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in persistence task: {e}")
    
    async def _save_persistence(self) -> None:
        """保存持久化数据"""
        if not self.config.persistence_path:
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
                        "size": item.size
                    }
                
                # 确保目录存在
                os.makedirs(os.path.dirname(self.config.persistence_path), exist_ok=True)
                
                # 保存到文件
                with open(self.config.persistence_path, 'wb') as f:
                    pickle.dump(persistence_data, f)
                
                logger.debug(f"Saved {len(persistence_data)} items to persistence file")
                
        except Exception as e:
            logger.error(f"Failed to save persistence data: {e}")
    
    async def _load_persistence(self) -> None:
        """加载持久化数据"""
        if not self.config.persistence_path or not os.path.exists(self.config.persistence_path):
            return
        
        try:
            with self._persistence_lock:
                # 从文件加载
                with open(self.config.persistence_path, 'rb') as f:
                    persistence_data = pickle.load(f)
                
                # 恢复数据
                for item_id, item_data in persistence_data.items():
                    # 检查是否过期
                    if item_data.get("expires_at") and time.time() > item_data["expires_at"]:
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
                    
                    self._storage[item_id] = item
                
                logger.debug(f"Loaded {len(self._storage)} items from persistence file")
                
        except Exception as e:
            logger.error(f"Failed to load persistence data: {e}")