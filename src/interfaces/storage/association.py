"""
Session-Thread关联工厂接口

定义了Session-Thread关联仓储的工厂接口，用于解耦Services层和Adapters层。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.sessions.association import ISessionThreadAssociationRepository


class ISessionThreadAssociationFactory(ABC):
    """Session-Thread关联仓储工厂接口
    
    负责创建Session-Thread关联仓储实例，不直接依赖具体的实现。
    """
    
    @abstractmethod
    def create_repository(
        self,
        session_backend,
        thread_backend
    ) -> "ISessionThreadAssociationRepository":
        """创建Session-Thread关联仓储
        
        Args:
            session_backend: 会话存储后端实例
            thread_backend: 线程存储后端实例
            
        Returns:
            关联仓储实例
            
        Raises:
            StorageError: 创建失败时抛出
        """
        pass
