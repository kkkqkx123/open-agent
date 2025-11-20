"""存储后端接口定义

定义存储系统的核心接口，包括后端、序列化器、缓存和指标接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator


class IStorageBackend(ABC):
    """存储后端接口
    
    定义了存储后端的底层操作接口，由具体的存储实现继承。
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到存储后端
        
        Raises:
            StorageConnectionError: 连接失败时抛出
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """检查是否已连接
        
        Returns:
            是否已连接
        """
        pass
    
    @abstractmethod
    async def save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现
        
        Args:
            data: 要保存的数据
            
        Returns:
            保存的数据ID
            
        Raises:
            StorageError: 保存失败时抛出
        """
        pass
    
    @abstractmethod
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，如果不存在则返回None
            
        Raises:
            StorageError: 加载失败时抛出
        """
        pass
    
    @abstractmethod
    async def update_impl(self, id: str, updates: Dict[str, Any]) -> bool:
        """实际更新实现
        
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
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
            
        Raises:
            StorageError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def list_impl(
        self, 
        filters: Dict[str, Any], 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """实际列表实现
        
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
    async def query_impl(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """实际查询实现
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        pass
    
    @abstractmethod
    async def exists_impl(self, id: str) -> bool:
        """实际存在检查实现
        
        Args:
            id: 数据ID
            
        Returns:
            数据是否存在
            
        Raises:
            StorageError: 检查失败时抛出
        """
        pass
    
    @abstractmethod
    async def count_impl(self, filters: Dict[str, Any]) -> int:
        """实际计数实现
        
        Args:
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
            
        Raises:
            StorageError: 计数失败时抛出
        """
        pass
    
    @abstractmethod
    async def transaction_impl(self, operations: List[Dict[str, Any]]) -> bool:
        """实际事务实现
        
        Args:
            operations: 操作列表
            
        Returns:
            事务是否执行成功
            
        Raises:
            StorageTransactionError: 事务失败时抛出
        """
        pass
    
    @abstractmethod
    async def batch_save_impl(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """实际批量保存实现
        
        Args:
            data_list: 数据列表
            
        Returns:
            保存的数据ID列表
            
        Raises:
            StorageError: 批量保存失败时抛出
        """
        pass
    
    @abstractmethod
    async def batch_delete_impl(self, ids: List[str]) -> int:
        """实际批量删除实现
        
        Args:
            ids: 数据ID列表
            
        Returns:
            删除的数据数量
            
        Raises:
            StorageError: 批量删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_by_session_impl(self, session_id: str) -> List[Dict[str, Any]]:
        """实际根据会话ID获取数据实现
        
        Args:
            session_id: 会话ID
            
        Returns:
            数据列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_by_thread_impl(self, thread_id: str) -> List[Dict[str, Any]]:
        """实际根据线程ID获取数据实现
        
        Args:
            thread_id: 线程ID
            
        Returns:
            数据列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        pass
    
    @abstractmethod
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现
        
        Args:
            retention_days: 保留天数
            
        Returns:
            清理的数据数量
            
        Raises:
            StorageError: 清理失败时抛出
        """
        pass
    
    @abstractmethod
    def stream_list_impl(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """实际流式列表实现
        
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
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现
        
        Returns:
            健康状态信息
            
        Raises:
            StorageConnectionError: 连接失败时抛出
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> None:
        """开始事务
        
        Raises:
            StorageTransactionError: 启动事务失败时抛出
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self) -> None:
        """提交事务
        
        Raises:
            StorageTransactionError: 提交事务失败时抛出
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self) -> None:
        """回滚事务
        
        Raises:
            StorageTransactionError: 回滚事务失败时抛出
        """
        pass