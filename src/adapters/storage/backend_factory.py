"""
存储后端工厂实现

Adapters层的工厂实现，负责创建具体的存储后端实例。
"""

from src.services.logger.injection import get_logger
from typing import Dict, Any, List

from .interfaces import (
    ISessionStorageBackendFactory,
    IThreadStorageBackendFactory,
)
from .backends.base import ISessionStorageBackend
from .backends.thread_base import IThreadStorageBackend
from .backends import SQLiteSessionBackend, FileSessionBackend
from .backends.sqlite_thread_backend import SQLiteThreadBackend
from .backends.file_thread_backend import FileThreadBackend


logger = get_logger(__name__)


class SessionStorageBackendFactory(ISessionStorageBackendFactory):
    """会话存储后端工厂实现"""
    
    def create_backend(
        self,
        backend_type: str,
        config: Dict[str, Any]
    ) -> ISessionStorageBackend:
        """根据类型创建会话存储后端
        
        Args:
            backend_type: 后端类型 (sqlite/file)
            config: 后端配置字典
            
        Returns:
            会话存储后端实例
            
        Raises:
            ValueError: 不支持的后端类型
        """
        if backend_type == "sqlite":
            db_path = config.get("db_path", "./data/sessions.db")
            return SQLiteSessionBackend(db_path=db_path)
        elif backend_type == "file":
            base_path = config.get("base_path", "./sessions_backup")
            return FileSessionBackend(base_path=base_path)
        else:
            raise ValueError(f"不支持的会话后端类型: {backend_type}")
    
    def create_primary_backend(self, config: Dict[str, Any]) -> ISessionStorageBackend:
        """创建主后端
        
        Args:
            config: 主后端配置
            
        Returns:
            主后端实例
        """
        primary_backend_type = config.get("session", {}).get("primary_backend", "sqlite")
        backend_config = config.get("session", {}).get(primary_backend_type, {})
        return self.create_backend(primary_backend_type, backend_config)
    
    def create_secondary_backends(self, config: Dict[str, Any]) -> List[ISessionStorageBackend]:
        """创建辅助后端列表
        
        Args:
            config: 辅助后端配置列表
            
        Returns:
            辅助后端实例列表
        """
        secondary_backends = []
        secondary_types = config.get("session", {}).get("secondary_backends", [])
        
        for backend_type in secondary_types:
            try:
                if backend_type == "file":
                    backend_config = config.get("session", {}).get("file", {})
                    backend = self.create_backend(backend_type, backend_config)
                    secondary_backends.append(backend)
                elif backend_type == "sqlite":
                    backend_config = config.get("session", {}).get("sqlite_secondary", {})
                    backend = self.create_backend(backend_type, backend_config)
                    secondary_backends.append(backend)
                else:
                    logger.warning(f"不支持的会话辅助后端类型: {backend_type}")
            except Exception as e:
                logger.warning(f"创建会话辅助后端 {backend_type} 失败: {e}")
        
        return secondary_backends


class ThreadStorageBackendFactory(IThreadStorageBackendFactory):
    """线程存储后端工厂实现"""
    
    def create_backend(
        self,
        backend_type: str,
        config: Dict[str, Any]
    ) -> IThreadStorageBackend:
        """根据类型创建线程存储后端
        
        Args:
            backend_type: 后端类型 (sqlite/file)
            config: 后端配置字典
            
        Returns:
            线程存储后端实例
            
        Raises:
            ValueError: 不支持的后端类型
        """
        if backend_type == "sqlite":
            db_path = config.get("db_path", "./data/threads.db")
            return SQLiteThreadBackend(db_path=db_path)
        elif backend_type == "file":
            base_path = config.get("base_path", "./threads_backup")
            return FileThreadBackend(base_path=base_path)
        else:
            raise ValueError(f"不支持的线程后端类型: {backend_type}")
    
    def create_primary_backend(self, config: Dict[str, Any]) -> IThreadStorageBackend:
        """创建主后端
        
        Args:
            config: 主后端配置
            
        Returns:
            主后端实例
        """
        primary_backend_type = config.get("thread", {}).get("primary_backend", "sqlite")
        backend_config = config.get("thread", {}).get(primary_backend_type, {})
        return self.create_backend(primary_backend_type, backend_config)
    
    def create_secondary_backends(self, config: Dict[str, Any]) -> List[IThreadStorageBackend]:
        """创建辅助后端列表
        
        Args:
            config: 辅助后端配置列表
            
        Returns:
            辅助后端实例列表
        """
        secondary_backends = []
        secondary_types = config.get("thread", {}).get("secondary_backends", [])
        
        for backend_type in secondary_types:
            try:
                if backend_type == "file":
                    backend_config = config.get("thread", {}).get("file", {})
                    backend = self.create_backend(backend_type, backend_config)
                    secondary_backends.append(backend)
                elif backend_type == "sqlite":
                    backend_config = config.get("thread", {}).get("sqlite_secondary", {})
                    backend = self.create_backend(backend_type, backend_config)
                    secondary_backends.append(backend)
                else:
                    logger.warning(f"不支持的线程辅助后端类型: {backend_type}")
            except Exception as e:
                logger.warning(f"创建线程辅助后端 {backend_type} 失败: {e}")
        
        return secondary_backends
