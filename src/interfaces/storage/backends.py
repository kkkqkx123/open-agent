"""
存储后端工厂接口

定义了会话和线程存储后端的工厂接口，用于解耦Services层和Adapters层。
Services层通过工厂接口创建后端，不直接依赖具体的后端实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.sessions import ISessionStorageBackend
    from src.interfaces.threads import IThreadStorageBackend


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
