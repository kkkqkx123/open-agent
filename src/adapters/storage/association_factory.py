"""
Session-Thread关联工厂实现

Adapters层的工厂实现，负责创建Session-Thread关联仓储实例。
"""

from src.interfaces.storage.association import ISessionThreadAssociationFactory
from src.interfaces.sessions.association import ISessionThreadAssociationRepository
from .association_repository import SessionThreadAssociationRepository


class SessionThreadAssociationFactory(ISessionThreadAssociationFactory):
    """Session-Thread关联仓储工厂实现"""
    
    def create_repository(
        self,
        session_backend,
        thread_backend
    ) -> ISessionThreadAssociationRepository:
        """创建Session-Thread关联仓储
        
        Args:
            session_backend: 会话存储后端实例
            thread_backend: 线程存储后端实例
            
        Returns:
            关联仓储实例
            
        Raises:
            ValueError: 参数无效时抛出
        """
        if not session_backend:
            raise ValueError("会话后端不能为空")
        if not thread_backend:
            raise ValueError("线程后端不能为空")
        
        return SessionThreadAssociationRepository(
            session_backend=session_backend,
            thread_backend=thread_backend
        )
