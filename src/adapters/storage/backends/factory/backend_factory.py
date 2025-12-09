"""存储后端工厂

提供统一的存储后端创建和管理功能。
"""

import asyncio
from typing import Dict, Any, Optional, List, Type, Union
from src.services.logger.injection import get_logger

from src.interfaces.storage import IStorage, ISessionStorage, IThreadStorage, IStorageProvider
from ..core.base_backend import BaseStorageBackend

# 定义后端类型别名
BackendType = Union[Type[BaseStorageBackend], Type[ISessionStorage], Type[IThreadStorage]]
from ..providers.sqlite_provider import SQLiteProvider
from ..providers.file_provider import FileProvider
from ..providers.memory_provider import MemoryProvider
from ..impl import (
    SessionBackend,
    ThreadBackend
)


logger = get_logger(__name__)


class BackendRegistry:
    """后端注册表
    
    管理所有可用的存储后端类型，提供注册、查询和实例化功能。
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
        self._provider_registry["file"] = FileProvider
        self._provider_registry["memory"] = MemoryProvider
    
    def _register_default_backends(self) -> None:
        """注册默认后端"""
        # 会话存储后端
        self.register_backend(
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
        self.register_backend(
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
    
    def register_backend(
        self,
        name: str,
        backend_class: BackendType,
        description: str = "",
        default_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册存储后端
        
        Args:
            name: 后端名称
            backend_class: 后端类
            description: 后端描述
            default_config: 默认配置
        """
        if name in self._backends:
            raise ValueError(f"Backend '{name}' already registered")
        
        self._backends[name] = {
            "class": backend_class,
            "description": description,
            "default_config": default_config or {},
            "provider_type": default_config.get("provider_type") if default_config else None
        }
        
        logger.info(f"Registered storage backend: {name}")
    
    def unregister_backend(self, name: str) -> bool:
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
    
    def get_backend_info(self, name: str) -> Dict[str, Any]:
        """获取后端信息
        
        Args:
            name: 后端名称
            
        Returns:
            后端信息
            
        Raises:
            ValueError: 后端不存在时抛出
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        backend_info = self._backends[name].copy()
        backend_info["name"] = name
        return backend_info
    
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
        
        return self._backends[backend_name]["default_config"].get("provider_type")
    
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
    
    def create_backend_instance(self, name: str, config: Dict[str, Any]) -> Union[IStorage, ISessionStorage, IThreadStorage]:
        """创建后端实例
        
        Args:
            name: 后端名称
            config: 配置字典
            
        Returns:
            后端实例
            
        Raises:
            ValueError: 后端不存在或配置无效时抛出
        """
        if name not in self._backends:
            raise ValueError(f"Unknown storage backend: {name}")
        
        backend_info = self._backends[name]
        backend_class = backend_info["class"]
        default_config = backend_info["default_config"].copy()
        
        # 合并配置
        merged_config = default_config.copy()
        merged_config.update(config)
        
        # 获取提供者类型
        provider_type = merged_config.get("provider_type")
        if not provider_type:
            raise ValueError(f"No provider_type specified for backend: {name}")
        
        # 创建提供者
        provider_config = {k: v for k, v in merged_config.items() if k != "provider_type"}
        provider = self.create_provider(provider_type, provider_config)
        
        # 创建后端实例
        return backend_class(provider=provider, **merged_config)


class StorageBackendFactory:
    """存储后端工厂
    
    负责创建、配置和管理存储后端实例。
    """
    
    def __init__(
        self,
        registry: Optional[BackendRegistry] = None,
        default_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化存储后端工厂
        
        Args:
            registry: 后端注册表，默认使用全局注册表
            default_config: 默认配置
        """
        self.registry = registry or BackendRegistry()
        self.default_config = default_config or {}
        
        # 实例缓存
        self._instance_cache: Dict[str, Union[IStorage, ISessionStorage, IThreadStorage]] = {}
        
        # 实例配置记录
        self._instance_configs: Dict[str, Dict[str, Any]] = {}
    
    def create_backend(
        self,
        backend_type: str,
        config: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        use_cache: bool = True
    ) -> Union[IStorage, ISessionStorage, IThreadStorage]:
        """创建存储后端实例
        
        Args:
            backend_type: 后端类型
            config: 存储配置
            cache_key: 缓存键，None表示自动生成
            use_cache: 是否使用缓存
            
        Returns:
            存储后端实例
            
        Raises:
            ValueError: 配置无效或创建失败时抛出
        """
        # 合并配置
        merged_config = self._merge_config(backend_type, config or {})
        
        # 检查缓存
        if use_cache:
            if cache_key is None:
                cache_key = self._generate_cache_key(backend_type, merged_config)
            
            if cache_key in self._instance_cache:
                logger.info(f"Using cached backend instance: {cache_key}")
                return self._instance_cache[cache_key]
        
        try:
            # 创建实例
            instance = self.registry.create_backend_instance(backend_type, merged_config)
            
            # 缓存实例
            if use_cache and cache_key:
                self._instance_cache[cache_key] = instance
                self._instance_configs[cache_key] = merged_config.copy()
            
            logger.info(f"Created backend instance of type '{backend_type}'")
            return instance
            
        except Exception as e:
            raise ValueError(f"Failed to create backend instance: {e}")
    
    async def create_backend_async(
        self,
        backend_type: str,
        config: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        use_cache: bool = True,
        auto_connect: bool = True
    ) -> Union[IStorage, ISessionStorage, IThreadStorage]:
        """异步创建存储后端实例
        
        Args:
            backend_type: 后端类型
            config: 存储配置
            cache_key: 缓存键
            use_cache: 是否使用缓存
            auto_connect: 是否自动连接
            
        Returns:
            存储后端实例
        """
        # 创建实例
        instance = self.create_backend(backend_type, config, cache_key, use_cache)
        
        # 自动连接
        if auto_connect:
            try:
                await instance.connect()
                logger.info(f"Connected backend instance of type '{backend_type}'")
            except Exception as e:
                logger.warning(f"Failed to connect backend instance: {e}")
        
        return instance
    
    def register_backend(
        self,
        backend_type: str,
        backend_class: BackendType,
        description: str = "",
        default_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册后端类型
        
        Args:
            backend_type: 后端类型名称
            backend_class: 后端类
            description: 后端描述
            default_config: 默认配置
        """
        self.registry.register_backend(backend_type, backend_class, description, default_config)
    
    def get_available_types(self) -> List[str]:
        """获取可用的后端类型
        
        Returns:
            后端类型列表
        """
        return self.registry.list_backends()
    
    def is_type_available(self, backend_type: str) -> bool:
        """检查后端类型是否可用
        
        Args:
            backend_type: 后端类型名称
            
        Returns:
            是否可用
        """
        return backend_type in self.registry.list_backends()
    
    def get_backend_info(self, backend_type: str) -> Dict[str, Any]:
        """获取后端类型信息
        
        Args:
            backend_type: 后端类型名称
            
        Returns:
            后端类型信息
        """
        return self.registry.get_backend_info(backend_type)
    
    def get_all_backend_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有后端类型信息
        
        Returns:
            所有后端类型信息
        """
        return {
            name: self.registry.get_backend_info(name)
            for name in self.registry.list_backends()
        }
    
    def _merge_config(self, backend_type: str, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            backend_type: 后端类型
            user_config: 用户配置
            
        Returns:
            合并后的配置
        """
        # 获取后端默认配置
        backend_info = self.registry.get_backend_info(backend_type)
        default_config = backend_info["default_config"]
        
        # 合并全局默认配置
        merged_config = self.default_config.copy()
        merged_config.update(default_config)
        merged_config.update(user_config)
        
        return merged_config
    
    def _generate_cache_key(self, backend_type: str, config: Dict[str, Any]) -> str:
        """生成缓存键
        
        Args:
            backend_type: 后端类型
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
        
        return f"{backend_type}_{config_hash}"
    
    def clear_cache(self, backend_type: Optional[str] = None) -> int:
        """清理缓存
        
        Args:
            backend_type: 后端类型，None表示清理所有缓存
            
        Returns:
            清理的实例数量
        """
        if backend_type is None:
            # 清理所有缓存
            count = len(self._instance_cache)
            self._instance_cache.clear()
            self._instance_configs.clear()
            logger.info(f"Cleared all cached backend instances ({count} instances)")
            return count
        else:
            # 清理指定类型的缓存
            keys_to_remove = [
                key for key in self._instance_cache.keys()
                if key.startswith(f"{backend_type}_")
            ]
            
            for key in keys_to_remove:
                self._instance_cache.pop(key, None)
                self._instance_configs.pop(key, None)
            
            logger.info(f"Cleared {len(keys_to_remove)} cached instances of type '{backend_type}'")
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
                        "description": self.registry.get_backend_info(name)["description"],
                        "has_default_config": bool(self.registry.get_backend_info(name)["default_config"])
                    }
                    for name in self.registry.list_backends()
                }
            }
        }