"""优化的文件存储后端

提供基于文件的存储后端实现，使用增强基类减少重复代码。
"""

import os
import time
from src.services.logger import get_logger
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.core.common.exceptions.state import (
    StorageError,
    StorageConnectionError,
    StorageCapacityError,
    StorageValidationError
)
from src.core.common.error_management import handle_error, ErrorCategory, ErrorSeverity
from ..adapters.base import StorageBackend
from ..utils.common_utils import StorageCommonUtils
from ..utils.file_utils import FileStorageUtils


logger = get_logger(__name__)


class FileStorageBackend(StorageBackend):
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
        StorageBackend.__init__(self, **config)
        
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
            await StorageBackend.connect(self)
            
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "connect",
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageConnectionError(f"Failed to connect FileStorageBackend: {e}") from e
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        try:
            if not self._connected:
                return
            
            # 调用父类断开逻辑
            await StorageBackend.disconnect(self)
            
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "disconnect",
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageConnectionError(f"Failed to disconnect FileStorageBackend: {e}") from e
    
    def _get_file_path(self, item_id: str, data: Optional[Dict[str, Any]] = None) -> str:
        """获取文件路径
        
        Args:
            item_id: 项目ID
            data: 数据（可选，用于确定目录结构）
            
        Returns:
            文件路径
            
        Raises:
            StorageValidationError: 路径验证失败
        """
        try:
            # 输入验证
            if not item_id:
                raise StorageValidationError("项目ID不能为空")
            
            if not isinstance(item_id, str):
                raise StorageValidationError(f"项目ID必须是字符串，实际类型: {type(item_id).__name__}")
            
            # 检查项目ID是否包含非法字符
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
            if any(char in item_id for char in invalid_chars):
                raise StorageValidationError(f"项目ID包含非法字符: {item_id}")
            
            if self.directory_structure == "flat":
                # 平铺结构
                file_path = os.path.join(self.base_path, f"{item_id}.{self.file_extension}")
            
            elif self.directory_structure == "by_type":
                # 按类型组织
                data_type = data.get("type", "unknown") if data else "unknown"
                type_dir = os.path.join(self.base_path, data_type)
                file_path = os.path.join(type_dir, f"{item_id}.{self.file_extension}")
            
            elif self.directory_structure == "by_date":
                # 按日期组织
                current_time = time.time()
                date_str = time.strftime("%Y-%m-%d", time.localtime(current_time))
                date_dir = os.path.join(self.base_path, date_str)
                file_path = os.path.join(date_dir, f"{item_id}.{self.file_extension}")
            
            elif self.directory_structure == "by_agent":
                # 按代理组织
                agent_id = data.get("agent_id", "unknown") if data else "unknown"
                agent_dir = os.path.join(self.base_path, agent_id)
                file_path = os.path.join(agent_dir, f"{item_id}.{self.file_extension}")
            
            else:
                # 默认平铺结构
                file_path = os.path.join(self.base_path, f"{item_id}.{self.file_extension}")
            
            # 验证路径长度
            if len(file_path) > 260:  # Windows路径长度限制
                raise StorageValidationError(f"文件路径过长: {len(file_path)} 字符")
            
            return file_path
            
        except StorageValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "_get_file_path",
                "item_id": item_id,
                "directory_structure": self.directory_structure
            }
            handle_error(e, error_context)
            raise StorageValidationError(f"获取文件路径失败: {e}") from e
    
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
                if not compressed and self.enable_compression:
                    import json
                    data_size = len(json.dumps(data))
                    if data_size > self.compression_threshold:
                        from src.core.state.core.base import BaseStateSerializer
                        from src.core.state.core.base import BaseState
                        serializer = BaseStateSerializer(format="pickle", compression=True)
                        state_obj = BaseState(data=data)
                        serialized = serializer.serialize(state_obj)
                        if isinstance(serialized, bytes):
                            processed_data = serialized
                        else:
                            processed_data = serialized.encode() if isinstance(serialized, str) else bytes(serialized)
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
                                # 使用文件存储工具类的保存方法
                                FileStorageUtils.save_data_to_file(file_path, processed_data)
                            else:
                                raise StorageError(f"Expected dict for uncompressed data, got {type(processed_data)}")
                        
                        self._update_stats("save")
                
                return item_id
            else:
                raise StorageError(f"Expected dict for data, got {type(data)}")
                
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "save_impl",
                "data_type": type(data).__name__,
                "compressed": compressed,
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageError(f"Failed to save data: {e}") from e
    
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
                                from src.core.state.core.base import BaseStateSerializer
                                serializer = BaseStateSerializer(compression=True)
                                state_obj = serializer.deserialize(compressed_data)
                                data = state_obj.to_dict()
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
            
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "load_impl",
                "item_id": id,
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageError(f"Failed to load data {id}: {e}") from e
    
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
            
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "delete_impl",
                "item_id": id,
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageError(f"Failed to delete data {id}: {e}") from e
    
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
            
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "list_impl",
                "filters": filters,
                "limit": limit,
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageError(f"Failed to list data: {e}") from e
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        try:
            from src.core.state.statistics import FileStorageStatistics, HealthCheckHelper
            
            # 获取存储信息
            dir_info = FileStorageUtils.get_directory_structure_info(self.base_path, self.directory_structure)
            total_size = FileStorageUtils.calculate_directory_size(self.base_path)
            total_files = FileStorageUtils.count_files_in_directory(self.base_path)
            
            # 更新统计信息
            self._stats["total_files"] = total_files
            self._stats["total_size_bytes"] = total_size
            
            # 清理过期文件（异步处理）
            if self.enable_ttl:
                expired_count = 0
                # 获取所有文件并检查过期
                all_files = FileStorageUtils.list_files_in_directory(
                    self.base_path,
                    pattern=f"*.{self.file_extension}",
                    recursive=True
                )
                current_time = time.time()
                for file_path in all_files:
                    modified_time = FileStorageUtils.get_file_modified_time(file_path)
                    # 如果文件超过TTL时间则删除
                    if current_time - modified_time > self.default_ttl_seconds:
                        if FileStorageUtils.delete_file(file_path):
                            expired_count += 1
                self._stats["expired_files_cleaned"] += expired_count
            
            # 计算压缩比
            compression_ratio = 0.0
            if self.enable_compression:
                # 简化的压缩比计算
                compression_ratio = 0.3  # 假设平均压缩比为30%
            
            self._stats["compression_ratio"] = compression_ratio
            
            # 创建统计对象
            stats = FileStorageStatistics(
                status="healthy",
                timestamp=time.time(),
                total_size_bytes=total_size,
                total_size_mb=round(total_size / (1024 * 1024), 2),
                total_items=total_files,
                total_records=total_files,
                directory_path=self.base_path,
                file_count=total_files,
            )
            
            # 使用健康检查助手准备响应
            return HealthCheckHelper.prepare_health_check_response(
                status="healthy",
                stats=stats,
                config={
                    "enable_compression": self.enable_compression,
                    "compression_threshold": self.compression_threshold,
                    "enable_ttl": self.enable_ttl,
                    "directory_structure": self.directory_structure,
                    "enable_backup": self.enable_backup,
                    "backup_interval_hours": self.backup_interval_hours
                },
                base_path=self.base_path,
                directory_exists=dir_info.get("directory_exists", False),
                total_files=total_files,
                total_size_bytes=total_size,
                total_size_mb=round(total_size / (1024 * 1024), 2),
                compression_ratio=compression_ratio,
            )
            
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "health_check_impl",
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageConnectionError(f"Health check failed: {e}") from e
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        try:
            cutoff_time = StorageCommonUtils.calculate_cutoff_time(retention_days)
            
            async with self._lock:
                with self._thread_lock:
                    # 获取所有文件
                    all_files = FileStorageUtils.list_files_in_directory(
                        self.base_path,
                        pattern=f"*.{self.file_extension}",
                        recursive=True
                    )
                    
                    cleaned_count = 0
                    for file_path in all_files:
                        modified_time = FileStorageUtils.get_file_modified_time(file_path)
                        # 如果文件早于cutoff_time，则删除
                        if modified_time < cutoff_time:
                            if FileStorageUtils.delete_file(file_path):
                                cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "cleanup_old_data_impl",
                "retention_days": retention_days,
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageError(f"Failed to cleanup old data: {e}") from e
    
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
            
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "_check_capacity_limits",
                "max_directory_size": self.max_directory_size,
                "max_files_per_directory": self.max_files_per_directory,
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            raise StorageError(f"Failed to check capacity limits: {e}") from e
    
    async def _create_backup_impl(self) -> None:
        """创建备份的具体实现
        
        备份存储目录到备份路径。
        """
        from src.core.state.backup_policy import FileBackupStrategy
        
        # 确保备份目录存在
        backup_dir = Path(self.backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成备份目录名
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        current_backup_dir = backup_dir / f"storage_backup_{timestamp}"
        
        # 创建备份
        backup_strategy = FileBackupStrategy()
        async with self._lock:
            with self._thread_lock:
                success = backup_strategy.backup(self.base_path, str(current_backup_dir))
        
        if not success:
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "_create_backup_impl",
                "base_path": self.base_path,
                "backup_path": str(current_backup_dir)
            }
            handle_error(StorageError("Failed to create file storage backup"), error_context)
            raise StorageError("Failed to create file storage backup")
        
        logger.info(f"Created file storage backup: {current_backup_dir}")
        
        # 清理旧备份
        try:
            backup_strategy.cleanup_old_backups(str(backup_dir), self.max_backup_files)
        except Exception as e:
            # 清理备份失败不应该影响主要功能
            logger.warning(f"清理旧备份失败: {e}")
    
    async def _cleanup_expired_items_impl(self) -> None:
        """清理过期项的文件存储特定实现
        
        扫描所有文件并删除过期的文件。
        """
        try:
            async with self._lock:
                with self._thread_lock:
                    # 获取所有文件
                    all_files = self._list_files_in_directory(
                        self.base_path,
                        f"*.{self.file_extension}",
                        recursive=True
                    )
                    
                    current_time = time.time()
                    expired_count = 0
                    
                    # 逐个检查文件的过期时间
                    for file_path in all_files:
                        try:
                            data = FileStorageUtils.load_data_from_file(file_path)
                            if data and StorageCommonUtils.is_data_expired(data, current_time):
                                FileStorageUtils.delete_file(file_path)
                                expired_count += 1
                        except Exception as e:
                            logger.error(f"Error checking expiration for file {file_path}: {e}")
                    
                    self._stats["expired_items_cleaned"] += expired_count
                    
                    if expired_count > 0:
                        logger.debug(f"Cleaned {expired_count} expired files")
        
        except Exception as e:
            # 使用统一错误处理
            error_context = {
                "backend_type": "file",
                "operation": "_cleanup_expired_items_impl",
                "base_path": self.base_path
            }
            handle_error(e, error_context)
            logger.error(f"Error cleaning expired files: {e}")
    
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
        
        return FileStorageUtils.load_data_from_file(file_path)
    
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