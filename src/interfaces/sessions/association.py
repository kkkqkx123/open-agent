"""Session-Thread关联接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol, Sequence
from datetime import datetime


class ISessionThreadAssociation(Protocol):
    """Session-Thread关联协议接口"""
    
    # 基本标识
    association_id: str
    session_id: str
    thread_id: str
    thread_name: str
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    
    # 关联状态
    is_active: bool
    association_type: str
    
    # 元数据
    metadata: Dict[str, Any]
    
    def update_timestamp(self) -> None: ...
    def deactivate(self) -> None: ...
    def activate(self) -> None: ...
    def update_metadata(self, metadata: Dict[str, Any]) -> None: ...
    def to_dict(self) -> Dict[str, Any]: ...


class ISessionThreadAssociationRepository(ABC):
    """Session-Thread关联仓储接口"""
    
    @abstractmethod
    async def create(self, association: ISessionThreadAssociation) -> bool:
        """创建关联
        
        Args:
            association: 关联实体
            
        Returns:
            是否创建成功
        """
        pass
    
    @abstractmethod
    async def get(self, association_id: str) -> Optional[ISessionThreadAssociation]:
        """获取关联
        
        Args:
            association_id: 关联ID
            
        Returns:
            关联实体，不存在返回None
        """
        pass
    
    @abstractmethod
    async def get_by_session_and_thread(
        self,
        session_id: str,
        thread_id: str
    ) -> Optional[ISessionThreadAssociation]:
        """根据Session和Thread ID获取关联
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            关联实体，不存在返回None
        """
        pass
    
    @abstractmethod
    async def list_by_session(self, session_id: str) -> Sequence[ISessionThreadAssociation]:
        """列出Session的所有关联
        
        Args:
            session_id: 会话ID
            
        Returns:
            关联列表
        """
        pass
    
    @abstractmethod
    async def list_by_thread(self, thread_id: str) -> Sequence[ISessionThreadAssociation]:
        """列出Thread的所有关联
        
        Args:
            thread_id: 线程ID
            
        Returns:
            关联列表
        """
        pass
    
    @abstractmethod
    async def update(self, association: ISessionThreadAssociation) -> bool:
        """更新关联
        
        Args:
            association: 关联实体
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete(self, association_id: str) -> bool:
        """删除关联
        
        Args:
            association_id: 关联ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def delete_by_session_and_thread(self, session_id: str, thread_id: str) -> bool:
        """根据Session和Thread ID删除关联
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, session_id: str, thread_id: str) -> bool:
        """检查关联是否存在
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def get_active_associations_by_session(self, session_id: str) -> Sequence[ISessionThreadAssociation]:
        """获取Session的活跃关联
        
        Args:
            session_id: 会话ID
            
        Returns:
            活跃关联列表
        """
        pass
    
    @abstractmethod
    async def cleanup_inactive_associations(self, max_age_days: int = 30) -> int:
        """清理非活跃关联
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的关联数量
        """
        pass


class ISessionThreadSynchronizer(ABC):
    """Session-Thread同步器接口"""
    
    @abstractmethod
    async def sync_session_threads(self, session_id: str) -> Dict[str, Any]:
        """同步Session的Thread关联
        
        Args:
            session_id: 会话ID
            
        Returns:
            同步结果统计
        """
        pass
    
    @abstractmethod
    async def validate_consistency(self, session_id: str) -> List[str]:
        """验证Session-Thread一致性
        
        Args:
            session_id: 会话ID
            
        Returns:
            发现的问题列表
        """
        pass
    
    @abstractmethod
    async def repair_inconsistencies(self, session_id: str) -> Dict[str, Any]:
        """修复不一致问题
        
        Args:
            session_id: 会话ID
            
        Returns:
            修复结果统计
        """
        pass


class ISessionThreadTransaction(ABC):
    """Session-Thread事务管理接口"""
    
    @abstractmethod
    async def create_thread_with_session(
        self,
        session_id: str,
        thread_config: Dict[str, Any],
        thread_name: str
    ) -> str:
        """原子性地创建Thread并建立Session关联
        
        Args:
            session_id: 会话ID
            thread_config: 线程配置
            thread_name: 线程名称
            
        Returns:
            创建的Thread ID
            
        Raises:
            SessionThreadException: 操作失败时抛出
        """
        pass
    
    @abstractmethod
    async def remove_thread_from_session(
        self,
        session_id: str,
        thread_id: str
    ) -> bool:
        """原子性地从Session中移除Thread
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            是否移除成功
            
        Raises:
            SessionThreadException: 操作失败时抛出
        """
        pass
    
    @abstractmethod
    async def transfer_thread_between_sessions(
        self,
        thread_id: str,
        from_session_id: str,
        to_session_id: str,
        new_thread_name: Optional[str] = None
    ) -> bool:
        """原子性地在线程间转移Thread
        
        Args:
            thread_id: 线程ID
            from_session_id: 源会话ID
            to_session_id: 目标会话ID
            new_thread_name: 新线程名称
            
        Returns:
            是否转移成功
            
        Raises:
            SessionThreadException: 操作失败时抛出
        """
        pass


# 导出所有接口
__all__ = [
    "ISessionThreadAssociationRepository",
    "ISessionThreadSynchronizer", 
    "ISessionThreadTransaction"
]