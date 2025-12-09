"""存储后端注册表

提供存储后端的注册和管理功能。
"""

from typing import Dict, Type, List, Optional, Any
from src.interfaces.storage.base import IStorage
from src.services.logger.injection import get_logger


logger = get_logger(__name__)


class BackendRegistry:
    """存储后端注册表
    
    管理所有可用的存储后端类型，提供注册、查询和实例化功能。
    """
    
    def __init__(self) -> None:
        """初始化后端注册表"""
        self._backends: Dict[str, Type[IStorage]] = {}
        self._backend_configs: Dict[str, Dict[str, Any]] = {}
        self._backend_descriptions: Dict[str, str] = {}
        
        # 注册默认后端
        self._register_default_backends()
    
    def _register_default_backends(self) -> None:
        """注册默认后端"""
        try:
            from ..backends.sqlite_backend import SQLiteStorageBackend
            self.register("sqlite", SQLiteStorageBackend, "SQLite存储后端")
        except ImportError:
            logger.warning("SQLite后端不可用")
        
        try:
            from ..backends.memory_backend import MemoryStorageBackend
            self.register("memory", MemoryStorageBackend, "内存存储后端")
        except ImportError:
            logger.warning("内存后端不可用")
        
        try:
            from ..backends.file_backend import FileStorageBackend
            self.register("file", FileStorageBackend, "文件存储后端")
        except ImportError:
            logger.warning("文件后端不可用")
        
        logger.info("默认后端注册完成")
    
    def register(
        self,
        name: str,
        backend_class: Type[IStorage],
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
        
        if not issubclass(backend_class, IStorage):
            raise ValueError(f"Backend class must implement IStorage interface")
        
        self._backends[name] = backend_class
        self._backend_descriptions[name] = description
        self._backend_configs[name] = default_config or {}
        
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
        
        self._backends.pop(name, None)
        self._backend_configs.pop(name, None)
        self._backend_descriptions.pop(name, None)
        
        logger.info(f"Unregistered storage backend: {name}")
        return True
    
    def get_backend_class(self, name: str) -> Type[IStorage]:
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
        
        return self._backends[name]
    
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
        
        return self._backend_configs[name].copy()
    
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
        
        return self._backend_descriptions[name]
    
    def list_backends(self) -> List[str]:
        """列出所有已注册的后端名称
        
        Returns:
            后端名称列表
        """
        return list(self._backends.keys())
    
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
        
        backend_class = self._backends[name]
        
        return {
            "name": name,
            "class_name": backend_class.__name__,
            "module": backend_class.__module__,
            "description": self._backend_descriptions[name],
            "default_config": self._backend_configs[name].copy(),
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
        
        default_config = self._backend_configs[name].copy()
        merged_config = default_config.copy()
        merged_config.update(user_config)
        
        return merged_config
    
    def create_backend_instance(self, name: str, config: Dict[str, Any]) -> IStorage:
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
        
        # 创建实例
        backend_class = self.get_backend_class(name)
        instance = backend_class(**merged_config)
        
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
    backend_class: Type[IStorage],
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