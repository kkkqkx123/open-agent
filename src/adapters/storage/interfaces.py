"""
Adapters 层存储工厂接口

仅在 Adapters 层内部使用的工厂接口，负责创建和管理存储后端及关联仓储实例。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .backends.base import ISessionStorageBackend
    from .backends.thread_base import IThreadStorageBackend
    from src.interfaces.sessions.association import ISessionThreadAssociationRepository


class ISessionStorageBackendFactory(ABC):
    """会话存储后端工厂接口
    
    负责创建和管理会话存储后端实例，支持多种后端类型。
    """
    
    @abstractmethod
    def create_backend(self, backend_type: str, config: Dict[str, Any]) -> "ISessionStorageBackend":
        """根据类型创建会话存储后端
        
        Args:
            backend_type: 后端类型 (sqlite/file)
            config: 后端配置字典
            
        Returns:
            会话存储后端实例
            
        Raises:
            StorageError: 创建失败时抛出
        """
        pass
    
    @abstractmethod
    def create_primary_backend(self, config: Dict[str, Any]) -> "ISessionStorageBackend":
        """创建主后端
        
        Args:
            config: 主后端配置
            
        Returns:
            主后端实例
        """
        pass
    
    @abstractmethod
    def create_secondary_backends(self, config: Dict[str, Any]) -> list["ISessionStorageBackend"]:
        """创建辅助后端列表
        
        Args:
            config: 辅助后端配置列表
            
        Returns:
            辅助后端实例列表
        """
        pass


class IThreadStorageBackendFactory(ABC):
    """线程存储后端工厂接口
    
    负责创建和管理线程存储后端实例，支持多种后端类型。
    """
    
    @abstractmethod
    def create_backend(self, backend_type: str, config: Dict[str, Any]) -> "IThreadStorageBackend":
        """根据类型创建线程存储后端
        
        Args:
            backend_type: 后端类型 (sqlite/file)
            config: 后端配置字典
            
        Returns:
            线程存储后端实例
            
        Raises:
            StorageError: 创建失败时抛出
        """
        pass
    
    @abstractmethod
    def create_primary_backend(self, config: Dict[str, Any]) -> "IThreadStorageBackend":
        """创建主后端
        
        Args:
            config: 主后端配置
            
        Returns:
            主后端实例
        """
        pass
    
    @abstractmethod
    def create_secondary_backends(self, config: Dict[str, Any]) -> list["IThreadStorageBackend"]:
        """创建辅助后端列表
        
        Args:
            config: 辅助后端配置列表
            
        Returns:
            辅助后端实例列表
        """
        pass


class ISessionThreadAssociationFactory(ABC):
    """Session-Thread关联仓储工厂接口
    
    负责创建Session-Thread关联仓储实例，仅在Adapters层内部使用。
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
