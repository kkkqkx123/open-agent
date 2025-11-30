"""
通用存储接口定义

定义了存储系统的核心接口，包括存储后端、仓储和管理器接口。
这些接口为整个存储系统提供了统一的抽象层。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator, Union
from datetime import datetime

from .models import StorageConfig, StorageOperation, StorageResult


class IStorageBackend(ABC):
    """通用存储后端接口
    
    定义了存储后端的基本操作，所有具体的存储后端都应该实现这个接口。
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接存储后端
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开存储后端连接
        
        Returns:
            是否断开成功
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """检查是否已连接
        
        Returns:
            是否已连接
        """
        pass
    
    @abstractmethod
    async def save(self, key: str, data: Dict[str, Any]) -> bool:
        """保存数据
        
        Args:
            key: 数据键
            data: 要保存的数据
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            key: 数据键
            
        Returns:
            加载的数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除数据
        
        Args:
            key: 数据键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查数据是否存在
        
        Args:
            key: 数据键
            
        Returns:
            数据是否存在
        """
        pass
    
    @abstractmethod
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """获取所有键
        
        Args:
            pattern: 键模式过滤
            
        Returns:
            键列表
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康检查结果
        """
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        pass


class IStorageRepository(ABC):
    """通用存储仓储接口
    
    定义了仓储模式的基本操作，提供更高级的数据访问抽象。
    """
    
    @abstractmethod
    async def save(self, entity: Any) -> bool:
        """保存实体
        
        Args:
            entity: 要保存的实体
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Optional[Any]:
        """根据ID查找实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            找到的实体，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Any]:
        """根据条件查找实体
        
        Args:
            criteria: 查询条件
            
        Returns:
            符合条件的实体列表
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Any]:
        """查找所有实体
        
        Returns:
            所有实体列表
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """更新实体
        
        Args:
            entity_id: 实体ID
            updates: 更新数据
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """统计实体数量
        
        Args:
            criteria: 统计条件
            
        Returns:
            实体数量
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """检查实体是否存在
        
        Args:
            entity_id: 实体ID
            
        Returns:
            实体是否存在
        """
        pass


class IStorageManager(ABC):
    """通用存储管理器接口
    
    定义了存储管理器的高级操作，包括后端管理和操作编排。
    """
    
    @abstractmethod
    async def register_backend(self, name: str, backend: IStorageBackend) -> bool:
        """注册存储后端
        
        Args:
            name: 后端名称
            backend: 存储后端实例
            
        Returns:
            是否注册成功
        """
        pass
    
    @abstractmethod
    async def unregister_backend(self, name: str) -> bool:
        """注销存储后端
        
        Args:
            name: 后端名称
            
        Returns:
            是否注销成功
        """
        pass
    
    @abstractmethod
    async def get_backend(self, name: Optional[str] = None) -> Optional[IStorageBackend]:
        """获取存储后端
        
        Args:
            name: 后端名称，如果为None则返回默认后端
            
        Returns:
            存储后端实例
        """
        pass
    
    @abstractmethod
    async def list_backends(self) -> List[Dict[str, Any]]:
        """列出所有已注册的后端
        
        Returns:
            后端信息列表
        """
        pass
    
    @abstractmethod
    async def set_default_backend(self, name: str) -> bool:
        """设置默认后端
        
        Args:
            name: 后端名称
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def execute_operation(self, operation: StorageOperation) -> StorageResult:
        """执行存储操作
        
        Args:
            operation: 存储操作
            
        Returns:
            操作结果
        """
        pass
    
    @abstractmethod
    async def execute_batch_operations(self, operations: List[StorageOperation]) -> List[StorageResult]:
        """批量执行存储操作
        
        Args:
            operations: 存储操作列表
            
        Returns:
            操作结果列表
        """
        pass


class IStorageMonitoring(ABC):
    """存储监控接口
    
    定义了存储系统的监控功能。
    """
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态
        
        Returns:
            健康状态信息
        """
        pass
    
    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            性能指标信息
        """
        pass
    
    @abstractmethod
    async def get_usage_statistics(self) -> Dict[str, Any]:
        """获取使用统计
        
        Returns:
            使用统计信息
        """
        pass
    
    @abstractmethod
    async def start_monitoring(self) -> bool:
        """开始监控
        
        Returns:
            是否开始成功
        """
        pass
    
    @abstractmethod
    async def stop_monitoring(self) -> bool:
        """停止监控
        
        Returns:
            是否停止成功
        """
        pass


class IStorageMigration(ABC):
    """存储迁移接口
    
    定义了存储系统的迁移功能。
    """
    
    @abstractmethod
    async def create_migration(self, name: str, description: str) -> str:
        """创建迁移
        
        Args:
            name: 迁移名称
            description: 迁移描述
            
        Returns:
            迁移ID
        """
        pass
    
    @abstractmethod
    async def apply_migration(self, migration_id: str) -> bool:
        """应用迁移
        
        Args:
            migration_id: 迁移ID
            
        Returns:
            是否应用成功
        """
        pass
    
    @abstractmethod
    async def rollback_migration(self, migration_id: str) -> bool:
        """回滚迁移
        
        Args:
            migration_id: 迁移ID
            
        Returns:
            是否回滚成功
        """
        pass
    
    @abstractmethod
    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史
        
        Returns:
            迁移历史列表
        """
        pass
    
    @abstractmethod
    async def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """获取待执行的迁移
        
        Returns:
            待执行迁移列表
        """
        pass


class IStorageTransaction(ABC):
    """存储事务接口
    
    定义了存储系统的事务功能。
    """
    
    @abstractmethod
    async def begin(self) -> str:
        """开始事务
        
        Returns:
            事务ID
        """
        pass
    
    @abstractmethod
    async def commit(self, transaction_id: str) -> bool:
        """提交事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否提交成功
        """
        pass
    
    @abstractmethod
    async def rollback(self, transaction_id: str) -> bool:
        """回滚事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否回滚成功
        """
        pass
    
    @abstractmethod
    async def add_operation(self, transaction_id: str, operation: StorageOperation) -> bool:
        """添加操作到事务
        
        Args:
            transaction_id: 事务ID
            operation: 存储操作
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """获取事务状态
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            事务状态信息
        """
        pass