"""
统一存储领域接口

定义了所有存储操作的基本接口，包括CRUD操作、查询操作、
高级操作和模块特定操作。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncIterator
from datetime import datetime


class IUnifiedStorage(ABC):
    """统一存储接口 - 所有模块的基础"""
    
    # 基础CRUD操作
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据并返回ID
        
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
        """根据ID加载数据
        
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
            StorageNotFoundError: 数据不存在时抛出
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
    
    # 查询操作
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
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询
        
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
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数
        
        Args:
            filters: 过滤条件
            
        Returns:
            符合条件的数据数量
            
        Raises:
            StorageError: 计数失败时抛出
        """
        pass
    
    # 高级操作
    @abstractmethod
    async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务
        
        Args:
            operations: 操作列表，每个操作包含type和data字段
            
        Returns:
            事务是否执行成功
            
        Raises:
            StorageTransactionError: 事务失败时抛出
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
    
    # 模块特定操作
    @abstractmethod
    async def get_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            数据列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """根据线程ID获取数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            数据列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        pass
    
    @abstractmethod
    async def cleanup_old_data(self, retention_days: int) -> int:
        """清理旧数据
        
        Args:
            retention_days: 保留天数
            
        Returns:
            清理的数据数量
            
        Raises:
            StorageError: 清理失败时抛出
        """
        pass
    
    # 流式操作
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
    
    # 健康检查
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
            
        Raises:
            StorageConnectionError: 连接失败时抛出
        """
        pass
    
    # 生命周期管理
    async def close(self) -> None:
        """关闭存储连接
        
        默认实现（可选）
        """
        pass


class IStorageFactory(ABC):
    """存储工厂接口"""
    
    @abstractmethod
    def create_storage(self, storage_type: str, config: Dict[str, Any]) -> IUnifiedStorage:
        """创建存储实例
        
        Args:
            storage_type: 存储类型
            config: 存储配置
            
        Returns:
            存储实例
            
        Raises:
            StorageError: 创建失败时抛出
        """
        pass
    
    @abstractmethod
    def register_storage(self, storage_type: str, storage_class: type) -> None:
        """注册存储类型
        
        Args:
            storage_type: 存储类型名称
            storage_class: 存储类
            
        Raises:
            StorageError: 注册失败时抛出
        """
        pass
    
    @abstractmethod
    def get_available_types(self) -> List[str]:
        """获取可用的存储类型
        
        Returns:
            存储类型列表
        """
        pass
    
    @abstractmethod
    def is_type_available(self, storage_type: str) -> bool:
        """检查存储类型是否可用
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            是否可用
        """
        pass