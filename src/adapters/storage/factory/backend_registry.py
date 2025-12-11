"""存储后端注册表

提供存储后端的注册和管理功能。
使用新的provider+impl设计模式。
"""

from typing import Dict, Type, List, Optional, Any, Union
from src.interfaces.storage.base import IStorage
from src.interfaces.storage import ISessionStorage, IThreadStorage, IStorageProvider
from src.interfaces.dependency_injection import get_logger

# 导入新的provider和impl
from ..backends.providers.sqlite_provider import SQLiteProvider
from ..backends.providers.memory_provider import MemoryProvider
from ..backends.providers.file_provider import FileProvider
from ..backends.impl.session_backend import SessionBackend
from ..backends.impl.thread_backend import ThreadBackend


logger = get_logger(__name__)


class BackendRegistry:
    """存储后端注册表
    
    管理所有可用的存储后端类型，提供注册、查询和实例化功能。
    使用新的provider+impl设计模式。
    """
    
    def __init__(self) -> None:
        """初始化后端注册表"""
        self._backends: Dict[str, Dict[str, Any]] = {}
        self._provider_registry: Dict[str, Type[IStorageProvider]] = {}
        
        # 注册默认提供者
        self._register_default_providers()
        
        # 注册默认后端
        self._register_default_backends()
    
    def _register_default_providers(self) -> None:
        """注册默认存储提供者"""
        self._provider_registry["sqlite"] = SQLiteProvider
        self._provider_registry["memory"] = MemoryProvider
        self._provider_registry["file"] = FileProvider
        logger.info("默认提供者注册完成")
    
    def _register_default_backends(self) -> None:
        """注册默认后端"""
        # 会话存储后端
        self.register(
            "session",
            SessionBackend,
            "会话存储后端",
            {
                "provider_type": "sqlite",  # 默认使用SQLite
                "db_path": "./data/sessions.db",
                "max_connections": 10,
                "timeout": 30.0
            }
        )
        
        # 线程存储后端
        self.register(
            "thread",
            ThreadBackend,
            "线程存储后端",
            {
                "provider_type": "sqlite",  # 默认使用SQLite
                "db_path": "./data/threads.db",
                "max_connections": 10,
                "timeout": 30.0
            }
        )
        
        # 通用存储后端（直接使用provider）
        self.register(
            "sqlite",
            SQLiteProvider,
            "SQLite存储后端",
            {
                "db_path": "./data/storage.db",
                "max_connections": 10,
                "timeout": 30.0
            }
        )
        
        self.register(
            "memory",
            MemoryProvider,
            "内存存储后端",
            {
                "max_memory_usage": 100 * 1024 * 1024  # 100MB
            }
        )
        
        self.register(
            "file",
            FileProvider,
            "文件存储后端",
            {
                "base_path": "./storage",
                "file_extension": ".json"
            }
        )
        
        logger.info("默认后端注册完成")
    
    def register(
        self,
        name: str,
        backend_class: Union[Type[IStorage], Type[ISessionStorage], Type[IThreadStorage], Type[IStorageProvider]],
        description: str = "",
        default_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册存储后端
        
        Args:
            name: 后端名称
            backend_class: 后端类
            description: 后端描述
            default_config: 默认配置
            
        Raises:
            ValueError: 后端名称已存在或类无效
        """
        if name in self._backends:
            raise ValueError(f"Backend '{name}' already registered")
        
        # 验证类是否实现了适当的接口
        if not (issubclass(backend_class, IStorage) or 
                issubclass(backend_class, ISessionStorage) or 
                issubclass(backend_class, IThreadStorage) or
                issubclass(backend_class, IStorageProvider)):
            raise ValueError(f"Backend class must implement IStorage, ISessionStorage, IThreadStorage or IStorageProvider interface")
        
        self._backends[name] = {
            "class": backend_class,
            "description": description,
            "default_config": default_config or {},
            "provider_type": default_config.get("provider_type") if default_config else None
        }
        
        logger.info(f"Registered storage backend: {name}")
    
    def unregister(self, name: str) -> bool:
        """注销存储后端
        
        Args:
            name: 后端名称
            
        Returns:
            是否成功注销
        """
        if name not in self._backends:
            return False
        
        del self._backends[name]
        logger.info(f"Unregistered storage backend: {name}")
        return True
    
    def get_backend_class(self, name: str) -> Union[Type[IStorage], Type[ISessionStorage], Type[IThreadStorage], Type[IStorageProvider]]:
        """获取后端类
        
        Args:
            name: 后端名称
            
        Returns:
            后端类
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        return self._backends[name]["class"]  # type: ignore
    
    def get_backend_config(self, name: str) -> Dict[str, Any]:
        """获取后端默认配置
        
        Args:
            name: 后端名称
            
        Returns:
            默认配置字典
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        return self._backends[name]["default_config"].copy()  # type: ignore
    
    def get_backend_description(self, name: str) -> str:
        """获取后端描述
        
        Args:
            name: 后端名称
            
        Returns:
            后端描述
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        return self._backends[name]["description"]  # type: ignore
    
    def list_backends(self) -> List[str]:
        """列出所有已注册的后端名称
        
        Returns:
            后端名称列表
        """
        return list(self._backends.keys())
    
    def get_provider_type(self, backend_name: str) -> Optional[str]:
        """获取后端的提供者类型
        
        Args:
            backend_name: 后端名称
            
        Returns:
            提供者类型
        """
        if backend_name not in self._backends:
            return None
        
        return self._backends[backend_name]["default_config"].get("provider_type")  # type: ignore
    
    def create_provider(self, provider_type: str, config: Dict[str, Any]) -> IStorageProvider:
        """创建存储提供者
        
        Args:
            provider_type: 提供者类型
            config: 提供者配置
            
        Returns:
            存储提供者实例
            
        Raises:
            ValueError: 提供者类型不存在时抛出
        """
        if provider_type not in self._provider_registry:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        provider_class = self._provider_registry[provider_type]
        return provider_class(**config)
    
    def get_backend_info(self, name: str) -> Dict[str, Any]:
        """获取后端详细信息
        
        Args:
            name: 后端名称
            
        Returns:
            后端信息字典
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        backend_info = self._backends[name]
        backend_class = backend_info["class"]
        
        return {
            "name": name,
            "class_name": backend_class.__name__,
            "module": backend_class.__module__,
            "description": backend_info["description"],
            "default_config": backend_info["default_config"].copy(),
            "provider_type": backend_info["provider_type"],
            "docstring": backend_class.__doc__ or "",
        }
    
    def get_all_backends_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有后端的详细信息
        
        Returns:
            所有后端信息字典
        """
        return {
            name: self.get_backend_info(name)
            for name in self._backends.keys()
        }
    
    def is_backend_registered(self, name: str) -> bool:
        """检查后端是否已注册
        
        Args:
            name: 后端名称
            
        Returns:
            是否已注册
        """
        return name in self._backends
    
    def validate_backend_config(self, name: str, config: Dict[str, Any]) -> bool:
        """验证后端配置
        
        Args:
            name: 后端名称
            config: 配置字典
            
        Returns:
            配置是否有效
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        # 基础验证：检查配置是否为字典
        if not isinstance(config, dict):
            return False
        
        # 这里可以添加更具体的配置验证逻辑
        # 例如检查必需的配置项
        
        return True
    
    def get_required_config_keys(self, name: str) -> List[str]:
        """获取后端必需的配置键
        
        Args:
            name: 后端名称
            
        Returns:
            必需配置键列表
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        # 这里可以根据后端类定义返回必需的配置键
        # 默认返回空列表
        return []
    
    def get_optional_config_keys(self, name: str) -> List[str]:
        """获取后端可选的配置键
        
        Args:
            name: 后端名称
            
        Returns:
            可选配置键列表
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        # 这里可以根据后端类定义返回可选的配置键
        # 默认返回常见配置键
        return [
            "max_retries",
            "retry_delay",
            "backoff_factor",
            "timeout",
            "max_history_size",
            "time_series_window",
            "max_concurrent_transactions",
            "transaction_timeout",
            "auto_cleanup_interval",
            "health_check_interval",
            "health_check_timeout",
            "enable_compression",
            "compression_threshold",
            "enable_ttl",
            "default_ttl_seconds",
        ]
    
    def merge_config(self, name: str, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并用户配置和默认配置
        
        Args:
            name: 后端名称
            user_config: 用户配置
            
        Returns:
            合并后的配置
            
        Raises:
            ValueError: 后端不存在
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        default_config = self._backends[name]["default_config"].copy()
        merged_config = default_config.copy()
        merged_config.update(user_config)
        
        return merged_config  # type: ignore
    
    def create_backend_instance(self, name: str, config: Dict[str, Any]) -> Union[IStorage, ISessionStorage, IThreadStorage, IStorageProvider]:
        """创建后端实例
        
        Args:
            name: 后端名称
            config: 配置字典
            
        Returns:
            后端实例
            
        Raises:
            ValueError: 后端不存在或配置无效
        """
        if not self.is_backend_registered(name):
            raise ValueError(f"Unknown storage backend: {name}")
        
        if not self.validate_backend_config(name, config):
            raise ValueError(f"Invalid config for backend '{name}'")
        
        # 合并配置
        merged_config = self.merge_config(name, config)
        
        # 获取后端类
        backend_class = self.get_backend_class(name)
        
        # 检查是否是Provider类
        if issubclass(backend_class, IStorageProvider):
            # 直接创建Provider实例
            instance = backend_class(**merged_config)
        else:
            # 创建Impl实例，需要Provider
            provider_type = merged_config.get("provider_type")
            if not provider_type:
                raise ValueError(f"No provider_type specified for backend: {name}")
            
            # 创建Provider
            provider_config = {k: v for k, v in merged_config.items() if k != "provider_type"}
            provider = self.create_provider(provider_type, provider_config)
            
            # 创建Impl实例
            config_without_provider_type = {k: v for k, v in merged_config.items() if k != "provider_type"}
            instance = backend_class(provider, **config_without_provider_type)  # type: ignore
        
        logger.info(f"Created instance of backend '{name}'")
        return instance


# 全局后端注册表实例
_global_registry: Optional[BackendRegistry] = None


def get_global_registry() -> BackendRegistry:
    """获取全局后端注册表实例
    
    Returns:
        全局后端注册表实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = BackendRegistry()
    return _global_registry


def register_backend(
    name: str,
    backend_class: Union[Type[IStorage], Type[ISessionStorage], Type[IThreadStorage], Type[IStorageProvider]],
    description: str = "",
    default_config: Optional[Dict[str, Any]] = None
) -> None:
    """注册存储后端到全局注册表
    
    Args:
        name: 后端名称
        backend_class: 后端类
        description: 后端描述
        default_config: 默认配置
    """
    registry = get_global_registry()
    registry.register(name, backend_class, description, default_config)


def unregister_backend(name: str) -> bool:
    """从全局注册表注销存储后端
    
    Args:
        name: 后端名称
        
    Returns:
        是否成功注销
    """
    registry = get_global_registry()
    return registry.unregister(name)