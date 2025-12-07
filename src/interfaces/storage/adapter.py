"""存储适配器接口定义

定义存储适配器的统一接口，作为Repository层和Storage Backend层之间的桥梁。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator


class IStorageAdapter(ABC):
    """存储适配器接口
    
    提供Repository层和Storage Backend层之间的统一抽象，
    封装存储细节，提供统一的数据访问接口。
    """
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据
        
        Args:
            data: 要保存的数据字典
            
        Returns:
            保存的数据ID
            
        Raises:
            StorageError: 保存失败时抛出
        """
        pass
    
    @abstractmethod
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，如果不存在则返回None
            
        Raises:
            StorageError: 加载失败时抛出
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
            
        Raises:
            StorageError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            
        Returns:
            数据是否存在
            
        Raises:
            StorageError: 检查失败时抛出
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数数据
        
        Args:
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
            
        Raises:
            StorageError: 计数失败时抛出
        """
        pass
    
    @abstractmethod
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存
        
        Args:
            data_list: 数据列表
            
        Returns:
            保存的数据ID列表
            
        Raises:
            StorageError: 批量保存失败时抛出
        """
        pass
    
    @abstractmethod
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除
        
        Args:
            ids: 数据ID列表
            
        Returns:
            删除的数据数量
            
        Raises:
            StorageError: 批量删除失败时抛出
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
            
        Raises:
            StorageError: 健康检查失败时抛出
        """
        pass


class IDataTransformer(ABC):
    """数据转换器接口
    
    定义领域对象和存储格式之间的转换接口。
    """
    
    @abstractmethod
    def to_storage_format(self, domain_object: Any) -> Dict[str, Any]:
        """领域对象转存储格式
        
        Args:
            domain_object: 领域对象
            
        Returns:
            存储格式数据
        """
        pass
    
    @abstractmethod
    def from_storage_format(self, storage_data: Dict[str, Any]) -> Any:
        """存储格式转领域对象
        
        Args:
            storage_data: 存储格式数据
            
        Returns:
            领域对象
        """
        pass


class IStorageErrorHandler(ABC):
    """存储错误处理器接口
    
    定义统一的错误处理接口。
    """
    
    @abstractmethod
    async def handle(self, operation: str, operation_func) -> Any:
        """处理操作并统一异常
        
        Args:
            operation: 操作名称
            operation_func: 操作函数
            
        Returns:
            操作结果
            
        Raises:
            StorageError: 操作失败时抛出
        """
        pass


class IStorageConfigManager(ABC):
    """存储配置管理器接口
    
    定义统一的配置管理接口。
    """
    
    @abstractmethod
    def get_backend_config(self, backend_type: str) -> Dict[str, Any]:
        """获取后端配置
        
        Args:
            backend_type: 后端类型
            
        Returns:
            后端配置字典
        """
        pass
    
    @abstractmethod
    def get_repository_config(self, repo_type: str) -> Dict[str, Any]:
        """获取仓库配置
        
        Args:
            repo_type: 仓库类型
            
        Returns:
            仓库配置字典
        """
        pass
    
    @abstractmethod
    def update_config(self, config_path: str, config_value: Any) -> None:
        """更新配置
        
        Args:
            config_path: 配置路径
            config_value: 配置值
        """
        pass