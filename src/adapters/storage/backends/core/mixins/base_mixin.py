"""基础存储混入类

提供通用的存储混入功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from src.interfaces.storage import IStorageProvider
from ..exceptions import StorageBackendError


logger = get_logger(__name__)


class BaseStorageMixin(ABC):
    """基础存储混入类
    
    提供通用的存储混入功能，作为所有混入类的基类。
    """
    
    def __init__(self, provider: IStorageProvider, table_name: str):
        """初始化基础存储混入
        
        Args:
            provider: 存储提供者实例
            table_name: 表名
        """
        self._provider = provider
        self._table_name = table_name
    
    @abstractmethod
    def _prepare_data(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备数据用于存储
        
        Args:
            id: 数据ID
            data: 原始数据
            
        Returns:
            存储格式的数据
        """
        pass
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            id: 数据ID
            updates: 更新的字段字典
            
        Returns:
            是否更新成功
        """
        try:
            # 加载现有数据
            existing_data = await self.load(id)
            
            if existing_data is None:
                logger.warning(f"Data not found for update: {id}")
                return False
            
            # 合并更新数据
            existing_data.update(updates)
            
            # 保存更新后的数据
            return await self.save(id, existing_data)
            
        except Exception as e:
            logger.error(f"Failed to update data {id}: {e}")
            raise StorageBackendError(f"Failed to update data: {e}")
    
    @abstractmethod
    def _extract_data(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """从存储数据提取业务数据
        
        Args:
            storage_data: 存储格式的数据
            
        Returns:
            业务格式的数据
        """
        pass
    
    @abstractmethod
    def _validate_data(self, data: Dict[str, Any]) -> None:
        """验证数据
        
        Args:
            data: 要验证的数据
            
        Raises:
            StorageBackendError: 数据无效时抛出
        """
        pass
    
    async def save(self, id: str, data: Dict[str, Any]) -> bool:
        """保存数据
        
        Args:
            id: 数据ID
            data: 数据字典
            
        Returns:
            是否保存成功
        """
        try:
            # 验证数据
            self._validate_data(data)
            
            # 准备数据
            prepared_data = self._prepare_data(id, data)
            
            # 保存到存储
            result_id = await self._provider.save(self._table_name, prepared_data)
            
            logger.debug(f"Data saved to {self._table_name}: {id}")
            return result_id == id
            
        except Exception as e:
            logger.error(f"Failed to save data {id} to {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to save data: {e}")
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，不存在返回None
        """
        try:
            # 从存储加载
            storage_data = await self._provider.load(self._table_name, id)
            
            if storage_data is None:
                return None
            
            # 提取业务数据
            data = self._extract_data(storage_data)
            
            logger.debug(f"Data loaded from {self._table_name}: {id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load data {id} from {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to load data: {e}")
    
    async def delete(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        try:
            result = await self._provider.delete(self._table_name, id)
            
            if result:
                logger.debug(f"Data deleted from {self._table_name}: {id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete data {id} from {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to delete data: {e}")
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            
        Returns:
            是否存在
        """
        try:
            return await self._provider.exists(self._table_name, id)
        except Exception as e:
            logger.error(f"Failed to check existence of {id} in {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to check existence: {e}")
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据
        
        Args:
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            数据列表
        """
        try:
            # 从存储查询
            storage_results = await self._provider.list(self._table_name, filters, limit)
            
            # 提取业务数据
            results = []
            for storage_data in storage_results:
                try:
                    data = self._extract_data(storage_data)
                    results.append(data)
                except Exception as e:
                    logger.warning(f"Failed to extract data: {e}")
                    continue
            
            logger.debug(f"Listed {len(results)} records from {self._table_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to list data from {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to list data: {e}")
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数
        
        Args:
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
        """
        try:
            return await self._provider.count(self._table_name, filters)
        except Exception as e:
            logger.error(f"Failed to count data in {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to count data: {e}")
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存数据
        
        Args:
            data_list: 数据列表
            
        Returns:
            数据ID列表
        """
        try:
            result_ids = []
            
            for data in data_list:
                # 确保有ID字段
                if "id" not in data:
                    import time
                    data["id"] = str(time.time()) + str(id(data))
                
                # 验证和准备数据
                self._validate_data(data)
                prepared_data = self._prepare_data(data["id"], data)
                
                # 保存到存储
                result_id = await self._provider.save(self._table_name, prepared_data)
                result_ids.append(result_id)
            
            logger.debug(f"Batch saved {len(result_ids)} records to {self._table_name}")
            return result_ids
            
        except Exception as e:
            logger.error(f"Failed to batch save data to {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to batch save data: {e}")
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除数据
        
        Args:
            ids: 数据ID列表
            
        Returns:
            删除的数量
        """
        try:
            count = 0
            
            for id in ids:
                if await self._provider.delete(self._table_name, id):
                    count += 1
            
            logger.debug(f"Batch deleted {count} records from {self._table_name}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to batch delete data from {self._table_name}: {e}")
            raise StorageBackendError(f"Failed to batch delete data: {e}")