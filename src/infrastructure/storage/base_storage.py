"""
基础存储实现

提供统一存储的基础实现，集成序列化、时间管理、元数据管理、
缓存组件和性能监控支持。
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime, timedelta

from ...domain.storage.interfaces import IUnifiedStorage
from ...domain.storage.models import StorageData, StorageHealth, StorageStatistics
from ...domain.storage.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageValidationError,
    StorageNotFoundError,
    StorageTimeoutError
)
from .interfaces import IStorageBackend, IStorageSerializer, IStorageCache, IStorageMetrics


class BaseStorage(IUnifiedStorage):
    """基础存储实现
    
    提供统一存储的基础功能，包括：
    - 序列化支持
    - 时间管理
    - 元数据管理
    - 缓存支持
    - 性能监控
    - 事务支持
    """
    
    def __init__(
        self,
        backend: IStorageBackend,
        serializer: Optional[IStorageSerializer] = None,
        cache: Optional[IStorageCache] = None,
        metrics: Optional[IStorageMetrics] = None,
        cache_ttl: int = 300,  # 5分钟
        enable_metrics: bool = True,
        timeout: float = 30.0
    ):
        """初始化基础存储
        
        Args:
            backend: 存储后端
            serializer: 序列化器
            cache: 缓存
            metrics: 指标收集器
            cache_ttl: 缓存TTL（秒）
            enable_metrics: 是否启用指标收集
            timeout: 操作超时时间（秒）
        """
        self._backend = backend
        self._serializer = serializer
        self._cache = cache
        self._metrics = metrics
        self._cache_ttl = cache_ttl
        self._enable_metrics = enable_metrics and metrics is not None
        self._timeout = timeout
        self._lock = asyncio.Lock()
        
        # 连接状态
        self._connected = False
        self._last_health_check = None
        self._health_status = None
    
    async def _ensure_connected(self) -> None:
        """确保已连接到存储后端"""
        if not await self._backend.is_connected():
            await self._backend.connect()
            self._connected = True
    
    async def _record_metrics(
        self, 
        operation: str, 
        duration: float, 
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作指标"""
        if self._enable_metrics and self._metrics:
            await self._metrics.record_operation(operation, duration, success, metadata)
    
    async def _get_cache_key(self, id: str) -> str:
        """获取缓存键"""
        return f"storage:{id}"
    
    async def _get_from_cache(self, id: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        if self._cache:
            cache_key = await self._get_cache_key(id)
            return await self._cache.get(cache_key)
        return None
    
    async def _set_cache(self, id: str, data: Dict[str, Any]) -> None:
        """设置缓存"""
        if self._cache:
            cache_key = await self._get_cache_key(id)
            await self._cache.set(cache_key, data, self._cache_ttl)
    
    async def _delete_cache(self, id: str) -> None:
        """删除缓存"""
        if self._cache:
            cache_key = await self._get_cache_key(id)
            await self._cache.delete(cache_key)
    
    async def _validate_data(self, data: Dict[str, Any]) -> None:
        """验证数据格式"""
        if not isinstance(data, dict):
            raise StorageValidationError("Data must be a dictionary")
        
        required_fields = ["id", "type", "data"]
        for field in required_fields:
            if field not in data:
                raise StorageValidationError(f"Missing required field: {field}")
        
        if not isinstance(data["id"], str) or not data["id"]:
            raise StorageValidationError("Field 'id' must be a non-empty string")
        
        if not isinstance(data["type"], str) or not data["type"]:
            raise StorageValidationError("Field 'type' must be a non-empty string")
        
        if not isinstance(data["data"], dict):
            raise StorageValidationError("Field 'data' must be a dictionary")
    
    async def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备数据，添加时间戳和元数据"""
        now = datetime.now()
        
        # 确保有创建时间和更新时间
        if "created_at" not in data:
            data["created_at"] = now
        data["updated_at"] = now
        
        # 确保有元数据
        if "metadata" not in data:
            data["metadata"] = {}
        
        # 添加版本信息
        data["metadata"]["version"] = data["metadata"].get("version", 1)
        
        return data
    
    async def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """序列化数据"""
        if self._serializer:
            # 序列化data字段
            if "data" in data:
                serialized = self._serializer.serialize(data["data"])
                data["data_serialized"] = serialized
                data["data"] = {"_serialized": True}
        return data
    
    async def _deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """反序列化数据"""
        if self._serializer and "data_serialized" in data:
            # 反序列化data字段
            data["data"] = self._serializer.deserialize(data["data_serialized"])
            del data["data_serialized"]
        return data
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据并返回ID"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 验证数据
            await self._validate_data(data)
            
            # 准备数据
            data = await self._prepare_data(data.copy())
            
            # 序列化数据
            data = await self._serialize_data(data)
            
            # 保存到后端
            id = await self._backend.save_impl(data)
            
            # 设置缓存
            await self._set_cache(id, data)
            
            success = True
            return id
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("save", duration, success)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID加载数据"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 先从缓存获取
            cached_data = await self._get_from_cache(id)
            if cached_data:
                return await self._deserialize_data(cached_data.copy())
            
            # 从后端加载
            data = await self._backend.load_impl(id)
            if data is None:
                return None
            
            # 反序列化数据
            data = await self._deserialize_data(data)
            
            # 设置缓存
            await self._set_cache(id, data)
            
            success = True
            return data
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("load", duration, success)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 检查数据是否存在
            existing = await self.load(id)
            if existing is None:
                raise StorageNotFoundError(f"Data not found: {id}")
            
            # 合并更新
            existing.update(updates)
            existing["updated_at"] = datetime.now()
            
            # 验证更新后的数据
            await self._validate_data(existing)
            
            # 序列化数据
            data_to_save = await self._serialize_data(existing.copy())
            
            # 更新后端
            result = await self._backend.update_impl(id, data_to_save)
            
            if result:
                # 更新缓存
                await self._set_cache(id, existing)
            
            success = True
            return result
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update data {id}: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("update", duration, success)
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 删除后端数据
            result = await self._backend.delete_impl(id)
            
            if result:
                # 删除缓存
                await self._delete_cache(id)
            
            success = True
            return result
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("delete", duration, success)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 从后端获取数据
            results = await self._backend.list_impl(filters, limit)
            
            # 反序列化数据
            deserialized_results = []
            for result in results:
                deserialized = await self._deserialize_data(result.copy())
                deserialized_results.append(deserialized)
            
            success = True
            return deserialized_results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("list", duration, success)
    
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 执行查询
            results = await self._backend.query_impl(query, params)
            
            # 反序列化数据
            deserialized_results = []
            for result in results:
                deserialized = await self._deserialize_data(result.copy())
                deserialized_results.append(deserialized)
            
            success = True
            return deserialized_results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to execute query: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("query", duration, success)
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 先检查缓存
            if self._cache:
                cache_key = await self._get_cache_key(id)
                if await self._cache.exists(cache_key):
                    return True
            
            # 检查后端
            result = await self._backend.exists_impl(id)
            
            success = True
            return result
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to check existence of data {id}: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("exists", duration, success)
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 执行计数
            result = await self._backend.count_impl(filters)
            
            success = True
            return result
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to count data: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("count", duration, success)
    
    async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 验证操作
            for op in operations:
                if "type" not in op:
                    raise StorageValidationError("Operation missing 'type' field")
                
                op_type = op["type"]
                if op_type == "save" and "data" not in op:
                    raise StorageValidationError("Save operation missing 'data' field")
                elif op_type == "update" and ("id" not in op or "data" not in op):
                    raise StorageValidationError("Update operation missing 'id' or 'data' field")
                elif op_type == "delete" and "id" not in op:
                    raise StorageValidationError("Delete operation missing 'id' field")
            
            # 执行事务
            result = await self._backend.transaction_impl(operations)
            
            # 清理相关缓存
            if result and self._cache:
                for op in operations:
                    if op["type"] in ["save", "update", "delete"]:
                        id = op.get("id") or op.get("data", {}).get("id")
                        if id:
                            await self._delete_cache(id)
            
            success = True
            return result
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to execute transaction: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("transaction", duration, success)
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 验证和准备数据
            prepared_data = []
            for data in data_list:
                await self._validate_data(data)
                prepared = await self._prepare_data(data.copy())
                prepared = await self._serialize_data(prepared)
                prepared_data.append(prepared)
            
            # 批量保存
            ids = await self._backend.batch_save_impl(prepared_data)
            
            # 设置缓存
            for i, id in enumerate(ids):
                await self._set_cache(id, prepared_data[i])
            
            success = True
            return ids
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch save data: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("batch_save", duration, success)
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 批量删除
            count = await self._backend.batch_delete_impl(ids)
            
            # 删除缓存
            if self._cache:
                for id in ids:
                    await self._delete_cache(id)
            
            success = True
            return count
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch delete data: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("batch_delete", duration, success)
    
    async def get_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取数据"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 获取数据
            results = await self._backend.get_by_session_impl(session_id)
            
            # 反序列化数据
            deserialized_results = []
            for result in results:
                deserialized = await self._deserialize_data(result.copy())
                deserialized_results.append(deserialized)
            
            success = True
            return deserialized_results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to get data by session {session_id}: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("get_by_session", duration, success)
    
    async def get_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """根据线程ID获取数据"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 获取数据
            results = await self._backend.get_by_thread_impl(thread_id)
            
            # 反序列化数据
            deserialized_results = []
            for result in results:
                deserialized = await self._deserialize_data(result.copy())
                deserialized_results.append(deserialized)
            
            success = True
            return deserialized_results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to get data by thread {thread_id}: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("get_by_thread", duration, success)
    
    async def cleanup_old_data(self, retention_days: int) -> int:
        """清理旧数据"""
        start_time = time.time()
        success = False
        
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 清理数据
            count = await self._backend.cleanup_old_data_impl(retention_days)
            
            # 清空缓存（简化处理）
            if self._cache and count > 0:
                await self._cache.clear()
            
            success = True
            return count
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
        finally:
            duration = time.time() - start_time
            await self._record_metrics("cleanup_old_data", duration, success)
    
    def stream_list(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列出数据"""
        async def _stream():
            try:
                # 确保连接
                await self._ensure_connected()
                
                # 流式获取数据
                async for batch in self._backend.stream_list_impl(filters, batch_size):
                    # 反序列化数据
                    deserialized_batch = []
                    for result in batch:
                        deserialized = await self._deserialize_data(result.copy())
                        deserialized_batch.append(deserialized)
                    
                    yield deserialized_batch
                    
            except Exception as e:
                if isinstance(e, StorageError):
                    raise
                raise StorageError(f"Failed to stream list data: {e}")
        
        return _stream()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        start_time = time.time()
        
        try:
            # 检查连接
            await self._ensure_connected()
            
            # 执行后端健康检查
            health_info = await self._backend.health_check_impl()
            
            # 添加基础存储信息
            health_info.update({
                "storage_type": self.__class__.__name__,
                "cache_enabled": self._cache is not None,
                "metrics_enabled": self._enable_metrics,
                "response_time": (time.time() - start_time) * 1000,  # 毫秒
                "timestamp": datetime.now().isoformat()
            })
            
            self._health_status = health_info
            self._last_health_check = datetime.now()
            
            return health_info
            
        except Exception as e:
            error_info = {
                "status": "unhealthy",
                "error": str(e),
                "storage_type": self.__class__.__name__,
                "response_time": (time.time() - start_time) * 1000,
                "timestamp": datetime.now().isoformat()
            }
            
            self._health_status = error_info
            self._last_health_check = datetime.now()
            
            raise StorageConnectionError(f"Health check failed: {e}")
    
    async def get_statistics(self) -> StorageStatistics:
        """获取存储统计信息"""
        try:
            # 确保连接
            await self._ensure_connected()
            
            # 获取基础统计
            total_count = await self.count({})
            
            # 获取类型分布
            type_counts = {}
            for data_type in ["session", "thread", "message", "checkpoint"]:
                count = await self.count({"type": data_type})
                if count > 0:
                    type_counts[data_type] = count
            
            # 获取时间范围
            all_data = await self.list({}, limit=1000)
            oldest = None
            newest = None
            total_size = 0
            
            for item in all_data:
                created_at = item.get("created_at")
                if created_at:
                    if oldest is None or created_at < oldest:
                        oldest = created_at
                    if newest is None or created_at > newest:
                        newest = created_at
                
                # 估算大小
                total_size += len(str(item))
            
            return StorageStatistics(
                total_count=total_count,
                total_size=total_size,
                type_distribution=type_counts,
                oldest_record=oldest,
                newest_record=newest
            )
            
        except Exception as e:
            raise StorageError(f"Failed to get statistics: {e}")
    
    async def close(self) -> None:
        """关闭存储连接"""
        try:
            if await self._backend.is_connected():
                await self._backend.disconnect()
            self._connected = False
        except Exception as e:
            raise StorageError(f"Failed to close storage: {e}")