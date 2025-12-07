"""存储适配器实现

提供Repository层和Storage Backend层之间的统一适配器实现。
"""

from typing import Dict, Any, Optional, List, AsyncIterator, Union
from src.services.logger.injection import get_logger
from src.interfaces.storage.adapter import IStorageAdapter, IDataTransformer, IStorageErrorHandler
from src.interfaces.storage.base import IStorage
from src.interfaces.storage.exceptions import StorageError
from src.infrastructure.error_management.impl.storage_adapter import StorageAdapterErrorHandler


logger = get_logger(__name__)


class StorageAdapter(IStorageAdapter):
    """统一存储适配器实现
    
    封装存储后端，提供统一的数据访问接口，
    处理数据转换和错误处理。
    """
    
    def __init__(
        self,
        backend: IStorage,
        transformer: IDataTransformer,
        error_handler: Optional[IStorageErrorHandler] = None,
        max_retries: int = 3
    ) -> None:
        """初始化存储适配器
        
        Args:
            backend: 存储后端
            transformer: 数据转换器
            error_handler: 错误处理器（可选，默认使用StorageAdapterErrorHandler）
            max_retries: 最大重试次数
        """
        self.backend = backend
        self.transformer = transformer
        self.error_handler = error_handler or StorageAdapterErrorHandler(max_retries)
        self.logger = get_logger(self.__class__.__name__)
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据
        
        Args:
            data: 要保存的数据字典
            
        Returns:
            保存的数据ID
            
        Raises:
            StorageError: 保存失败时抛出
        """
        return await self.error_handler.handle(
            "save",
            lambda: self._save_internal(data)
        )
    
    async def _save_internal(self, data: Dict[str, Any]) -> str:
        """内部保存实现"""
        # 转换为存储格式
        storage_data = self.transformer.to_storage_format(data)
        
        # 调用后端保存
        result_id = await self.backend.save(storage_data)
        
        self.logger.debug(f"数据保存成功，ID: {result_id}")
        return result_id
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，如果不存在则返回None
            
        Raises:
            StorageError: 加载失败时抛出
        """
        return await self.error_handler.handle(
            "load",
            lambda: self._load_internal(id)
        )
    
    async def _load_internal(self, id: str) -> Optional[Dict[str, Any]]:
        """内部加载实现"""
        # 从后端加载
        storage_data = await self.backend.load(id)
        
        if storage_data is None:
            return None
        
        # 转换为领域格式
        domain_data = self.transformer.from_storage_format(storage_data)
        
        self.logger.debug(f"数据加载成功，ID: {id}")
        return domain_data
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            id: 数据ID
            updates: 要更新的字段
            
        Returns:
            是否更新成功
            
        Raises:
            StorageError: 更新失败时抛出
        """
        return await self.error_handler.handle(
            "update",
            lambda: self._update_internal(id, updates)
        )
    
    async def _update_internal(self, id: str, updates: Dict[str, Any]) -> bool:
        """内部更新实现"""
        # 转换更新数据为存储格式
        storage_updates = self.transformer.to_storage_format(updates)
        
        # 调用后端更新
        result = await self.backend.update(id, storage_updates)
        
        if result:
            self.logger.debug(f"数据更新成功，ID: {id}")
        
        return result
    
    async def delete(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
            
        Raises:
            StorageError: 删除失败时抛出
        """
        return await self.error_handler.handle(
            "delete",
            lambda: self._delete_internal(id)
        )
    
    async def _delete_internal(self, id: str) -> bool:
        """内部删除实现"""
        # 调用后端删除
        result = await self.backend.delete(id)
        
        if result:
            self.logger.debug(f"数据删除成功，ID: {id}")
        
        return result
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            
        Returns:
            数据是否存在
            
        Raises:
            StorageError: 检查失败时抛出
        """
        return await self.error_handler.handle(
            "exists",
            lambda: self._exists_internal(id)
        )
    
    async def _exists_internal(self, id: str) -> bool:
        """内部存在检查实现"""
        # 调用后端存在检查
        return await self.backend.exists(id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据
        
        Args:
            filters: 过滤条件
            limit: 限制返回数量
            
        Returns:
            数据列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        return await self.error_handler.handle(
            "list",
            lambda: self._list_internal(filters, limit)
        )
    
    async def _list_internal(self, filters: Dict[str, Any], limit: Optional[int]) -> List[Dict[str, Any]]:
        """内部列表实现"""
        # 调用后端列表
        storage_results = await self.backend.list(filters, limit)
        
        # 转换为领域格式
        domain_results = []
        for storage_data in storage_results:
            try:
                domain_data = self.transformer.from_storage_format(storage_data)
                domain_results.append(domain_data)
            except Exception as e:
                self.logger.warning(f"转换数据失败，跳过: {e}")
                continue
        
        self.logger.debug(f"列表查询成功，返回 {len(domain_results)} 条记录")
        return domain_results
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数数据
        
        Args:
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
            
        Raises:
            StorageError: 计数失败时抛出
        """
        return await self.error_handler.handle(
            "count",
            lambda: self._count_internal(filters)
        )
    
    async def _count_internal(self, filters: Dict[str, Any]) -> int:
        """内部计数实现"""
        # 调用后端计数
        return await self.backend.count(filters)
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存
        
        Args:
            data_list: 数据列表
            
        Returns:
            保存的数据ID列表
            
        Raises:
            StorageError: 批量保存失败时抛出
        """
        return await self.error_handler.handle(
            "batch_save",
            lambda: self._batch_save_internal(data_list)
        )
    
    async def _batch_save_internal(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """内部批量保存实现"""
        # 转换为存储格式
        storage_data_list = []
        for data in data_list:
            try:
                storage_data = self.transformer.to_storage_format(data)
                storage_data_list.append(storage_data)
            except Exception as e:
                self.logger.warning(f"转换数据失败，跳过: {e}")
                continue
        
        # 调用后端批量保存
        result_ids = await self.backend.batch_save(storage_data_list)
        
        self.logger.debug(f"批量保存成功，保存了 {len(result_ids)} 条记录")
        return result_ids
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除
        
        Args:
            ids: 数据ID列表
            
        Returns:
            删除的数据数量
            
        Raises:
            StorageError: 批量删除失败时抛出
        """
        return await self.error_handler.handle(
            "batch_delete",
            lambda: self._batch_delete_internal(ids)
        )
    
    async def _batch_delete_internal(self, ids: List[str]) -> int:
        """内部批量删除实现"""
        # 调用后端批量删除
        count = await self.backend.batch_delete(ids)
        
        self.logger.debug(f"批量删除成功，删除了 {count} 条记录")
        return count
    
    def stream_list(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列出数据
        
        Args:
            filters: 过滤条件
            batch_size: 批次大小
            
        Yields:
            数据批次列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        return self._stream_list_internal(filters, batch_size)
    
    async def _stream_list_internal(
        self, 
        filters: Dict[str, Any], 
        batch_size: int
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """内部流式列表实现"""
        # 获取后端流式迭代器
        async for storage_batch in self.backend.stream_list(filters, batch_size):
            # 转换为领域格式
            domain_batch = []
            for storage_data in storage_batch:
                try:
                    domain_data = self.transformer.from_storage_format(storage_data)
                    domain_batch.append(domain_data)
                except Exception as e:
                    self.logger.warning(f"转换数据失败，跳过: {e}")
                    continue
            
            if domain_batch:  # 只返回非空批次
                yield domain_batch
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
            
        Raises:
            StorageError: 健康检查失败时抛出
        """
        return await self.error_handler.handle(
            "health_check",
            lambda: self._health_check_internal()
        )
    
    async def _health_check_internal(self) -> Dict[str, Any]:
        """内部健康检查实现"""
        # 调用后端健康检查
        health_info = await self.backend.health_check()
        
        # 添加适配器信息
        health_info["adapter"] = {
            "type": self.__class__.__name__,
            "backend_type": self.backend.__class__.__name__,
            "transformer_type": self.transformer.__class__.__name__,
        }
        
        return health_info