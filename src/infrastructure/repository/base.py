"""Repository基类

提供所有Repository实现的通用基类和功能。
"""

from src.interfaces.dependency_injection import get_logger
from abc import ABC
from typing import Dict, Any, Optional, Type

from src.interfaces.repository import RepositoryError

logger = get_logger(__name__)


class BaseRepository(ABC):
    """Repository基类，包含通用功能"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        storage_backend: Optional[Any] = None,
        repository_type: str = "default"
    ):
        """初始化基类
        
        Args:
            config: 配置参数
            storage_backend: 存储后端（可选）
            repository_type: 仓库类型
        """
        self.config = config
        self.repository_type = repository_type
        self.logger = get_logger(self.__class__.__name__)
        
        # 初始化存储后端
        if storage_backend is None:
            self.storage_backend = self._create_default_storage_backend()
        else:
            self.storage_backend = storage_backend
        
        # 默认表名
        self.table_name = f"{repository_type}_data"
    
    def _create_default_storage_backend(self):
        """创建默认存储后端
        
        Returns:
            存储后端实例
        """
        try:
            # 根据仓库类型确定存储类型
            storage_type = self._get_storage_type_for_repository()
            
            # 使用默认配置
            backend_config = self.config.get('storage', {})
            
            # 创建存储后端
            return self._create_storage_backend(storage_type, backend_config)
            
        except Exception as e:
            self.logger.error(f"创建默认存储后端失败: {e}")
            raise RepositoryError(f"创建存储后端失败: {e}") from e
    
    def _get_storage_type_for_repository(self) -> str:
        """根据仓库类型获取存储类型
        
        Returns:
            存储类型
        """
        # 默认映射关系
        repository_storage_mapping = {
            "state": "sqlite",
            "history": "sqlite",
            "snapshot": "file",
            "checkpoint": "sqlite"
        }
        
        return repository_storage_mapping.get(self.repository_type, "sqlite")
    
    def _create_storage_backend(self, backend_type: str, config: Dict[str, Any]):
        """创建存储后端
        
        Args:
            backend_type: 后端类型
            config: 后端配置
            
        Returns:
            存储后端实例
        """
        try:
            # 根据后端类型创建提供者
            if backend_type == "sqlite":
                from src.adapters.storage.backends.providers.sqlite_provider import SQLiteProvider
                provider = SQLiteProvider(**config)
                # 创建通用存储后端，使用提供者
                from src.adapters.storage.backends.core.base_backend import BaseStorageBackend
                return self._create_backend_with_provider(provider, config)
            elif backend_type == "memory":
                from src.adapters.storage.backends.providers.memory_provider import MemoryProvider
                provider = MemoryProvider(**config)
                from src.adapters.storage.backends.core.base_backend import BaseStorageBackend
                return self._create_backend_with_provider(provider, config)
            elif backend_type == "file":
                from src.adapters.storage.backends.providers.file_provider import FileProvider
                provider = FileProvider(**config)
                from src.adapters.storage.backends.core.base_backend import BaseStorageBackend
                return self._create_backend_with_provider(provider, config)
            else:
                raise ValueError(f"不支持的存储后端类型: {backend_type}")
                
        except Exception as e:
            self.logger.error(f"创建存储后端失败 {backend_type}: {e}")
            raise RepositoryError(f"创建存储后端失败: {e}") from e
    
    def _create_backend_with_provider(self, provider, config: Dict[str, Any]):
        """使用提供者创建存储后端
        
        Args:
            provider: 存储提供者实例
            config: 配置参数
            
        Returns:
            存储后端实例
        """
        # 创建一个简单的通用后端实现
        class GenericStorageBackend:
            def __init__(self, provider, config):
                self.provider = provider
                self.config = config
                self._connected = False
            
            async def connect(self):
                if not self._connected:
                    await self.provider.connect()
                    self._connected = True
            
            async def disconnect(self):
                if self._connected:
                    await self.provider.disconnect()
                    self._connected = False
            
            async def is_connected(self):
                return self._connected
            
            async def health_check(self):
                return await self.provider.health_check()
            
            async def save(self, table_name, data):
                return await self.provider.save(table_name, data)
            
            async def load(self, table_name, id):
                return await self.provider.load(table_name, id)
            
            async def update(self, table_name, id, updates):
                return await self.provider.update(table_name, id, updates)
            
            async def delete(self, table_name, id):
                return await self.provider.delete(table_name, id)
            
            async def exists(self, table_name, id):
                return await self.provider.exists(table_name, id)
            
            async def list(self, table_name, filters, limit=None):
                return await self.provider.list(table_name, filters, limit)
            
            async def query(self, table_name, query, params):
                return await self.provider.query(table_name, query, params)
            
            async def count(self, table_name, filters):
                return await self.provider.count(table_name, filters)
            
            async def batch_save(self, table_name, data_list):
                return await self.provider.batch_save(table_name, data_list)
            
            async def batch_delete(self, table_name, ids):
                return await self.provider.batch_delete(table_name, ids)
            
            async def create_table(self, table_name, schema):
                return await self.provider.create_table(table_name, schema)
            
            async def table_exists(self, table_name):
                return await self.provider.table_exists(table_name)
        
        return GenericStorageBackend(provider, config)
    
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
        return await self.storage_backend.save(self.table_name, data)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，如果不存在则返回None
        """
        return await self.storage_backend.load(self.table_name, id)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            id: 数据ID
            updates: 要更新的字段
            
        Returns:
            是否更新成功
        """
        return await self.storage_backend.update(self.table_name, id, updates)
    
    async def delete(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        return await self.storage_backend.delete(self.table_name, id)
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            
        Returns:
            数据是否存在
        """
        return await self.storage_backend.exists(self.table_name, id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> list:
        """列出数据
        
        Args:
            filters: 过滤条件
            limit: 限制返回数量
            
        Returns:
            数据列表
        """
        return await self.storage_backend.list(self.table_name, filters, limit)
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数数据
        
        Args:
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
        """
        return await self.storage_backend.count(self.table_name, filters)
    
    async def batch_save(self, data_list: list) -> list:
        """批量保存
        
        Args:
            data_list: 数据列表
            
        Returns:
            保存的数据ID列表
        """
        return await self.storage_backend.batch_save(self.table_name, data_list)
    
    async def batch_delete(self, ids: list) -> int:
        """批量删除
        
        Args:
            ids: 数据ID列表
            
        Returns:
            删除的数据数量
        """
        return await self.storage_backend.batch_delete(self.table_name, ids)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        return await self.storage_backend.health_check()
    
    async def connect(self) -> None:
        """连接到存储后端"""
        await self.storage_backend.connect()
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        await self.storage_backend.disconnect()
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return await self.storage_backend.is_connected()