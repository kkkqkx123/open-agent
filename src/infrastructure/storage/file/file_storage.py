"""
文件存储实现

提供基于文件系统的存储后端实现，支持数据持久化和文件管理。
"""

import asyncio
import time
import uuid
import json
import pickle
import yaml
import os
import shutil
import threading
import fcntl
import gzip
import bz2
import lzma
import hashlib
import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from pathlib import Path

from ...domain.storage.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageValidationError,
    StorageNotFoundError,
    StorageTimeoutError,
    StorageCapacityError
)
from ..interfaces import IStorageBackend
from .file_config import FileStorageConfig


logger = logging.getLogger(__name__)


class FileStorage(IStorageBackend):
    """文件存储实现
    
    提供基于文件系统的存储后端，支持数据持久化和文件管理。
    """
    
    def __init__(self, **config):
        """初始化文件存储
        
        Args:
            **config: 配置参数
        """
        # 解析配置
        self.config = FileStorageConfig(**config)
        
        # 连接状态
        self._connected = False
        
        # 线程锁
        self._lock = asyncio.Lock()
        self._file_locks = {}  # 文件锁字典
        self._lock_lock = threading.Lock()  # 保护文件锁字典的锁
        
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
            "file_errors": 0,
            "lock_timeouts": 0,
            "total_file_size": 0,
            "file_count": 0
        }
        
        # 索引缓存
        self._index_cache = {}
        self._index_cache_lock = threading.Lock()
        
        # 后台任务
        self._cleanup_task = None
        
        logger.info(f"FileStorage initialized with base path: {self.config.base_path}")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 创建基础目录
            if self.config.auto_create_directories:
                os.makedirs(self.config.base_path, exist_ok=True)
            
            # 验证基础路径
            if not os.path.exists(self.config.base_path):
                raise StorageConnectionError(f"Base path does not exist: {self.config.base_path}")
            
            if not os.path.isdir(self.config.base_path):
                raise StorageConnectionError(f"Base path is not a directory: {self.config.base_path}")
            
            # 检查写权限
            test_file = os.path.join(self.config.base_path, ".test_write")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                raise StorageConnectionError(f"No write permission to base path: {e}")
            
            # 加载索引
            await self._load_index()
            
            # 启动清理任务
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            
            self._connected = True
            logger.info("FileStorage connected")
            
        except Exception as e:
            self._stats["file_errors"] += 1
            raise StorageConnectionError(f"Failed to connect FileStorage: {e}")
    
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
            
            # 保存索引
            await self._save_index()
            
            # 清理文件锁
            with self._lock_lock:
                self._file_locks.clear()
            
            self._connected = False
            logger.info("FileStorage disconnected")
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to disconnect FileStorage: {e}")
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    async def save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        start_time = time.time()
        
        try:
            # 生成ID（如果没有）
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            item_id = data["id"]
            
            # 获取文件路径
            data_type = data.get("type")
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = self.config.get_file_path(item_id, data_type, date_str)
            directory = os.path.dirname(file_path)
            
            # 创建目录
            if self.config.auto_create_directories:
                os.makedirs(directory, exist_ok=True)
            
            # 检查文件大小限制
            if self.config.max_file_size_mb:
                serialized_data = json.dumps(data, default=str)
                if len(serialized_data.encode('utf-8')) > self.config.max_file_size_mb * 1024 * 1024:
                    raise StorageCapacityError(
                        f"File size exceeds limit: {self.config.max_file_size_mb}MB"
                    )
            
            # 获取文件锁
            async with self._get_file_lock(file_path):
                # 创建备份
                if self.config.enable_backup and os.path.exists(file_path):
                    await self._create_backup(file_path)
                
                # 序列化数据
                serialized_data = await self._serialize_data(data)
                
                # 压缩数据（如果需要）
                if self.config.enable_compression:
                    serialized_data = await self._compress_data(serialized_data)
                
                # 加密数据（如果需要）
                if self.config.enable_encryption:
                    serialized_data = await self._encrypt_data(serialized_data)
                
                # 写入文件
                await self._write_file(file_path, serialized_data)
                
                # 更新索引
                if self.config.enable_indexing:
                    await self._update_index(item_id, file_path, data)
                
                # 更新元数据
                if self.config.enable_metadata_file:
                    await self._update_metadata(directory, item_id, data)
            
            self._update_stats("save", time.time() - start_time)
            return item_id
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to save data: {e}")
    
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        start_time = time.time()
        
        try:
            # 从索引查找文件路径
            file_path = await self._find_file_path(id)
            if file_path is None:
                return None
            
            # 获取文件锁
            async with self._get_file_lock(file_path):
                # 读取文件
                serialized_data = await self._read_file(file_path)
                if serialized_data is None:
                    return None
                
                # 解密数据（如果需要）
                if self.config.enable_encryption:
                    serialized_data = await self._decrypt_data(serialized_data)
                
                # 解压缩数据（如果需要）
                if self.config.enable_compression:
                    serialized_data = await self._decompress_data(serialized_data)
                
                # 反序列化数据
                data = await self._deserialize_data(serialized_data)
            
            self._update_stats("load", time.time() - start_time)
            return data
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to load data {id}: {e}")
    
    async def update_impl(self, id: str, updates: Dict[str, Any]) -> bool:
        """实际更新实现"""
        start_time = time.time()
        
        try:
            # 加载现有数据
            existing = await self.load_impl(id)
            if existing is None:
                return False
            
            # 合并更新
            existing.update(updates)
            existing["updated_at"] = datetime.now().isoformat()
            
            # 保存更新后的数据
            await self.save_impl(existing)
            
            self._update_stats("update", time.time() - start_time)
            return True
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update data {id}: {e}")
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        start_time = time.time()
        
        try:
            # 从索引查找文件路径
            file_path = await self._find_file_path(id)
            if file_path is None:
                return False
            
            # 获取文件锁
            async with self._get_file_lock(file_path):
                # 删除文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # 删除备份文件
                if self.config.enable_backup:
                    await self._delete_backups(file_path)
                
                # 更新索引
                if self.config.enable_indexing:
                    await self._remove_from_index(id)
                
                # 更新元数据
                if self.config.enable_metadata_file:
                    directory = os.path.dirname(file_path)
                    await self._remove_from_metadata(directory, id)
            
            self._update_stats("delete", time.time() - start_time)
            return True
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete data {id}: {e}")
    
    async def list_impl(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """实际列表实现"""
        start_time = time.time()
        
        try:
            results = []
            
            # 遍历索引
            if self.config.enable_indexing:
                # 使用索引快速查找
                for item_id, item_info in self._index_cache.items():
                    if self._matches_filters(item_info.get("data", {}), filters):
                        data = await self.load_impl(item_id)
                        if data:
                            results.append(data)
                            if limit and len(results) >= limit:
                                break
            else:
                # 扫描文件系统
                for root, dirs, files in os.walk(self.config.base_path):
                    for file in files:
                        # 跳过元数据和索引文件
                        if (file.startswith(self.config.metadata_file_name) or 
                            file.startswith(self.config.index_file_name)):
                            continue
                        
                        file_path = os.path.join(root, file)
                        
                        # 读取文件
                        try:
                            data = await self._load_file_direct(file_path)
                            if data and self._matches_filters(data, filters):
                                results.append(data)
                                if limit and len(results) >= limit:
                                    break
                        except Exception as e:
                            logger.warning(f"Failed to load file {file_path}: {e}")
                    
                    if limit and len(results) >= limit:
                        break
            
            self._update_stats("list", time.time() - start_time)
            return results
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
    
    async def query_impl(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """实际查询实现"""
        start_time = time.time()
        
        try:
            # 简单的查询实现（基于过滤器）
            if query.startswith("filters:"):
                filters_str = query[8:]  # 移除 "filters:" 前缀
                filters = json.loads(filters_str) if filters_str else {}
                return await self.list_impl(filters, params.get("limit"))
            
            # 其他查询类型暂不支持
            raise StorageError(f"Unsupported query type: {query}")
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to execute query: {e}")
    
    async def exists_impl(self, id: str) -> bool:
        """实际存在检查实现"""
        try:
            file_path = await self._find_file_path(id)
            return file_path is not None and os.path.exists(file_path)
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to check existence of data {id}: {e}")
    
    async def count_impl(self, filters: Dict[str, Any]) -> int:
        """实际计数实现"""
        try:
            # 使用列表实现并计数
            results = await self.list_impl(filters)
            return len(results)
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to count data: {e}")
    
    async def transaction_impl(self, operations: List[Dict[str, Any]]) -> bool:
        """实际事务实现"""
        start_time = time.time()
        
        try:
            # 简单的事务实现（按顺序执行）
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
            
            self._update_stats("transaction", time.time() - start_time)
            return True
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageTransactionError(f"Transaction failed: {e}")
    
    async def batch_save_impl(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """实际批量保存实现"""
        try:
            ids = []
            
            for data in data_list:
                item_id = await self.save_impl(data)
                ids.append(item_id)
            
            return ids
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to batch save data: {e}")
    
    async def batch_delete_impl(self, ids: List[str]) -> int:
        """实际批量删除实现"""
        try:
            count = 0
            
            for id in ids:
                if await self.delete_impl(id):
                    count += 1
            
            return count
            
        except Exception as e:
            self._stats["file_errors"] += 1
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
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            count = 0
            
            # 遍历文件系统
            for root, dirs, files in os.walk(self.config.base_path):
                for file in files:
                    # 跳过元数据和索引文件
                    if (file.startswith(self.config.metadata_file_name) or 
                        file.startswith(self.config.index_file_name)):
                        continue
                    
                    file_path = os.path.join(root, file)
                    
                    # 检查文件修改时间
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_date:
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete old file {file_path}: {e}")
            
            return count
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
    
    async def stream_list_impl(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """实际流式列表实现"""
        try:
            batch = []
            
            # 遍历索引
            if self.config.enable_indexing:
                # 使用索引快速查找
                for item_id, item_info in self._index_cache.items():
                    if self._matches_filters(item_info.get("data", {}), filters):
                        data = await self.load_impl(item_id)
                        if data:
                            batch.append(data)
                            
                            # 检查批次大小
                            if len(batch) >= batch_size:
                                yield batch
                                batch = []
            else:
                # 扫描文件系统
                for root, dirs, files in os.walk(self.config.base_path):
                    for file in files:
                        # 跳过元数据和索引文件
                        if (file.startswith(self.config.metadata_file_name) or 
                            file.startswith(self.config.index_file_name)):
                            continue
                        
                        file_path = os.path.join(root, file)
                        
                        # 读取文件
                        try:
                            data = await self._load_file_direct(file_path)
                            if data and self._matches_filters(data, filters):
                                batch.append(data)
                                
                                # 检查批次大小
                                if len(batch) >= batch_size:
                                    yield batch
                                    batch = []
                        except Exception as e:
                            logger.warning(f"Failed to load file {file_path}: {e}")
                    
                    # 检查批次大小
                    if batch and len(batch) >= batch_size:
                        yield batch
                        batch = []
            
            # 返回最后一批
            if batch:
                yield batch
            
        except Exception as e:
            self._stats["file_errors"] += 1
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to stream list data: {e}")
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        try:
            start_time = time.time()
            
            # 检查基础路径
            if not os.path.exists(self.config.base_path):
                raise StorageConnectionError(f"Base path does not exist: {self.config.base_path}")
            
            # 检查写权限
            test_file = os.path.join(self.config.base_path, ".health_check")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                raise StorageConnectionError(f"No write permission to base path: {e}")
            
            # 统计文件数量和大小
            file_count = 0
            total_size = 0
            
            for root, dirs, files in os.walk(self.config.base_path):
                for file in files:
                    # 跳过元数据和索引文件
                    if (file.startswith(self.config.metadata_file_name) or 
                        file.startswith(self.config.index_file_name)):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        file_count += 1
                    except Exception:
                        pass
            
            # 更新统计信息
            self._stats["file_count"] = file_count
            self._stats["total_file_size"] = total_size
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "base_path": self.config.base_path,
                "file_count": file_count,
                "total_size_bytes": total_size,
                "response_time_ms": response_time,
                "total_operations": self._stats["total_operations"],
                "file_errors": self._stats["file_errors"],
                "lock_timeouts": self._stats["lock_timeouts"],
                "config": self.config.to_dict()
            }
            
        except Exception as e:
            self._stats["file_errors"] += 1
            raise StorageConnectionError(f"Health check failed: {e}")
    
    @asynccontextmanager
    async def _get_file_lock(self, file_path: str):
        """获取文件锁"""
        lock_key = file_path
        
        with self._lock_lock:
            if lock_key not in self._file_locks:
                self._file_locks[lock_key] = threading.Lock()
            
            file_lock = self._file_locks[lock_key]
        
        # 尝试获取锁
        lock_acquired = file_lock.acquire(timeout=self.config.lock_timeout)
        if not lock_acquired:
            self._stats["lock_timeouts"] += 1
            raise StorageTimeoutError(f"Failed to acquire lock for {file_path}")
        
        try:
            yield
        finally:
            file_lock.release()
    
    async def _serialize_data(self, data: Dict[str, Any]) -> bytes:
        """序列化数据"""
        try:
            if self.config.file_format == "json":
                return json.dumps(data, default=str).encode('utf-8')
            elif self.config.file_format == "pickle":
                return pickle.dumps(data)
            elif self.config.file_format == "yaml":
                return yaml.dump(data, default_flow_style=False).encode('utf-8')
            else:
                raise StorageError(f"Unsupported file format: {self.config.file_format}")
        except Exception as e:
            raise StorageError(f"Failed to serialize data: {e}")
    
    async def _deserialize_data(self, data: bytes) -> Dict[str, Any]:
        """反序列化数据"""
        try:
            if self.config.file_format == "json":
                return json.loads(data.decode('utf-8'))
            elif self.config.file_format == "pickle":
                return pickle.loads(data)
            elif self.config.file_format == "yaml":
                return yaml.safe_load(data.decode('utf-8'))
            else:
                raise StorageError(f"Unsupported file format: {self.config.file_format}")
        except Exception as e:
            raise StorageError(f"Failed to deserialize data: {e}")
    
    async def _compress_data(self, data: bytes) -> bytes:
        """压缩数据"""
        try:
            if self.config.compression_type == "gzip":
                return gzip.compress(data, compresslevel=self.config.compression_level)
            elif self.config.compression_type == "bz2":
                return bz2.compress(data, compresslevel=self.config.compression_level)
            elif self.config.compression_type == "lzma":
                return lzma.compress(data, preset=self.config.compression_level)
            else:
                raise StorageError(f"Unsupported compression type: {self.config.compression_type}")
        except Exception as e:
            raise StorageError(f"Failed to compress data: {e}")
    
    async def _decompress_data(self, data: bytes) -> bytes:
        """解压缩数据"""
        try:
            if self.config.compression_type == "gzip":
                return gzip.decompress(data)
            elif self.config.compression_type == "bz2":
                return bz2.decompress(data)
            elif self.config.compression_type == "lzma":
                return lzma.decompress(data)
            else:
                raise StorageError(f"Unsupported compression type: {self.config.compression_type}")
        except Exception as e:
            raise StorageError(f"Failed to decompress data: {e}")
    
    async def _encrypt_data(self, data: bytes) -> bytes:
        """加密数据"""
        # 简单的XOR加密实现（实际应用中应使用更安全的加密算法）
        try:
            if not self.config.encryption_key:
                return data
            key = self.config.encryption_key.encode('utf-8')
            key_bytes = key * (len(data) // len(key) + 1)
            return bytes([b ^ k for b, k in zip(data, key_bytes)])
        except Exception as e:
            raise StorageError(f"Failed to encrypt data: {e}")
    
    async def _decrypt_data(self, data: bytes) -> bytes:
        """解密数据"""
        # 简单的XOR解密实现（实际应用中应使用更安全的解密算法）
        try:
            if not self.config.encryption_key:
                return data
            key = self.config.encryption_key.encode('utf-8')
            key_bytes = key * (len(data) // len(key) + 1)
            return bytes([b ^ k for b, k in zip(data, key_bytes)])
        except Exception as e:
            raise StorageError(f"Failed to decrypt data: {e}")
    
    async def _write_file(self, file_path: str, data: bytes) -> None:
        """写入文件"""
        # 写入临时文件
        temp_path = f"{file_path}.tmp"
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 写入临时文件
            with open(temp_path, "wb") as f:
                f.write(data)
                
                # 同步到磁盘
                if self.config.enable_sync:
                    f.flush()
                    os.fsync(f.fileno())
            
            # 原子性重命名
            os.rename(temp_path, file_path)
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise StorageError(f"Failed to write file {file_path}: {e}")
    
    async def _read_file(self, file_path: str) -> Optional[bytes]:
        """读取文件"""
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, "rb") as f:
                return f.read()
                
        except Exception as e:
            raise StorageError(f"Failed to read file {file_path}: {e}")
    
    async def _load_file_direct(self, file_path: str) -> Optional[Dict[str, Any]]:
        """直接加载文件（不通过索引）"""
        try:
            # 读取文件
            serialized_data = await self._read_file(file_path)
            if serialized_data is None:
                return None
            
            # 解密数据（如果需要）
            if self.config.enable_encryption:
                serialized_data = await self._decrypt_data(serialized_data)
            
            # 解压缩数据（如果需要）
            if self.config.enable_compression:
                serialized_data = await self._decompress_data(serialized_data)
            
            # 反序列化数据
            data = await self._deserialize_data(serialized_data)
            return data
            
        except Exception as e:
            logger.warning(f"Failed to load file {file_path}: {e}")
            return None
    
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
    
    def _update_stats(self, operation: str, duration: float) -> None:
        """更新统计信息"""
        self._stats["total_operations"] += 1
        if f"{operation}_operations" in self._stats:
            self._stats[f"{operation}_operations"] += 1
    
    async def _create_backup(self, file_path: str) -> None:
        """创建备份文件"""
        try:
            for i in range(self.config.backup_count - 1, 0, -1):
                old_backup = self.config.get_backup_file_path(file_path, i)
                new_backup = self.config.get_backup_file_path(file_path, i + 1)
                
                if os.path.exists(old_backup):
                    shutil.move(old_backup, new_backup)
            
            # 创建第一个备份
            first_backup = self.config.get_backup_file_path(file_path, 1)
            shutil.copy2(file_path, first_backup)
            
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
    
    async def _delete_backups(self, file_path: str) -> None:
        """删除备份文件"""
        try:
            for i in range(1, self.config.backup_count + 1):
                backup_path = self.config.get_backup_file_path(file_path, i)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
        except Exception as e:
            logger.warning(f"Failed to delete backups for {file_path}: {e}")
    
    async def _load_index(self) -> None:
        """加载索引"""
        if not self.config.enable_indexing:
            return
        
        try:
            index_path = self.config.get_index_file_path(self.config.base_path)
            if os.path.exists(index_path):
                with open(index_path, "r") as f:
                    self._index_cache = json.load(f)
            else:
                self._index_cache = {}
        except Exception as e:
            logger.warning(f"Failed to load index: {e}")
            self._index_cache = {}
    
    async def _save_index(self) -> None:
        """保存索引"""
        if not self.config.enable_indexing:
            return
        
        try:
            index_path = self.config.get_index_file_path(self.config.base_path)
            with open(index_path, "w") as f:
                json.dump(self._index_cache, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save index: {e}")
    
    async def _update_index(self, id: str, file_path: str, data: Dict[str, Any]) -> None:
        """更新索引"""
        if not self.config.enable_indexing:
            return
        
        with self._index_cache_lock:
            self._index_cache[id] = {
                "file_path": file_path,
                "data": {
                    "id": id,
                    "type": data.get("type"),
                    "session_id": data.get("session_id"),
                    "thread_id": data.get("thread_id"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                }
            }
    
    async def _remove_from_index(self, id: str) -> None:
        """从索引中移除"""
        if not self.config.enable_indexing:
            return
        
        with self._index_cache_lock:
            if id in self._index_cache:
                del self._index_cache[id]
    
    async def _find_file_path(self, id: str) -> Optional[str]:
        """从索引查找文件路径"""
        if not self.config.enable_indexing:
            # 扫描文件系统查找
            for root, dirs, files in os.walk(self.config.base_path):
                for file in files:
                    if file.startswith(id):
                        return os.path.join(root, file)
            return None
        
        with self._index_cache_lock:
            item_info = self._index_cache.get(id)
            return item_info["file_path"] if item_info else None
    
    async def _update_metadata(self, directory: str, id: str, data: Dict[str, Any]) -> None:
        """更新元数据"""
        if not self.config.enable_metadata_file:
            return
        
        try:
            metadata_path = self.config.get_metadata_file_path(directory)
            
            # 加载现有元数据
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
            
            # 更新元数据
            metadata[id] = {
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "type": data.get("type"),
                "size": len(str(data))
            }
            
            # 保存元数据
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2, default=str)
                
        except Exception as e:
            logger.warning(f"Failed to update metadata for {id}: {e}")
    
    async def _remove_from_metadata(self, directory: str, id: str) -> None:
        """从元数据中移除"""
        if not self.config.enable_metadata_file:
            return
        
        try:
            metadata_path = self.config.get_metadata_file_path(directory)
            
            if not os.path.exists(metadata_path):
                return
            
            # 加载现有元数据
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # 移除元数据
            if id in metadata:
                del metadata[id]
                
                # 保存元数据
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2, default=str)
                
        except Exception as e:
            logger.warning(f"Failed to remove from metadata for {id}: {e}")
    
    async def _cleanup_worker(self) -> None:
        """清理工作线程（异步任务）"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
                
                # 清理旧数据
                count = await self.cleanup_old_data_impl(self.config.retention_days)
                if count > 0:
                    logger.info(f"Cleaned up {count} old files")
                
                # 保存索引
                await self._save_index()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")