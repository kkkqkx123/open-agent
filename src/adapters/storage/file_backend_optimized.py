"""优化的文件存储后端

提供基于文件的存储后端实现，使用增强基类减少重复代码。
"""

import asyncio
import os
import shutil
import threading
import time
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.core.state.exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageCapacityError
)
from .base_optimized import EnhancedStorageBackend
from .utils.common_utils import StorageCommonUtils
from .utils.file_utils import FileStorageUtils


logger = logging.getLogger(__name__)


class FileStorageBackend(EnhancedStorageBackend):
    """优化的文件存储后端实现
    
    提供基于文件的存储后端，支持持久化、压缩、目录组织等功能。
    使用增强基类减少重复代码。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化文件存储
        
        Args:
            **config: 配置参数
        """
        # 初始化基类
        EnhancedStorageBackend.__init__(self, **config)
        
        # 文件存储特定配置
        self.base_path = config.get("base_path", "file_storage")
        self.compression_threshold = config.get("compression_threshold", 1024)
        self.directory_structure = config.get("directory_structure", "flat")  # flat, by_type, by_date, by_agent
        self.file_extension = config.get("file_extension", "json")
        self.enable_metadata = config.get("enable_metadata", True)
        self.max_directory_size = config.get("max_directory_size")  # 最大目录大小（字节）
        self.max_files_per_directory = config.get("max_files_per_directory", 1000)
        
        # 扩展统计信息
        self._stats.update({
            "total_files": 0,
            "total_size_bytes": 0,
            "expired_files_cleaned": 0,
            "compression_ratio": 0.0
        })
        
        logger.info(f"FileStorageBackend initialized with base_path: {self.base_path}")
    
    async def connect(self) -> None:
        """连接到存储后端"""
        try:
            if self._connected:
                return
            
            # 确保基础目录存在
            StorageCommonUtils.ensure_directory_exists(self.base_path)
            
            # 调用父类连接逻辑（启动清理和备份任务）
            await EnhancedStorageBackend.connect(self)
            
        except Exception as e:
            raise StorageConnectionError(f"Failed to connect FileStorageBackend: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 调用父类断开逻辑
            await EnhancedStorageBackend.disconnect(self)
            
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
            if isinstance(data, dict):
                item_id = StorageCommonUtils.validate_data_id(data)
                current_time = time.time()
                
                # 添加元数据
                if self.enable_metadata:
                    data["created_at"] = data.get("created_at", current_time)
                    data["updated_at"] = current_time
                    
                    if self.enable_ttl and "expires_at" not in data:
                        data["expires_at"] = current_time + self.default_ttl_seconds
                
                # 压缩数据（如果需要）
                processed_data: Union[Dict[str, Any], bytes] = data
                if not compressed and self.enable_compression and StorageCommonUtils.should_compress_data(data, self.compression_threshold):
                    processed_data = StorageCommonUtils.compress_data(data)
                    compressed = True
                
                # 获取文件路径
                file_path = self._get_file_path(item_id, data)
                
                # 保存数据
                async with self._lock:
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
                                # 使用通用工具类的序列化方法
                                serialized_data = StorageCommonUtils.serialize_data(processed_data)
                                StorageCommonUtils.ensure_directory_exists(os.path.dirname(file_path))
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(serialized_data)
                            else:
                                raise StorageError(f"Expected dict for uncompressed data, got {type(processed_data)}")
                        
                        self._update_stats("save")
                
                return item_id
            else:
                raise StorageError(f"Expected dict for data, got {type(data)}")
                
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
                        if not os.path.exists(file_path):
                            continue
                        
                        # 检查是否过期
                        if self.enable_ttl:
                            data = FileStorageUtils.load_data_from_file(file_path)
                            if data and "expires_at" in data and data["expires_at"] < time.time():
                                os.remove(file_path)
                                self._stats["expired_files_cleaned"] += 1
                                continue
                        
                        # 加载数据
                        try:
                            # 尝试作为压缩文件加载
                            with open(file_path, 'rb') as f:
                                compressed_data = f.read()
                            
                            # 检查是否是压缩数据
                            try:
                                data = StorageCommonUtils.decompress_data(compressed_data)
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
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        try:
            # 获取可能的文件路径
            file_paths = await self._get_possible_file_paths(id)
            
            async with self._lock:
                with self._thread_lock:
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            os.remove(file_path)
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
                    all_files = self._list_files_in_directory(
                        self.base_path,
                        f"*.{self.file_extension}",
                        recursive=True
                    )
                    
                    # 按修改时间排序（最新的在前）
                    all_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
                    
                    # 处理文件
                    for file_path in all_files:
                        # 检查限制
                        if limit and len(results) >= limit:
                            break
                        
                        # 加载数据
                        data = self._load_data_from_file(file_path)
                        if data is None:
                            continue
                        
                        # 检查是否过期
                        if self.enable_ttl and "expires_at" in data and data["expires_at"] < time.time():
                            os.remove(file_path)
                            self._stats["expired_files_cleaned"] += 1
                            continue
                        
                        # 检查过滤器
                        if StorageCommonUtils.matches_filters(data, filters):
                            results.append(data)
            
            self._update_stats("list")
            return results
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to list data: {e}")
    
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
            
            # 使用通用工具准备健康检查响应
            return StorageCommonUtils.prepare_health_check_response(
                status="healthy",
                config={
                    "enable_compression": self.enable_compression,
                    "compression_threshold": self.compression_threshold,
                    "enable_ttl": self.enable_ttl,
                    "directory_structure": self.directory_structure,
                    "enable_backup": self.enable_backup,
                    "backup_interval_hours": self.backup_interval_hours
                },
                stats=self._stats,
                base_path=self.base_path,
                directory_exists=storage_info["directory_exists"],
                total_files=self._stats["total_files"],
                total_size_bytes=self._stats["total_size_bytes"],
                total_size_mb=storage_info["total_size_mb"],
                compression_ratio=self._stats["compression_ratio"],
            )
            
        except Exception as e:
            raise StorageConnectionError(f"Health check failed: {e}")
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        try:
            cutoff_time = StorageCommonUtils.calculate_cutoff_time(retention_days)
            
            async with self._lock:
                with self._thread_lock:
                    cleaned_count = FileStorageUtils.cleanup_old_files(self.base_path, cutoff_time)
            
            return cleaned_count
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to cleanup old data: {e}")
    
    # 文件存储特定的辅助方法
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
                current_files = len(self._list_files_in_directory(
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
    
    async def _create_backup(self) -> None:
        """创建备份"""
        try:
            # 确保备份目录存在
            backup_dir = Path(self.backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成备份目录名
            current_backup_dir = backup_dir / StorageCommonUtils.generate_timestamp_filename("storage_backup")
            
            # 创建备份
            success = FileStorageUtils.backup_directory(self.base_path, str(current_backup_dir))
            
            if success:
                # 更新统计信息
                self._stats["backup_count"] += 1
                self._stats["last_backup_time"] = time.time()
                
                logger.info(f"Created backup: {current_backup_dir}")
                
                # 清理旧备份
                StorageCommonUtils.cleanup_old_backups(
                    str(backup_dir), self.max_backup_files, "storage_backup_*"
                )
            else:
                logger.error("Failed to create backup")
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    # 文件存储特定的辅助方法
    def _load_data_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从文件加载数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            加载的数据或None
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
                return StorageCommonUtils.deserialize_data(data)
        except Exception as e:
            logger.error(f"Failed to load data from file {file_path}: {e}")
            return None
    
    def _list_files_in_directory(
        self,
        dir_path: str,
        pattern: str = "*.json",
        recursive: bool = False
    ) -> List[str]:
        """列出目录中的文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件模式
            recursive: 是否递归搜索
            
        Returns:
            文件路径列表
        """
        if not os.path.exists(dir_path):
            return []
        
        path_obj = Path(dir_path)
        
        if recursive:
            files = list(path_obj.rglob(pattern))
        else:
            files = list(path_obj.glob(pattern))
        
        return [str(f) for f in files]