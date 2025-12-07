"""Repository基类

提供所有Repository实现的通用基类和功能。
"""

from src.services.logger.injection import get_logger
from abc import ABC
from typing import Dict, Any, Optional, Type

from src.interfaces.repository import RepositoryError
from src.interfaces.storage.adapter import IStorageAdapter, IDataTransformer
from src.adapters.storage.adapter.storage_adapter import StorageAdapter
from src.adapters.storage.adapter.data_transformer import DefaultDataTransformer
from src.core.storage.config import StorageConfigManager, StorageType
from src.infrastructure.error_management.impl.storage_adapter import StorageAdapterErrorHandler

logger = get_logger(__name__)


class BaseRepository(ABC):
    """Repository基类，包含通用功能"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        storage_adapter: Optional[IStorageAdapter] = None,
        data_transformer: Optional[IDataTransformer] = None,
        repository_type: str = "default"
    ):
        """初始化基类
        
        Args:
            config: 配置参数
            storage_adapter: 存储适配器（可选）
            data_transformer: 数据转换器（可选）
            repository_type: 仓库类型
        """
        self.config = config
        self.repository_type = repository_type
        self.logger = get_logger(self.__class__.__name__)
        
        # 初始化存储适配器
        if storage_adapter is None:
            self.storage_adapter = self._create_default_storage_adapter()
        else:
            self.storage_adapter = storage_adapter
        
        # 初始化数据转换器
        if data_transformer is None:
            self.data_transformer = DefaultDataTransformer()
        else:
            self.data_transformer = data_transformer
    
    def _create_default_storage_adapter(self) -> IStorageAdapter:
        """创建默认存储适配器
        
        Returns:
            存储适配器实例
        """
        try:
            # 获取配置管理器
            config_manager = StorageConfigManager()
            
            # 根据仓库类型确定存储类型
            storage_type = self._get_storage_type_for_repository()
            
            # 获取存储配置
            storage_config = config_manager.get_config(f"{self.repository_type}_default")
            if storage_config is None:
                # 使用默认配置
                storage_config = config_manager.get_default_config()
                if storage_config is None:
                    raise RepositoryError(f"无法找到 {self.repository_type} 的存储配置")
            
            # 获取后端配置
            backend_config = storage_config.config
            
            # 创建存储后端
            storage_backend = self._create_storage_backend(storage_type.value, backend_config)
            
            # 创建错误处理器
            error_handler = StorageAdapterErrorHandler()
            
            # 创建并返回适配器
            return StorageAdapter(
                backend=storage_backend,
                transformer=self.data_transformer,
                error_handler=error_handler
            )
            
        except Exception as e:
            self.logger.error(f"创建默认存储适配器失败: {e}")
            raise RepositoryError(f"创建存储适配器失败: {e}") from e
    
    def _get_storage_type_for_repository(self) -> StorageType:
        """根据仓库类型获取存储类型
        
        Returns:
            存储类型
        """
        # 默认映射关系
        repository_storage_mapping = {
            "state": StorageType.SQLITE,
            "history": StorageType.SQLITE,
            "snapshot": StorageType.FILE,
            "checkpoint": StorageType.SQLITE
        }
        
        return repository_storage_mapping.get(self.repository_type, StorageType.SQLITE)
    
    def _create_storage_backend(self, backend_type: str, config: Dict[str, Any]):
        """创建存储后端
        
        Args:
            backend_type: 后端类型
            config: 后端配置
            
        Returns:
            存储后端实例
        """
        try:
            if backend_type == "sqlite":
                from src.adapters.storage.backends.sqlite_backend import SQLiteStorageBackend
                return SQLiteStorageBackend(**config)
            elif backend_type == "memory":
                from src.adapters.storage.backends.memory_backend import MemoryStorageBackend
                return MemoryStorageBackend(**config)
            elif backend_type == "file":
                from src.adapters.storage.backends.file_backend import FileStorageBackend
                return FileStorageBackend(**config)
            else:
                raise ValueError(f"不支持的存储后端类型: {backend_type}")
                
        except Exception as e:
            self.logger.error(f"创建存储后端失败 {backend_type}: {e}")
            raise RepositoryError(f"创建存储后端失败: {e}") from e
    
    def _log_operation(self, operation: str, success: bool, details: str = "") -> None:
        """记录操作日志
        
        Args:
            operation: 操作名称
            success: 是否成功
            details: 详细信息
        """
        status = "成功" if success else "失败"
        message = f"{operation}{status}"
        if details:
            message += f": {details}"
        
        if success:
            self.logger.debug(message)
        else:
            self.logger.error(message)
    
    def _handle_exception(self, operation: str, exception: Exception) -> None:
        """处理异常
        
        Args:
            operation: 操作名称
            exception: 异常对象
        """
        error_msg = f"{operation}失败: {exception}"
        self.logger.error(error_msg)
        raise RepositoryError(error_msg) from exception
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据
        
        Args:
            data: 要保存的数据
            
        Returns:
            保存的数据ID
        """
        return await self.storage_adapter.save(data)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，如果不存在则返回None
        """
        return await self.storage_adapter.load(id)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            id: 数据ID
            updates: 要更新的字段
            
        Returns:
            是否更新成功
        """
        return await self.storage_adapter.update(id, updates)
    
    async def delete(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        return await self.storage_adapter.delete(id)
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            
        Returns:
            数据是否存在
        """
        return await self.storage_adapter.exists(id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> list:
        """列出数据
        
        Args:
            filters: 过滤条件
            limit: 限制返回数量
            
        Returns:
            数据列表
        """
        return await self.storage_adapter.list(filters, limit)
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数数据
        
        Args:
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
        """
        return await self.storage_adapter.count(filters)
    
    async def batch_save(self, data_list: list) -> list:
        """批量保存
        
        Args:
            data_list: 数据列表
            
        Returns:
            保存的数据ID列表
        """
        return await self.storage_adapter.batch_save(data_list)
    
    async def batch_delete(self, ids: list) -> int:
        """批量删除
        
        Args:
            ids: 数据ID列表
            
        Returns:
            删除的数据数量
        """
        return await self.storage_adapter.batch_delete(ids)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        return await self.storage_adapter.health_check()