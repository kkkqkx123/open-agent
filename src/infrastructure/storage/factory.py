"""
存储工厂

提供存储实例的创建和管理功能，支持配置驱动的存储创建。
"""

from typing import Dict, Any, Type, Optional, List
import logging

from ...domain.storage.interfaces import IUnifiedStorage, IStorageFactory
from ...domain.storage.exceptions import StorageError, StorageConfigurationError
from .base_storage import BaseStorage
from .registry import StorageRegistry
from ..common.serialization.serializer import Serializer
from .serializer_adapter import SerializerAdapter


logger = logging.getLogger(__name__)


class StorageFactory(IStorageFactory):
    """存储工厂实现
    
    负责根据配置创建和管理存储实例。
    """
    
    def __init__(self, registry: Optional[StorageRegistry] = None):
        """初始化存储工厂
        
        Args:
            registry: 存储注册表，如果为None则创建默认注册表
        """
        self._registry = registry or StorageRegistry()
        self._instances: Dict[str, IUnifiedStorage] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
    
    def create_storage(self, storage_type: str, config: Dict[str, Any]) -> IUnifiedStorage:
        """创建存储实例
        
        Args:
            storage_type: 存储类型
            config: 存储配置
            
        Returns:
            存储实例
            
        Raises:
            StorageConfigurationError: 配置错误时抛出
            StorageError: 创建失败时抛出
        """
        try:
            # 验证配置
            self._validate_config(storage_type, config)
            
            # 获取存储类
            storage_class = self._registry.get_storage_class(storage_type)
            
            # 创建后端实例
            backend = self._create_backend(storage_class, config)
            
            # 创建序列化器
            serializer = self._create_serializer(config)
            
            # 创建缓存
            cache = self._create_cache(config)
            
            # 创建指标收集器
            metrics = self._create_metrics(config)
            
            # 创建存储实例
            storage = BaseStorage(
                backend=backend,
                serializer=serializer,
                cache=cache,
                metrics=metrics,
                cache_ttl=config.get("cache_ttl", 300),
                enable_metrics=config.get("enable_metrics", True),
                timeout=config.get("timeout", 30.0)
            )
            
            logger.info(f"Created storage instance of type '{storage_type}'")
            return storage
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to create storage of type '{storage_type}': {e}")
    
    def register_storage(self, storage_type: str, storage_class: Type) -> None:
        """注册存储类型
        
        Args:
            storage_type: 存储类型名称
            storage_class: 存储类
            
        Raises:
            StorageError: 注册失败时抛出
        """
        try:
            self._registry.register(storage_type, storage_class)
            logger.info(f"Registered storage type '{storage_type}'")
        except Exception as e:
            raise StorageError(f"Failed to register storage type '{storage_type}': {e}")
    
    def get_available_types(self) -> List[str]:
        """获取可用的存储类型
        
        Returns:
            存储类型列表
        """
        return self._registry.get_registered_types()
    
    def is_type_available(self, storage_type: str) -> bool:
        """检查存储类型是否可用
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            是否可用
        """
        return self._registry.is_registered(storage_type)
    
    def create_or_get_storage(
        self, 
        storage_type: str, 
        config: Dict[str, Any],
        instance_name: Optional[str] = None
    ) -> IUnifiedStorage:
        """创建或获取存储实例
        
        如果指定了实例名称且该实例已存在，则返回现有实例；
        否则创建新实例。
        
        Args:
            storage_type: 存储类型
            config: 存储配置
            instance_name: 实例名称
            
        Returns:
            存储实例
        """
        if instance_name and instance_name in self._instances:
            return self._instances[instance_name]
        
        storage = self.create_storage(storage_type, config)
        
        if instance_name:
            self._instances[instance_name] = storage
            self._configs[instance_name] = config
        
        return storage
    
    def get_instance(self, instance_name: str) -> Optional[IUnifiedStorage]:
        """获取已命名的存储实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            存储实例，如果不存在则返回None
        """
        return self._instances.get(instance_name)
    
    def remove_instance(self, instance_name: str) -> bool:
        """移除已命名的存储实例
        
        Args:
            instance_name: 实例名称
            
        Returns:
            是否成功移除
        """
        if instance_name in self._instances:
            del self._instances[instance_name]
            if instance_name in self._configs:
                del self._configs[instance_name]
            return True
        return False
    
    def get_instance_config(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """获取实例配置
        
        Args:
            instance_name: 实例名称
            
        Returns:
            配置字典，如果不存在则返回None
        """
        return self._configs.get(instance_name)
    
    def list_instances(self) -> Dict[str, Dict[str, Any]]:
        """列出所有实例及其配置
        
        Returns:
            实例名称到配置的映射
        """
        return {
            name: {
                "config": config.copy(),
                "type": config.get("storage_type", "unknown")
            }
            for name, config in self._configs.items()
        }
    
    async def close_all_instances(self) -> None:
        """关闭所有实例"""
        for name, storage in self._instances.items():
            try:
                if hasattr(storage, "close"):
                    await storage.close()
                logger.info(f"Closed storage instance '{name}'")
            except Exception as e:
                logger.error(f"Failed to close storage instance '{name}': {e}")
        
        self._instances.clear()
        self._configs.clear()
    
    def _validate_config(self, storage_type: str, config: Dict[str, Any]) -> None:
        """验证配置
        
        Args:
            storage_type: 存储类型
            config: 配置字典
            
        Raises:
            StorageConfigurationError: 配置无效时抛出
        """
        if not isinstance(config, dict):
            raise StorageConfigurationError("Config must be a dictionary")
        
        if "storage_type" not in config:
            config["storage_type"] = storage_type
        
        # 验证通用配置
        if "timeout" in config:
            timeout = config["timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise StorageConfigurationError("Timeout must be a positive number")
        
        if "cache_ttl" in config:
            cache_ttl = config["cache_ttl"]
            if not isinstance(cache_ttl, int) or cache_ttl < 0:
                raise StorageConfigurationError("Cache TTL must be a non-negative integer")
        
        # 验证特定存储类型的配置
        self._validate_type_specific_config(storage_type, config)
    
    def _validate_type_specific_config(self, storage_type: str, config: Dict[str, Any]) -> None:
        """验证特定存储类型的配置
        
        Args:
            storage_type: 存储类型
            config: 配置字典
            
        Raises:
            StorageConfigurationError: 配置无效时抛出
        """
        # 根据存储类型验证特定配置
        if storage_type == "memory":
            # 内存存储特定验证
            max_size = config.get("max_size")
            if max_size is not None and (not isinstance(max_size, int) or max_size <= 0):
                raise StorageConfigurationError("Memory storage max_size must be a positive integer")
        
        elif storage_type == "sqlite":
            # SQLite存储特定验证
            if "database_path" not in config:
                raise StorageConfigurationError("SQLite storage requires 'database_path' config")
            
            pool_size = config.get("pool_size")
            if pool_size is not None and (not isinstance(pool_size, int) or pool_size <= 0):
                raise StorageConfigurationError("SQLite storage pool_size must be a positive integer")
        
        elif storage_type == "file":
            # 文件存储特定验证
            if "base_path" not in config:
                raise StorageConfigurationError("File storage requires 'base_path' config")
    
    def _create_backend(self, storage_class: Type, config: Dict[str, Any]) -> Any:
        """创建存储后端
        
        Args:
            storage_class: 存储类
            config: 配置字典
            
        Returns:
            存储后端实例
        """
        # 提取后端配置
        backend_config = config.get("backend", {})
        
        # 创建后端实例
        return storage_class(**backend_config)
    
    def _create_serializer(self, config: Dict[str, Any]) -> Optional[SerializerAdapter]:
        """创建序列化器
        
        Args:
            config: 配置字典
            
        Returns:
            序列化器适配器实例，如果未配置则返回None
        """
        serializer_config = config.get("serializer")
        if not serializer_config:
            return None
        
        options = serializer_config.get("options", {})
        enable_cache = options.get("enable_cache", False)
        cache_size = options.get("cache_size", 1000)
        
        serializer = Serializer(enable_cache=enable_cache, cache_size=cache_size)
        return SerializerAdapter(serializer)
    
    def _create_cache(self, config: Dict[str, Any]) -> None:
        """创建缓存
        
        缓存功能已集成在 Serializer 中。
        
        Args:
            config: 配置字典
            
        Returns:
            None
        """
        # 缓存功能已通过 Serializer 实现，此方法保留以保持接口兼容
        return None
    
    def _create_metrics(self, config: Dict[str, Any]) -> None:
        """创建指标收集器
        
        当前未实现单独的指标收集模块。
        
        Args:
            config: 配置字典
            
        Returns:
            None
        """
        # 指标收集功能保留用于未来扩展
        return None