"""存储工厂

提供统一的存储实例创建和管理功能。
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from src.interfaces.storage.base import IStorage, IStorageFactory
from src.interfaces.storage import ISessionStorage, IThreadStorage, IStorageProvider
from src.interfaces.storage.exceptions import StorageError, StorageConfigurationError
from src.interfaces.dependency_injection import get_logger
from .backend_registry import BackendRegistry, get_global_registry


logger = get_logger(__name__)


class StorageFactory(IStorageFactory):
    """存储工厂
    
    负责创建、配置和管理存储实例。
    """
    
    def __init__(
        self,
        registry: Optional[BackendRegistry] = None,
        default_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化存储工厂
        
        Args:
            registry: 后端注册表，默认使用全局注册表
            default_config: 默认配置
        """
        self.registry = registry or get_global_registry()
        self.default_config = default_config or {}
        
        # 存储实例缓存
        self._instance_cache: Dict[str, Union[IStorage, ISessionStorage, IThreadStorage, IStorageProvider]] = {}
        
        # 实例配置记录
        self._instance_configs: Dict[str, Dict[str, Any]] = {}
    
    def create_storage(
        self,
        storage_type: str,
        config: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        use_cache: bool = True
    ) -> IStorage:
        """创建存储实例
        
        Args:
            storage_type: 存储类型
            config: 存储配置
            cache_key: 缓存键，None表示自动生成
            use_cache: 是否使用缓存
            
        Returns:
            存储实例
            
        Raises:
            StorageConfigurationError: 配置无效
            StorageError: 创建失败
        """
        # 合并配置
        merged_config = self._merge_config(storage_type, config or {})
        
        # 验证配置
        if not self._validate_config(storage_type, merged_config):
            raise StorageConfigurationError(f"Invalid config for storage type '{storage_type}'")
        
        # 检查缓存
        if use_cache:
            if cache_key is None:
                cache_key = self._generate_cache_key(storage_type, merged_config)
            
            if cache_key in self._instance_cache:
                logger.info(f"Using cached storage instance: {cache_key}")
                return self._instance_cache[cache_key]  # type: ignore
        
        try:
            # 创建实例
            instance = self.registry.create_backend_instance(storage_type, merged_config)
            
            # 缓存实例
            if use_cache and cache_key:
                self._instance_cache[cache_key] = instance
                self._instance_configs[cache_key] = merged_config.copy()
            
            logger.info(f"Created storage instance of type '{storage_type}'")
            return instance  # type: ignore
            
        except Exception as e:
            raise StorageError(f"Failed to create storage instance: {e}")
    
    async def create_storage_async(
        self,
        storage_type: str,
        config: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        use_cache: bool = True,
        auto_connect: bool = True
    ) -> IStorage:
        """异步创建存储实例
        
        Args:
            storage_type: 存储类型
            config: 存储配置
            cache_key: 缓存键
            use_cache: 是否使用缓存
            auto_connect: 是否自动连接
            
        Returns:
            存储实例
        """
        # 创建实例
        instance: IStorage = self.create_storage(storage_type, config, cache_key, use_cache)
        
        # 自动连接
        if auto_connect:
            try:
                await instance.connect()
                logger.info(f"Connected storage instance of type '{storage_type}'")
            except Exception as e:
                logger.warning(f"Failed to connect storage instance: {e}")
        
        return instance
    
    def register_storage(self, storage_type: str, storage_class: type) -> None:
        """注册存储类型
        
        Args:
            storage_type: 存储类型名称
            storage_class: 存储类
            
        Raises:
            StorageError: 注册失败
        """
        try:
            self.registry.register(storage_type, storage_class)
            logger.info(f"Registered storage type: {storage_type}")
        except Exception as e:
            raise StorageError(f"Failed to register storage type '{storage_type}': {e}")
    
    def get_available_types(self) -> List[str]:
        """获取可用的存储类型
        
        Returns:
            存储类型列表
        """
        return self.registry.list_backends()
    
    def is_type_available(self, storage_type: str) -> bool:
        """检查存储类型是否可用
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            是否可用
        """
        return self.registry.is_backend_registered(storage_type)
    
    def get_storage_info(self, storage_type: str) -> Dict[str, Any]:
        """获取存储类型信息
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            存储类型信息
            
        Raises:
            StorageError: 存储类型不存在
        """
        try:
            return self.registry.get_backend_info(storage_type)
        except ValueError as e:
            raise StorageError(str(e))
    
    def get_all_storage_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有存储类型信息
        
        Returns:
            所有存储类型信息
        """
        return self.registry.get_all_backends_info()
    
    def _merge_config(self, storage_type: str, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            storage_type: 存储类型
            user_config: 用户配置
            
        Returns:
            合并后的配置
        """
        # 获取默认配置
        try:
            default_config = self.registry.get_backend_config(storage_type)
        except ValueError:
            default_config = {}
        
        # 合并全局默认配置
        merged_config = self.default_config.copy()
        merged_config.update(default_config)
        merged_config.update(user_config)
        
        return merged_config
    
    def _validate_config(self, storage_type: str, config: Dict[str, Any]) -> bool:
        """验证配置
        
        Args:
            storage_type: 存储类型
            config: 配置字典
            
        Returns:
            配置是否有效
        """
        try:
            # 使用注册表验证配置
            return self.registry.validate_backend_config(storage_type, config)
        except ValueError:
            return False
    
    def _generate_cache_key(self, storage_type: str, config: Dict[str, Any]) -> str:
        """生成缓存键
        
        Args:
            storage_type: 存储类型
            config: 配置字典
            
        Returns:
            缓存键
        """
        import hashlib
        import json
        
        # 将配置转换为JSON字符串
        config_str = json.dumps(config, sort_keys=True)
        
        # 生成哈希
        hash_obj = hashlib.md5(config_str.encode())
        config_hash = hash_obj.hexdigest()
        
        return f"{storage_type}_{config_hash}"
    
    def clear_cache(self, storage_type: Optional[str] = None) -> int:
        """清理缓存
        
        Args:
            storage_type: 存储类型，None表示清理所有缓存
            
        Returns:
            清理的实例数量
        """
        if storage_type is None:
            # 清理所有缓存
            count = len(self._instance_cache)
            self._instance_cache.clear()
            self._instance_configs.clear()
            logger.info(f"Cleared all cached storage instances ({count} instances)")
            return count
        else:
            # 清理指定类型的缓存
            keys_to_remove = [
                key for key in self._instance_cache.keys()
                if key.startswith(f"{storage_type}_")
            ]
            
            for key in keys_to_remove:
                self._instance_cache.pop(key, None)
                self._instance_configs.pop(key, None)
            
            logger.info(f"Cleared {len(keys_to_remove)} cached instances of type '{storage_type}'")
            return len(keys_to_remove)
    
    def get_cached_instances(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存的实例信息
        
        Returns:
            缓存实例信息字典
        """
        return {
            key: {
                "type": instance.__class__.__name__,
                "config": self._instance_configs.get(key, {}),
                "connected": getattr(instance, '_connected', False)
            }
            for key, instance in self._instance_cache.items()
        }
    
    def remove_cached_instance(self, cache_key: str) -> bool:
        """移除缓存的实例
        
        Args:
            cache_key: 缓存键
            
        Returns:
            是否成功移除
            
        Note:
            此方法不会断开异步连接。请使用 disconnect_all_cached_instances 进行异步断开
        """
        if cache_key in self._instance_cache:
            self._instance_cache.pop(cache_key, None)
            self._instance_configs.pop(cache_key, None)
            logger.info(f"Removed cached instance: {cache_key}")
            return True
        
        return False
    
    async def disconnect_all_cached_instances(self) -> int:
        """断开所有缓存实例的连接
        
        Returns:
            断开连接的实例数量
        """
        count = 0
        for cache_key, instance in list(self._instance_cache.items()):
            try:
                if hasattr(instance, 'disconnect'):
                    await instance.disconnect()
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to disconnect instance {cache_key}: {e}")
        
        logger.info(f"Disconnected {count} cached instances")
        return count
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """获取工厂统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "available_types": len(self.get_available_types()),
            "cached_instances": len(self._instance_cache),
            "registry_info": {
                "registered_backends": len(self.registry.list_backends()),
                "backend_details": {
                    name: {
                        "description": self.registry.get_backend_description(name),
                        "has_default_config": bool(self.registry.get_backend_config(name))
                    }
                    for name in self.registry.list_backends()
                }
            }
        }


# 全局存储工厂实例
_global_factory: Optional[StorageFactory] = None


def get_global_factory() -> StorageFactory:
    """获取全局存储工厂实例
    
    Returns:
        全局存储工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = StorageFactory()
    return _global_factory


def create_storage(
    storage_type: str,
    config: Optional[Dict[str, Any]] = None,
    cache_key: Optional[str] = None,
    use_cache: bool = True
) -> IStorage:
    """使用全局工厂创建存储实例
    
    Args:
        storage_type: 存储类型
        config: 存储配置
        cache_key: 缓存键
        use_cache: 是否使用缓存
        
    Returns:
        存储实例
    """
    factory = get_global_factory()
    return factory.create_storage(storage_type, config, cache_key, use_cache)


async def create_storage_async(
    storage_type: str,
    config: Optional[Dict[str, Any]] = None,
    cache_key: Optional[str] = None,
    use_cache: bool = True,
    auto_connect: bool = True
) -> IStorage:
    """使用全局工厂异步创建存储实例
    
    Args:
        storage_type: 存储类型
        config: 存储配置
        cache_key: 缓存键
        use_cache: 是否使用缓存
        auto_connect: 是否自动连接
        
    Returns:
        存储实例
    """
    factory = get_global_factory()
    return await factory.create_storage_async(
        storage_type, config, cache_key, use_cache, auto_connect
    )