"""
存储基础设施接口

定义了存储后端的底层接口，用于实现具体的存储后端。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime


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


class IStorageSerializer(ABC):
    """存储序列化接口
    
    定义了数据序列化和反序列化的接口。
    """
    
    @abstractmethod
    def serialize(self, data: Any) -> str:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            
        Returns:
            序列化后的字符串
            
        Raises:
            StorageError: 序列化失败时抛出
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: str) -> Any:
        """反序列化数据
        
        Args:
            data: 要反序列化的字符串
            
        Returns:
            反序列化后的数据
            
        Raises:
            StorageError: 反序列化失败时抛出
        """
        pass


class IStorageCache(ABC):
    """存储缓存接口
    
    定义了存储缓存的接口。
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass


class IStorageMetrics(ABC):
    """存储指标接口
    
    定义了存储性能指标收集的接口。
    """
    
    @abstractmethod
    async def record_operation(
        self, 
        operation: str, 
        duration: float, 
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作指标
        
        Args:
            operation: 操作类型
            duration: 操作耗时（秒）
            success: 是否成功
            metadata: 元数据
        """
        pass
    
    @abstractmethod
    async def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取指标数据
        
        Args:
            operation: 操作类型，None表示获取所有
            
        Returns:
            指标数据
        """
        pass
    
    @abstractmethod
    async def reset_metrics(self) -> None:
        """重置指标数据"""
        pass