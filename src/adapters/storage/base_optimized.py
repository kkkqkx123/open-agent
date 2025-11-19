"""优化的存储基类

提供增强的存储基类实现，减少重复代码。
"""

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

from src.core.state.interfaces import IStorageBackend
from src.core.state.exceptions import StorageError, StorageConnectionError
from .utils.common_utils import StorageCommonUtils


logger = logging.getLogger(__name__)


class EnhancedStorageBackend(IStorageBackend, ABC):
    """增强的存储后端基类
    
    提供通用的存储后端功能，减少具体实现类的重复代码。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化增强存储后端
        
        Args:
            **config: 配置参数
        """
        self._connected = False
        self._config = config
        self._stats: Dict[str, Any] = {
            "total_operations": 0,
            "save_operations": 0,
            "load_operations": 0,
            "update_operations": 0,
            "delete_operations": 0,
            "list_operations": 0,
            "query_operations": 0,
            "transaction_operations": 0,
            "expired_items_cleaned": 0,
            "backup_count": 0,
            "last_backup_time": 0,
        }
        
        # 通用配置
        self.enable_compression = config.get("enable_compression", False)
        self.compression_threshold = config.get("compression_threshold", 1024)
        self.enable_ttl = config.get("enable_ttl", False)
        self.default_ttl_seconds = config.get("default_ttl_seconds", 3600)
        self.cleanup_interval_seconds = config.get("cleanup_interval_seconds", 300)
        self.enable_backup = config.get("enable_backup", False)
        self.backup_interval_hours = config.get("backup_interval_hours", 24)
        self.backup_path = config.get("backup_path", "backups")
        self.max_backup_files = config.get("max_backup_files", 7)
        
        # 线程安全
        self._lock = asyncio.Lock()
        self._thread_lock = threading.RLock()
        
        # 异步任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._backup_task: Optional[asyncio.Task] = None
        self._last_backup_time = 0
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 启动清理任务
            if self.enable_ttl:
                self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            
            # 启动备份任务
            if self.enable_backup:
                self._backup_task = asyncio.create_task(self._backup_worker())
            
            self._connected = True
            logger.info(f"{self.__class__.__name__} connected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect {self.__class__.__name__}: {e}")
    
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
            
            # 停止备份任务
            if self._backup_task:
                self._backup_task.cancel()
                try:
                    await self._backup_task
                except asyncio.CancelledError:
                    pass
                self._backup_task = None
            
            self._connected = False
            logger.info(f"{self.__class__.__name__} disconnected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect {self.__class__.__name__}: {e}")
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        try:
            # 验证并生成ID
            item_id = StorageCommonUtils.validate_data_id(data)
            
            # 添加元数据时间戳
            StorageCommonUtils.add_metadata_timestamps(
                data, self.enable_ttl, self.default_ttl_seconds
            )
            
            # 压缩数据（如果需要）
            processed_data = data
            compressed = False
            if (self.enable_compression and 
                StorageCommonUtils.should_compress_data(data, self.compression_threshold)):
                processed_data = StorageCommonUtils.compress_data(data)
                compressed = True
            
            # 保存数据
            result_id = await self.save_impl(processed_data, compressed)
            
            self._update_stats("save")
            return result_id
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        try:
            # 加载数据
            data = await self.load_impl(id)
            
            if data is None:
                return None
            
            # 检查是否过期
            if self.enable_ttl and StorageCommonUtils.is_data_expired(data):
                await self.delete(id)
                self._stats["expired_items_cleaned"] += 1
                return None
            
            self._update_stats("load")
            return data
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        try:
            # 加载现有数据
            current_data = await self.load(id)
            if current_data is None:
                return False
            
            # 更新数据
            current_data.update(updates)
            current_data["updated_at"] = time.time()
            
            # 保存更新后的数据
            result = await self.save(current_data)
            
            return result == id
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update data {id}: {e}")
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        try:
            result = await self.delete_impl(id)
            if result:
                self._update_stats("delete")
            return result
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        try:
            # 清理过期项
            if self.enable_ttl:
                await self._cleanup_expired_items()
            
            # 获取数据列表
            results = await self.list_impl(filters, limit)
            
            # 过滤过期数据
            if self.enable_ttl:
                filtered_results = []
                for data in results:
                    if not StorageCommonUtils.is_data_expired(data):
                        filtered_results.append(data)
                    else:
                        self._stats["expired_items_cleaned"] += 1
                results = filtered_results
            
            self._update_stats("list")
            return results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数数据"""
        try:
            results = await self.list(filters)
            return len(results)
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to count data: {e}")
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        try:
            data = await self.load(id)
            return data is not None
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to check existence of data {id}: {e}")
    
    async def cleanup_old_data(self, retention_days: int) -> int:
        """清理旧数据"""
        try:
            return await self.cleanup_old_data_impl(retention_days)
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 清理过期项
            if self.enable_ttl:
                await self._cleanup_expired_items()
            
            # 获取健康检查信息
            health_info = await self.health_check_impl()
            
            # 添加通用信息
            health_info["total_operations"] = self._stats["total_operations"]
            health_info["expired_items_cleaned"] = self._stats["expired_items_cleaned"]
            health_info["backup_count"] = self._stats["backup_count"]
            health_info["last_backup_time"] = self._stats["last_backup_time"]
            
            # 添加配置信息
            health_info["config"] = {
                "enable_compression": self.enable_compression,
                "compression_threshold": self.compression_threshold,
                "enable_ttl": self.enable_ttl,
                "default_ttl_seconds": self.default_ttl_seconds,
                "enable_backup": self.enable_backup,
                "backup_interval_hours": self.backup_interval_hours,
                "max_backup_files": self.max_backup_files,
            }
            
            return health_info
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
    
    # 抽象方法 - 必须由子类实现
    @abstractmethod
    async def save_impl(self, data: Union[Dict[str, Any], bytes], compressed: bool = False) -> str:
        """实际保存实现"""
        pass
    
    @abstractmethod
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        pass
    
    @abstractmethod
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        pass
    
    @abstractmethod
    async def list_impl(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """实际列表实现"""
        pass
    
    @abstractmethod
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        pass
    
    # 可选实现的方法
    async def update_impl(self, id: str, updates: Dict[str, Any]) -> bool:
        """实际更新实现 - 默认使用保存实现"""
        # 默认实现：加载-更新-保存
        data = await self.load_impl(id)
        if data is None:
            return False
        
        data.update(updates)
        data["updated_at"] = time.time()
        
        await self.save_impl(data)
        return True
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现 - 默认实现"""
        # 默认实现：列出所有数据并删除旧数据
        cutoff_time = StorageCommonUtils.calculate_cutoff_time(retention_days)
        all_data = await self.list_impl({})
        count = 0
        
        for data in all_data:
            created_at = data.get("created_at", 0)
            if created_at < cutoff_time:
                if await self.delete_impl(data["id"]):
                    count += 1
        
        return count
    
    # 内部辅助方法
    def _update_stats(self, operation: str) -> None:
        """更新统计信息"""
        self._stats["total_operations"] += 1
        if f"{operation}_operations" in self._stats:
            self._stats[f"{operation}_operations"] += 1
    
    async def _cleanup_worker(self) -> None:
        """清理工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                await self._cleanup_expired_items()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _cleanup_expired_items(self) -> None:
        """清理过期项"""
        # 默认实现：通过列表接口清理
        try:
            all_data = await self.list_impl({})
            for data in all_data:
                if StorageCommonUtils.is_data_expired(data):
                    await self.delete_impl(data["id"])
                    self._stats["expired_items_cleaned"] += 1
        except Exception as e:
            logger.error(f"Error cleaning up expired items: {e}")
    
    async def _backup_worker(self) -> None:
        """备份工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.backup_interval_hours * 3600)
                
                current_time = time.time()
                if current_time - self._last_backup_time >= self.backup_interval_hours * 3600:
                    await self._create_backup()
                    self._last_backup_time = int(current_time)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in backup task: {e}")
    
    async def _create_backup(self) -> None:
        """创建备份 - 默认实现"""
        # 默认实现：确保备份目录存在并更新时间
        try:
            StorageCommonUtils.ensure_directory_exists(self.backup_path)
            self._stats["backup_count"] += 1
            self._stats["last_backup_time"] = time.time()
            logger.info(f"Backup marker updated for {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to create backup marker: {e}")


class ConnectionPoolMixin:
    """连接池混入类
    
    提供通用的连接池管理功能。
    """
    
    def __init__(self, pool_size: int = 5):
        self._connection_pool: List[Any] = []
        self._pool_lock = threading.Lock()
        self._pool_semaphore = threading.Semaphore(pool_size)
        self._pool_size = pool_size
        self._active_connections = 0
    
    def _get_connection(self) -> Any:
        """从连接池获取连接"""
        self._pool_semaphore.acquire()
        
        with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
                self._active_connections += 1
                return conn
            else:
                self._pool_semaphore.release()
                raise StorageConnectionError("No available connections in pool")
    
    def _return_connection(self, conn: Any) -> None:
        """归还连接到连接池"""
        try:
            with self._pool_lock:
                if len(self._connection_pool) < self._pool_size:
                    self._connection_pool.append(conn)
                    self._active_connections -= 1
                else:
                    # 如果池已满，关闭连接
                    if hasattr(conn, 'close'):
                        conn.close()
            
            self._pool_semaphore.release()
            
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
    
    def _close_connection_pool(self) -> None:
        """关闭连接池"""
        try:
            with self._pool_lock:
                for conn in self._connection_pool:
                    if hasattr(conn, 'close'):
                        conn.close()
                
                self._connection_pool.clear()
                self._active_connections = 0
                
        except Exception as e:
            logger.error(f"Failed to close connection pool: {e}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        return {
            "pool_size": self._pool_size,
            "active_connections": self._active_connections,
            "available_connections": len(self._connection_pool),
        }


class TaskManagerMixin:
    """任务管理混入类
    
    提供通用的异步任务管理功能。
    """
    
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._task_lock = asyncio.Lock()
    
    async def _start_task(self, task_name: str, task_func: Any, *args: Any, **kwargs: Any) -> None:
        """启动任务"""
        async with self._task_lock:
            if task_name in self._tasks and not self._tasks[task_name].done():
                return  # 任务已在运行
            
            self._tasks[task_name] = asyncio.create_task(task_func(*args, **kwargs))
    
    async def _stop_task(self, task_name: str) -> None:
        """停止任务"""
        async with self._task_lock:
            if task_name in self._tasks:
                task = self._tasks[task_name]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self._tasks[task_name]
    
    async def _stop_all_tasks(self) -> None:
        """停止所有任务"""
        async with self._task_lock:
            for task_name in list(self._tasks.keys()):
                await self._stop_task(task_name)
    
    def get_task_status(self) -> Dict[str, str]:
        """获取任务状态"""
        status = {}
        for task_name, task in self._tasks.items():
            if task.done():
                status[task_name] = "completed"
            else:
                status[task_name] = "running"
        return status