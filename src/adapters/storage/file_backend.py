"""文件存储后端

提供基于文件的存储后端实现，支持持久化、压缩、目录组织等功能。
"""

import asyncio
import os
import shutil
import threading
import time
import logging
import uuid
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.core.state.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageCapacityError
)
from .base_optimized import EnhancedStorageBackend
from .utils.file_utils import FileStorageUtils


logger = logging.getLogger(__name__)


class FileStorageBackend(EnhancedStorageBackend):
    """文件存储后端实现
    
    提供基于文件的存储后端，支持持久化、压缩、目录组织等功能。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化文件存储
        
        Args:
            **config: 配置参数
        """
        super().__init__(**config)
        
        # 解析配置
        self.base_path = config.get("base_path", "file_storage")
        self.enable_compression = config.get("enable_compression", False)
        self.compression_threshold = config.get("compression_threshold", 1024)
        self.enable_ttl = config.get("enable_ttl", False)
        self.default_ttl_seconds = config.get("default_ttl_seconds", 3600)
        self.cleanup_interval_seconds = config.get("cleanup_interval_seconds", 300)
        self.enable_backup = config.get("enable_backup", False)
        self.backup_interval_hours = config.get("backup_interval_hours", 24)
        self.backup_path = config.get("backup_path", "file_storage_backups")
        self.max_backup_files = config.get("max_backup_files", 7)
        self.directory_structure = config.get("directory_structure", "flat")  # flat, by_type, by_date, by_agent
        self.file_extension = config.get("file_extension", "json")
        self.enable_metadata = config.get("enable_metadata", True)
        self.max_directory_size = config.get("max_directory_size")  # 最大目录大小（字节）
        self.max_files_per_directory = config.get("max_files_per_directory", 1000)
        
        # 线程锁
        self._lock = asyncio.Lock()
        self._thread_lock = threading.RLock()
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._backup_task: Optional[asyncio.Task] = None
        
        # 持久化相关
        self._last_backup_time = 0
        
        # 扩展统计信息
        self._stats.update({
            "total_files": 0,
            "total_size_bytes": 0,
            "expired_files_cleaned": 0,
            "backup_count": 0,
            "last_backup_time": 0,
            "compression_ratio": 0.0
        })
        
        logger.info(f"FileStorageBackend initialized with base_path: {self.base_path}")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 确保基础目录存在
            FileStorageUtils.ensure_directory_exists(self.base_path)
            
            # 启动清理任务
            if self.enable_ttl:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_files())
            
            # 启动备份任务
            if self.enable_backup:
                self._backup_task = asyncio.create_task(self._backup_worker())
            
            self._connected = True
            logger.info("FileStorageBackend connected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect FileStorageBackend: {e}")
    
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
            logger.info("FileStorageBackend disconnected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect FileStorageBackend: {e}")
    
    def _get_file_path(self, item_id: str, data: Optional[Dict[str, Any]] = None) -> str:
        """获取文件路径
        
        Args:
            item_id: 项目ID
            data: 数据（可选，用于确定目录结构）
            
        Returns:
            文件路径
        """
        if self.directory_structure == "flat":
            # 平铺结构
            return os.path.join(self.base_path, f"{item_id}.{self.file_extension}")
        
        elif self.directory_structure == "by_type":
            # 按类型组织
            data_type = data.get("type", "unknown") if data else "unknown"
            type_dir = os.path.join(self.base_path, data_type)
            return os.path.join(type_dir, f"{item_id}.{self.file_extension}")
        
        elif self.directory_structure == "by_date":
            # 按日期组织
            current_time = time.time()
            date_str = time.strftime("%Y-%m-%d", time.localtime(current_time))
            date_dir = os.path.join(self.base_path, date_str)
            return os.path.join(date_dir, f"{item_id}.{self.file_extension}")
        
        elif self.directory_structure == "by_agent":
            # 按代理组织
            agent_id = data.get("agent_id", "unknown") if data else "unknown"
            agent_dir = os.path.join(self.base_path, agent_id)
            return os.path.join(agent_dir, f"{item_id}.{self.file_extension}")
        
        else:
            # 默认平铺结构
            return os.path.join(self.base_path, f"{item_id}.{self.file_extension}")
    
    async def save_impl(self, data: Union[Dict[str, Any], bytes], compressed: bool = False) -> str:
        """实际保存实现"""
        try:
            # 检查容量限制
            if self.max_directory_size or self.max_files_per_directory:
                await self._check_capacity_limits()
            
            # 生成ID（如果没有）
            if isinstance(data, dict) and "id" not in data:
                data = data.copy()  # 避免修改原始数据
                data["id"] = str(uuid.uuid4())
            
            item_id: str = data["id"] if isinstance(data, dict) else str(uuid.uuid4())
            current_time = time.time()
            
            # 处理数据 - 如果传入的是bytes且标记为压缩，则先解压为字典
            if isinstance(data, bytes) and compressed:
                import gzip
                import json
                try:
                    decompressed_data = gzip.decompress(data)
                    str_data = decompressed_data.decode('utf-8')
                    data = json.loads(str_data)
                except Exception as e:
                    raise StorageError(f"Failed to decompress and deserialize data: {e}")
            elif isinstance(data, bytes) and not compressed:
                raise StorageError(f"Unexpected bytes data type without compression flag")
            
            # 添加元数据
            if self.enable_metadata and isinstance(data, dict):
                data["created_at"] = data.get("created_at", current_time)
                data["updated_at"] = current_time
                
                if self.enable_ttl and "expires_at" not in data:
                    data["expires_at"] = current_time + self.default_ttl_seconds
            
            # 压缩数据（如果需要）
            actual_compressed = False
            processed_data: Union[Dict[str, Any], bytes] = data
            if isinstance(data, dict) and (compressed or (self.enable_compression and
                FileStorageUtils.should_compress_data(data, self.compression_threshold))):
                processed_data = FileStorageUtils.compress_data(data)
                actual_compressed = True
            else:
                actual_compressed = compressed
            
            # 获取文件路径
            file_path = self._get_file_path(item_id, data if isinstance(data, dict) else None)
            
            # 保存数据
            async with self._lock:
                with self._thread_lock:
                    if actual_compressed:
                        # 保存压缩数据
                        with open(file_path, 'wb') as f:
                            if isinstance(processed_data, bytes):
                                f.write(processed_data)
                            else:
                                raise StorageError(f"Expected bytes for compressed data, got {type(processed_data)}")
                    else:
                        # 保存普通数据
                        if isinstance(processed_data, dict):
                            FileStorageUtils.save_data_to_file(file_path, processed_data)
                        else:
                            raise StorageError(f"Expected dict for uncompressed data, got {type(processed_data)}")
                    
                    self._update_stats("save")
            
            return item_id
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
    
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        try:
            # 获取可能的文件路径
            file_paths = await self._get_possible_file_paths(id)
            
            async with self._lock:
                with self._thread_lock:
                    for file_path in file_paths:
                        if not FileStorageUtils.file_exists(file_path):
                            continue
                        
                        # 检查是否过期
                        if self.enable_ttl:
                            data = FileStorageUtils.load_data_from_file(file_path)
                            if data and "expires_at" in data and data["expires_at"] < time.time():
                                FileStorageUtils.delete_file(file_path)
                                self._stats["expired_files_cleaned"] += 1
                                continue
                        
                        # 加载数据
                        try:
                            # 尝试作为压缩文件加载
                            with open(file_path, 'rb') as f:
                                compressed_data = f.read()
                            
                            # 检查是否是压缩数据
                            try:
                                data = FileStorageUtils.decompress_data(compressed_data)
                            except:
                                # 如果解压失败，尝试作为普通文件加载
                                data = FileStorageUtils.load_data_from_file(file_path)
                            
                            self._update_stats("load")
                            return data
                            
                        except Exception as e:
                            logger.error(f"Failed to load data from file {file_path}: {e}")
                            continue
            
            return None
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
    
    async def _get_possible_file_paths(self, id: str) -> List[str]:
        """获取可能的文件路径列表
        
        Args:
            id: 项目ID
            
        Returns:
            可能的文件路径列表
        """
        file_paths = []
        
        if self.directory_structure == "flat":
            file_paths.append(os.path.join(self.base_path, f"{id}.{self.file_extension}"))
        
        else:
            # 对于其他目录结构，需要搜索所有可能的目录
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file == f"{id}.{self.file_extension}":
                        file_paths.append(os.path.join(root, file))
        
        return file_paths
    
    async def update_impl(self, id: str, updates: Dict[str, Any]) -> bool:
        """实际更新实现"""
        try:
            # 加载现有数据
            current_data = await self.load_impl(id)
            if current_data is None:
                return False
            
            # 更新数据
            current_data.update(updates)
            current_data["updated_at"] = time.time()
            
            # 保存更新后的数据
            result = await self.save_impl(current_data)
            
            self._update_stats("update")
            return bool(result)
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update data {id}: {e}")
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        try:
            # 获取可能的文件路径
            file_paths = await self._get_possible_file_paths(id)
            
            async with self._lock:
                with self._thread_lock:
                    for file_path in file_paths:
                        if FileStorageUtils.delete_file(file_path):
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
            results: List[Dict[str, Any]] = []
            
            async with self._lock:
                with self._thread_lock:
                    # 获取所有文件
                    all_files = FileStorageUtils.list_files_in_directory(
                        self.base_path, 
                        f"*.{self.file_extension}", 
                        recursive=True
                    )
                    
                    # 按修改时间排序（最新的在前）
                    all_files.sort(key=lambda f: FileStorageUtils.get_file_modified_time(f), reverse=True)
                    
                    # 处理文件
                    for file_path in all_files:
                        # 检查限制
                        if limit and len(results) >= limit:
                            break
                        
                        # 加载数据
                        data = FileStorageUtils.load_data_from_file(file_path)
                        if data is None:
                            continue
                        
                        # 检查是否过期
                        if self.enable_ttl and "expires_at" in data and data["expires_at"] < time.time():
                            FileStorageUtils.delete_file(file_path)
                            self._stats["expired_files_cleaned"] += 1
                            continue
                        
                        # 检查过滤器
                        if FileStorageUtils.matches_filters(data, filters):
                            results.append(data)
            
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
            
            # 文件路径查询
            elif query.startswith("path:"):
                path_pattern = query[5:]  # 移除 "path:" 前缀
                matching_files = FileStorageUtils.list_files_in_directory(
                    self.base_path, 
                    path_pattern, 
                    recursive=True
                )
                
                results = []
                for file_path in matching_files:
                    data = FileStorageUtils.load_data_from_file(file_path)
                    if data:
                        results.append(data)
                
                return results
            
            # 其他查询类型暂不支持
            else:
                raise StorageError(f"Unsupported query type: {query}")
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to execute query: {e}")
    
    async def exists_impl(self, id: str) -> bool:
        """实际存在检查实现"""
        try:
            # 获取可能的文件路径
            file_paths = await self._get_possible_file_paths(id)
            
            for file_path in file_paths:
                if not FileStorageUtils.file_exists(file_path):
                    continue
                
                # 检查是否过期
                if self.enable_ttl:
                    data = FileStorageUtils.load_data_from_file(file_path)
                    if data and "expires_at" in data and data["expires_at"] < time.time():
                        FileStorageUtils.delete_file(file_path)
                        self._stats["expired_files_cleaned"] += 1
                        continue
                
                return True
            
            return False
            
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
                    # 获取所有文件
                    all_files = FileStorageUtils.list_files_in_directory(
                        self.base_path, 
                        f"*.{self.file_extension}", 
                        recursive=True
                    )
                    
                    # 处理文件
                    for file_path in all_files:
                        # 加载数据
                        data = FileStorageUtils.load_data_from_file(file_path)
                        if data is None:
                            continue
                        
                        # 检查是否过期
                        if self.enable_ttl and "expires_at" in data and data["expires_at"] < time.time():
                            FileStorageUtils.delete_file(file_path)
                            self._stats["expired_files_cleaned"] += 1
                            continue
                        
                        # 检查过滤器
                        if FileStorageUtils.matches_filters(data, filters):
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
                    if self.max_directory_size or self.max_files_per_directory:
                        await self._check_capacity_limits()
                    
                    # 生成ID（如果没有）
                    if "id" not in data:
                        data["id"] = str(uuid.uuid4())
                    
                    item_id = data["id"]
                    current_time = time.time()
                    
                    # 添加元数据
                    if self.enable_metadata:
                        data["created_at"] = data.get("created_at", current_time)
                        data["updated_at"] = current_time
                        
                        if self.enable_ttl and "expires_at" not in data:
                            data["expires_at"] = current_time + self.default_ttl_seconds
                    
                    # 压缩数据（如果需要）
                    compressed = False
                    processed_data: Union[Dict[str, Any], bytes] = data
                    if (self.enable_compression and 
                        FileStorageUtils.should_compress_data(data, self.compression_threshold)):
                        processed_data = FileStorageUtils.compress_data(data)
                        compressed = True
                    
                    # 获取文件路径
                    file_path = self._get_file_path(item_id, data)
                    
                    # 保存数据
                    with self._thread_lock:
                        if compressed:
                            # 保存压缩数据
                            with open(file_path, 'wb') as f:
                                if isinstance(processed_data, bytes):
                                    f.write(processed_data)
                                else:
                                    raise StorageError(f"Expected bytes for compressed data, got {type(processed_data)}")
                        else:
                            # 保存普通数据
                            if isinstance(processed_data, dict):
                                FileStorageUtils.save_data_to_file(file_path, processed_data)
                            else:
                                raise StorageError(f"Expected dict for uncompressed data, got {type(processed_data)}")
                    
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
                        # 获取可能的文件路径
                        file_paths = await self._get_possible_file_paths(id)
                        
                        for file_path in file_paths:
                            if FileStorageUtils.delete_file(file_path):
                                count += 1
                                break
                
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
            
            async with self._lock:
                with self._thread_lock:
                    cleaned_count = FileStorageUtils.cleanup_old_files(self.base_path, cutoff_time)
            
            return cleaned_count
            
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
                # 获取所有文件
                all_files = FileStorageUtils.list_files_in_directory(
                    self.base_path, 
                    f"*.{self.file_extension}", 
                    recursive=True
                )
                
                # 按修改时间排序（最新的在前）
                all_files.sort(key=lambda f: FileStorageUtils.get_file_modified_time(f), reverse=True)
                
                # 分批处理
                batch = []
                
                async with self._lock:
                    with self._thread_lock:
                        for file_path in all_files:
                            # 加载数据
                            data = FileStorageUtils.load_data_from_file(file_path)
                            if data is None:
                                continue
                            
                            # 检查是否过期
                            if self.enable_ttl and "expires_at" in data and data["expires_at"] < time.time():
                                FileStorageUtils.delete_file(file_path)
                                self._stats["expired_files_cleaned"] += 1
                                continue
                            
                            # 检查过滤器
                            if FileStorageUtils.matches_filters(data, filters):
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
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    async def get_by_session_impl(self, session_id: str) -> List[Dict[str, Any]]:
        """实际根据会话ID获取数据实现"""
        filters = {"session_id": session_id}
        return await self.list_impl(filters)

    async def get_by_thread_impl(self, thread_id: str) -> List[Dict[str, Any]]:
        """实际根据线程ID获取数据实现"""
        filters = {"thread_id": thread_id}
        return await self.list_impl(filters)

    async def begin_transaction(self) -> None:
        """开始事务"""
        # 默认实现：简单标记事务开始
        pass

    async def commit_transaction(self) -> None:
        """提交事务"""
        # 默认实现：简单标记事务提交
        pass

    async def rollback_transaction(self) -> None:
        """回滚事务"""
        # 默认实现：简单标记事务回滚
        pass

    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        try:
            # 获取存储信息
            storage_info = FileStorageUtils.get_storage_info(self.base_path)
            
            # 更新统计信息
            self._stats["total_files"] = storage_info["total_files"]
            self._stats["total_size_bytes"] = storage_info["total_size_bytes"]
            
            # 清理过期文件
            if self.enable_ttl:
                expired_count = FileStorageUtils.cleanup_expired_files(self.base_path, time.time())
                self._stats["expired_files_cleaned"] += expired_count
            
            # 计算压缩比
            compression_ratio = 0.0
            if self.enable_compression:
                # 简化的压缩比计算
                compression_ratio = 0.3  # 假设平均压缩比为30%
            
            self._stats["compression_ratio"] = compression_ratio
            
            return {
                "status": "healthy",
                "base_path": self.base_path,
                "directory_exists": storage_info["directory_exists"],
                "total_files": self._stats["total_files"],
                "total_size_bytes": self._stats["total_size_bytes"],
                "total_size_mb": storage_info["total_size_mb"],
                "expired_files_cleaned": self._stats["expired_files_cleaned"],
                "backup_count": self._stats["backup_count"],
                "last_backup_time": self._stats["last_backup_time"],
                "compression_ratio": self._stats["compression_ratio"],
                "total_operations": self._stats["total_operations"],
                "config": {
                    "enable_compression": self.enable_compression,
                    "compression_threshold": self.compression_threshold,
                    "enable_ttl": self.enable_ttl,
                    "directory_structure": self.directory_structure,
                    "enable_backup": self.enable_backup,
                    "backup_interval_hours": self.backup_interval_hours
                }
            }
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
    
    async def _check_capacity_limits(self) -> None:
        """检查容量限制"""
        try:
            # 检查目录大小限制
            if self.max_directory_size:
                current_size = FileStorageUtils.calculate_directory_size(self.base_path)
                if current_size > self.max_directory_size:
                    raise StorageCapacityError(
                        f"Directory size limit exceeded: {current_size} > {self.max_directory_size}"
                    )
            
            # 检查文件数量限制
            if self.max_files_per_directory:
                current_files = len(FileStorageUtils.list_files_in_directory(
                    self.base_path, 
                    f"*.{self.file_extension}", 
                    recursive=True
                ))
                if current_files > self.max_files_per_directory:
                    raise StorageCapacityError(
                        f"File count limit exceeded: {current_files} > {self.max_files_per_directory}"
                    )
                    
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to check capacity limits: {e}")
    
    async def _cleanup_expired_files(self) -> None:
        """清理过期文件（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                
                async with self._lock:
                    with self._thread_lock:
                        expired_count = FileStorageUtils.cleanup_expired_files(self.base_path, time.time())
                        self._stats["expired_files_cleaned"] += expired_count
                
                if expired_count > 0:
                    logger.debug(f"Cleaned up {expired_count} expired files")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
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
        """创建备份"""
        try:
            # 确保备份目录存在
            backup_dir = Path(self.backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成备份目录名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            current_backup_dir = backup_dir / f"storage_backup_{timestamp}"
            
            # 创建备份
            success = FileStorageUtils.backup_directory(self.base_path, str(current_backup_dir))
            
            if success:
                # 更新统计信息
                self._stats["backup_count"] += 1
                self._stats["last_backup_time"] = time.time()
                
                logger.info(f"Created backup: {current_backup_dir}")
                
                # 清理旧备份
                await self._cleanup_old_backups()
            else:
                logger.error("Failed to create backup")
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    async def _cleanup_old_backups(self) -> None:
        """清理旧备份"""
        try:
            backup_dir = Path(self.backup_path)
            if not backup_dir.exists():
                return
            
            # 获取所有备份目录
            backup_dirs = list(backup_dir.glob("storage_backup_*"))
            
            # 按修改时间排序
            backup_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
            
            # 删除超出限制的备份目录
            if len(backup_dirs) > self.max_backup_files:
                for backup_dir in backup_dirs[self.max_backup_files:]:
                    shutil.rmtree(backup_dir)
                    logger.debug(f"Deleted old backup: {backup_dir}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")