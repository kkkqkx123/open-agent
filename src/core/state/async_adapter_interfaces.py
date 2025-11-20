"""异步状态存储适配器接口定义

定义状态存储适配器的异步接口，支持历史记录和快照的存储操作。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from .entities import StateSnapshot, StateHistoryEntry


class IAsyncStateStorageAdapter(ABC):
    """异步状态存储适配器接口
    
    定义状态存储的统一异步接口，支持历史记录和快照的存储操作。
    """
    
    @abstractmethod
    async def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """异步保存历史记录条目
        
        Args:
            entry: 历史记录条目
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def get_history_entries(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """异步获取历史记录条目
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            历史记录条目列表
        """
        pass
    
    @abstractmethod
    async def delete_history_entry(self, history_id: str) -> bool:
        """异步删除历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def clear_agent_history(self, agent_id: str) -> bool:
        """异步清空代理的历史记录
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否清空成功
        """
        pass
    
    @abstractmethod
    async def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """异步保存状态快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """异步加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """异步获取指定代理的快照列表
        
        Args:
            agent_id: 代理ID
            limit: 返回快照数限制
            
        Returns:
            快照列表
        """
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """异步删除状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_history_statistics(self) -> Dict[str, Any]:
        """异步获取历史记录统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """异步获取快照统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> None:
        """异步开始事务"""
        pass
    
    @abstractmethod
    async def commit_transaction(self) -> None:
        """异步提交事务"""
        pass
    
    @abstractmethod
    async def rollback_transaction(self) -> None:
        """异步回滚事务"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """异步关闭存储连接"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """异步健康检查
        
        Returns:
            存储是否健康
        """
        pass


class IAsyncStorageAdapterFactory(ABC):
    """异步存储适配器工厂接口
    
    定义异步存储适配器的创建接口。
    """
    
    @abstractmethod
    async def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IAsyncStateStorageAdapter:
        """异步创建存储适配器
        
        Args:
            storage_type: 存储类型（memory, sqlite, file等）
            config: 配置参数
            
        Returns:
            存储适配器实例
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的存储类型
        
        Returns:
            支持的存储类型列表
        """
        pass
    
    @abstractmethod
    async def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """异步验证配置参数
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        pass


class IAsyncStorageMigration(ABC):
    """异步存储迁移接口
    
    定义存储数据的异步迁移功能。
    """
    
    @abstractmethod
    async def migrate_from(self, source_adapter: IAsyncStateStorageAdapter, 
                          target_adapter: IAsyncStateStorageAdapter) -> Dict[str, Any]:
        """异步从源存储迁移到目标存储
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            迁移结果统计
        """
        pass
    
    @abstractmethod
    async def validate_migration(self, source_adapter: IAsyncStateStorageAdapter,
                                target_adapter: IAsyncStateStorageAdapter) -> Dict[str, Any]:
        """异步验证迁移结果
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            验证结果
        """
        pass