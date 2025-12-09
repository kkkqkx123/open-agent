"""状态存储接口定义

定义状态存储相关的接口，包括历史记录和快照管理。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from .base import IStorage
from ..state.entities import IStateSnapshot, IStateHistoryEntry


class IStateStorageAdapter(ABC):
    """状态存储适配器接口
    
    专注于状态特有的存储功能，如历史记录和快照管理。
    统一采用异步接口设计。
    
    职责：
    - 提供状态历史记录的存储和检索
    - 管理状态快照的创建和恢复
    - 支持事务性操作
    - 提供存储统计和健康检查
    
    使用示例：
        ```python
        # 创建存储适配器
        adapter = MyStateStorageAdapter()
        
        # 保存历史记录
        await adapter.save_history_entry(history_entry)
        
        # 获取历史记录
        entries = await adapter.get_history_entries("agent_123")
        ```
    
    注意事项：
    - 所有操作都是异步的
    - 应该处理并发访问和事务管理
    - 需要考虑存储容量和性能优化
    
    相关接口：
    - IStorage: 通用存储接口
    - IStateHistoryEntry: 状态历史记录接口
    - IStateSnapshot: 状态快照接口
    
    版本历史：
    - v1.0.0: 初始版本
    """
    
    @abstractmethod
    async def save_history_entry(self, entry: IStateHistoryEntry) -> bool:
        """保存历史记录条目
        
        Args:
            entry: 历史记录条目
            
        Returns:
            保存成功返回True，失败返回False
            
        Examples:
            ```python
            # 保存历史记录
            entry = MyHistoryEntry(...)
            success = await adapter.save_history_entry(entry)
            if success:
                print("History entry saved")
            ```
        """
        pass
    
    @abstractmethod
    async def get_history_entries(self, agent_id: str, limit: int = 100) -> Sequence[IStateHistoryEntry]:
        """获取历史记录条目
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            历史记录条目列表
            
        Examples:
            ```python
            # 获取代理的历史记录
            entries = await adapter.get_history_entries("agent_123", limit=50)
            for entry in entries:
                print(f"Entry {entry.history_id}: {entry.action}")
            ```
        """
        pass
    
    @abstractmethod
    async def delete_history_entry(self, history_id: str) -> bool:
        """删除历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
            
        Examples:
            ```python
            # 删除特定历史记录
            if await adapter.delete_history_entry("history_123"):
                print("History entry deleted")
            ```
        """
        pass
    
    @abstractmethod
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否清空成功
            
        Examples:
            ```python
            # 清空代理的所有历史记录
            if await adapter.clear_agent_history("agent_123"):
                print("Agent history cleared")
            ```
        """
        pass
    
    @abstractmethod
    async def save_snapshot(self, snapshot: IStateSnapshot) -> bool:
        """保存状态快照
        
        Args:
            snapshot: 状态快照条目
            
        Returns:
            保存成功返回True，失败返回False
            
        Examples:
            ```python
            # 保存状态快照
            snapshot = MyStateSnapshot(...)
            success = await adapter.save_snapshot(snapshot)
            if success:
                print("Snapshot saved")
            ```
        """
        pass
    
    @abstractmethod
    async def load_snapshot(self, snapshot_id: str) -> Optional[IStateSnapshot]:
        """加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果未找到则返回None
            
        Examples:
            ```python
            # 加载快照
            snapshot = await adapter.load_snapshot("snapshot_123")
            if snapshot:
                print(f"Loaded snapshot: {snapshot.snapshot_name}")
            ```
        """
        pass
    
    @abstractmethod
    async def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> Sequence[IStateSnapshot]:
        """获取指定代理的快照列表
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            快照列表
            
        Examples:
            ```python
            # 获取代理的快照列表
            snapshots = await adapter.get_snapshots_by_agent("agent_123")
            for snapshot in snapshots:
                print(f"Snapshot: {snapshot.snapshot_name}")
            ```
        """
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否删除成功
            
        Examples:
            ```python
            # 删除快照
            if await adapter.delete_snapshot("snapshot_123"):
                print("Snapshot deleted")
            ```
        """
        pass
    
    @abstractmethod
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息
        
        Returns:
            统计信息字典
            
        Examples:
            ```python
            stats = await adapter.get_history_statistics()
            print(f"Total history entries: {stats['total_entries']}")
            ```
        """
        pass
    
    @abstractmethod
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息
        
        Returns:
            统计信息字典
            
        Examples:
            ```python
            stats = await adapter.get_snapshot_statistics()
            print(f"Total snapshots: {stats['total_snapshots']}")
            ```
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> None:
        """开始事务
        
        Examples:
            ```python
            # 开始事务
            await adapter.begin_transaction()
            try:
                # 执行多个操作
                await adapter.save_history_entry(entry1)
                await adapter.save_snapshot(snapshot1)
                await adapter.commit_transaction()
            except Exception:
                await adapter.rollback_transaction()
            ```
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self) -> None:
        """提交事务
        
        Examples:
            ```python
            # 提交事务
            await adapter.commit_transaction()
            ```
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self) -> None:
        """回滚事务
        
        Examples:
            ```python
            # 回滚事务
            await adapter.rollback_transaction()
            ```
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭存储连接
        
        Examples:
            ```python
            # 关闭连接
            await adapter.close()
            ```
        """
        pass

    async def get_unified_storage(self) -> Optional[IStorage]:
        """获取通用存储接口实例（可选功能）
        
        Returns:
            通用存储接口实例，如果不可用则返回None
            
        Examples:
            ```python
            # 获取通用存储接口
            storage = await adapter.get_unified_storage()
            if storage:
                # 使用通用存储功能
                data = await storage.get("key")
            ```
        """
        # 默认返回None，表示不支持
        return None
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            存储是否健康
            
        Examples:
            ```python
            # 检查存储健康状态
            if await adapter.health_check():
                print("Storage is healthy")
            else:
                print("Storage has issues")
            ```
        """
        pass

    @property
    @abstractmethod
    def _backend(self) -> Any:
        """存储后端"""
        pass

    @_backend.setter
    @abstractmethod
    def _backend(self, value: Any) -> None:
        """设置存储后端"""
        pass

    @abstractmethod
    async def backup_database(self, backup_path: Optional[str] = None) -> str:
        """备份数据库
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
            
        Examples:
            ```python
            # 备份数据库
            backup_file = await adapter.backup_database("/path/to/backup")
            print(f"Database backed up to: {backup_file}")
            ```
        """
        pass

    @abstractmethod
    async def restore_database(self, backup_path: str) -> bool:
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
            
        Examples:
            ```python
            # 恢复数据库
            if await adapter.restore_database("/path/to/backup"):
                print("Database restored successfully")
            ```
        """
        pass

    @abstractmethod
    async def backup_storage(self, backup_path: Optional[str] = None) -> str:
        """备份存储
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
            
        Examples:
            ```python
            # 备份存储
            backup_file = await adapter.backup_storage("/path/to/backup")
            print(f"Storage backed up to: {backup_file}")
            ```
        """
        pass

    @abstractmethod
    async def restore_storage(self, backup_path: str) -> bool:
        """恢复存储
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
            
        Examples:
            ```python
            # 恢复存储
            if await adapter.restore_storage("/path/to/backup"):
                print("Storage restored successfully")
            ```
        """
        pass


class IStorageAdapterFactory(ABC):
    """存储适配器工厂接口
    
    定义存储适配器的创建接口。
    
    职责：
    - 创建不同类型的存储适配器
    - 验证配置参数
    - 管理支持的存储类型
    
    使用示例：
        ```python
        # 创建工厂
        factory = MyStorageAdapterFactory()
        
        # 创建适配器
        config = {"path": "/data/storage.db"}
        adapter = await factory.create_adapter("sqlite", config)
        ```
    
    版本历史：
    - v1.0.0: 初始版本
    """
    
    @abstractmethod
    async def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建存储适配器
        
        Args:
            storage_type: 存储类型（memory, sqlite, file等）
            config: 配置参数
            
        Returns:
            存储适配器实例
            
        Raises:
            ValueError: 当存储类型不支持时
            RuntimeError: 当创建失败时
            
        Examples:
            ```python
            # 创建SQLite适配器
            config = {"path": "states.db", "timeout": 30}
            adapter = await factory.create_adapter("sqlite", config)
            
            # 创建内存适配器
            adapter = await factory.create_adapter("memory", {})
            ```
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的存储类型
        
        Returns:
            支持的存储类型列表
            
        Examples:
            ```python
            types = factory.get_supported_types()
            print(f"Supported types: {types}")
            # 输出: ['memory', 'sqlite', 'file']
            ```
        """
        pass
    
    @abstractmethod
    async def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """验证配置参数
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            验证错误列表，空列表表示验证通过
            
        Examples:
            ```python
            # 验证配置
            config = {"path": "states.db"}
            errors = await factory.validate_config("sqlite", config)
            
            if errors:
                print(f"Config errors: {errors}")
            else:
                print("Config is valid")
            ```
        """
        pass


class IStorageMigration(ABC):
    """存储迁移接口
    
    定义存储数据的迁移功能。
    
    职责：
    - 在不同存储之间迁移数据
    - 验证迁移结果
    - 提供迁移统计信息
    
    使用示例：
        ```python
        # 创建迁移器
        migration = MyStorageMigration()
        
        # 执行迁移
        result = await migration.migrate_from(source_adapter, target_adapter)
        print(f"Migrated {result['total_items']} items")
        ```
    
    版本历史：
    - v1.0.0: 初始版本
    """
    
    @abstractmethod
    async def migrate_from(self, source_adapter: IStateStorageAdapter, 
                          target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
        """从源存储迁移到目标存储
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            迁移结果统计
            
        Examples:
            ```python
            # 从内存存储迁移到SQLite
            result = await migration.migrate_from(memory_adapter, sqlite_adapter)
            print(f"Migrated {result['history_entries']} history entries")
            print(f"Migrated {result['snapshots']} snapshots")
            ```
        """
        pass
    
    @abstractmethod
    async def validate_migration(self, source_adapter: IStateStorageAdapter,
                                target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
        """验证迁移结果
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            验证结果
            
        Examples:
            ```python
            # 验证迁移结果
            result = await migration.validate_migration(source_adapter, target_adapter)
            if result['is_valid']:
                print("Migration validation passed")
            else:
                print(f"Validation errors: {result['errors']}")
            ```
        """
        pass