"""状态存储适配器接口定义

定义状态存储适配器的核心接口，包括存储适配器、工厂和迁移接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from ..entities import StateSnapshot, StateHistoryEntry


class IStateStorageAdapter(ABC):
    """状态存储适配器接口
    
    定义状态存储的统一接口，支持历史记录和快照的存储操作。
    """
    
    @abstractmethod
    def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """保存历史记录条目
        
        Args:
            entry: 历史记录条目
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    def get_history_entries(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取历史记录条目
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            历史记录条目列表
        """
        pass
    
    @abstractmethod
    def delete_history_entry(self, history_id: str) -> bool:
        """删除历史记录条目
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否清空成功
        """
        pass
    
    @abstractmethod
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存状态快照
        
        Args:
            snapshot: 状态快照
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态快照，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定代理的快照列表
        
        Args:
            agent_id: 代理ID
            limit: 返回快照数限制
            
        Returns:
            快照列表
        """
        pass
    
    @abstractmethod
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """开始事务"""
        pass
    
    @abstractmethod
    def commit_transaction(self) -> None:
        """提交事务"""
        pass
    
    @abstractmethod
    def rollback_transaction(self) -> None:
        """回滚事务"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭存储连接"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """健康检查
        
        Returns:
            存储是否健康
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
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """备份数据库
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        pass

    @abstractmethod
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        pass

    @abstractmethod
    def backup_storage(self, backup_path: Optional[str] = None) -> str:
        """备份存储
        
        Args:
            backup_path: 备份路径（可选）
            
        Returns:
            备份文件路径
        """
        pass

    @abstractmethod
    def restore_storage(self, backup_path: str) -> bool:
        """恢复存储
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        pass


class IStorageAdapterFactory(ABC):
    """存储适配器工厂接口
    
    定义存储适配器的创建接口。
    """
    
    @abstractmethod
    def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建存储适配器
        
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
    def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """验证配置参数
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            验证错误列表，空列表表示验证通过
        """
        pass


class IStorageMigration(ABC):
    """存储迁移接口
    
    定义存储数据的迁移功能。
    """
    
    @abstractmethod
    def migrate_from(self, source_adapter: IStateStorageAdapter, 
                    target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
        """从源存储迁移到目标存储
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            迁移结果统计
        """
        pass
    
    @abstractmethod
    def validate_migration(self, source_adapter: IStateStorageAdapter,
                          target_adapter: IStateStorageAdapter) -> Dict[str, Any]:
        """验证迁移结果
        
        Args:
            source_adapter: 源存储适配器
            target_adapter: 目标存储适配器
            
        Returns:
            验证结果
        """
        pass