# 存储类型注册和发现机制设计

## 概述

本文档设计存储类型的注册和发现机制，为Redis和PostgreSQL等新存储类型提供自动化的注册、发现和管理功能。

## 设计目标

1. **自动发现**: 自动发现可用的存储类型
2. **动态注册**: 支持运行时动态注册存储类型
3. **插件化**: 支持第三方存储类型插件
4. **依赖管理**: 自动检查和管理存储类型依赖
5. **版本控制**: 支持存储类型版本管理
6. **热插拔**: 支持存储类型的热插拔和卸载

## 架构设计

### 1. 核心组件架构

```
Storage Registry System
├── StorageTypeRegistry          # 存储类型注册表
├── StorageTypeDiscovery         # 存储类型发现器
├── StorageTypeLoader            # 存储类型加载器
├── StorageTypeValidator         # 存储类型验证器
├── StorageTypeMetadata          # 存储类型元数据
├── PluginManager                # 插件管理器
└── DependencyManager            # 依赖管理器
```

### 2. 注册表设计

#### 2.1 存储类型注册表接口

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
from enum import Enum

class StorageTypeStatus(Enum):
    """存储类型状态"""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"
    UNLOADING = "unloading"

@dataclass
class StorageTypeMetadata:
    """存储类型元数据"""
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: str
    repository: str
    tags: List[str]
    category: str
    features: List[str]
    dependencies: List[str]
    optional_dependencies: List[str]
    python_requires: str
    entry_point: str
    config_schema: Dict[str, Any]
    default_config: Dict[str, Any]
    health_check_method: Optional[str] = None
    migration_support: bool = False
    backup_support: bool = False
    replication_support: bool = False
    clustering_support: bool = False

@dataclass
class StorageTypeRegistration:
    """存储类型注册信息"""
    metadata: StorageTypeMetadata
    storage_class: Type
    factory_class: Optional[Type] = None
    status: StorageTypeStatus = StorageTypeStatus.REGISTERED
    registration_time: float = 0.0
    last_used: float = 0.0
    usage_count: int = 0
    error_message: Optional[str] = None
    config_validator: Optional[callable] = None

class IStorageTypeRegistry(ABC):
    """存储类型注册表接口"""
    
    @abstractmethod
    async def register_storage_type(
        self, 
        metadata: StorageTypeMetadata, 
        storage_class: Type,
        factory_class: Optional[Type] = None
    ) -> bool:
        """注册存储类型"""
        pass
    
    @abstractmethod
    async def unregister_storage_type(self, name: str, version: Optional[str] = None) -> bool:
        """注销存储类型"""
        pass
    
    @abstractmethod
    async def get_storage_type(self, name: str, version: Optional[str] = None) -> Optional[StorageTypeRegistration]:
        """获取存储类型"""
        pass
    
    @abstractmethod
    async def list_storage_types(self, status: Optional[StorageTypeStatus] = None) -> List[StorageTypeRegistration]:
        """列出存储类型"""
        pass
    
    @abstractmethod
    async def activate_storage_type(self, name: str, version: Optional[str] = None) -> bool:
        """激活存储类型"""
        pass
    
    @abstractmethod
    async def deactivate_storage_type(self, name: str, version: Optional[str] = None) -> bool:
        """停用存储类型"""
        pass
    
    @abstractmethod
    async def update_storage_type(self, name: str, version: str, metadata: StorageTypeMetadata) -> bool:
        """更新存储类型"""
        pass
    
    @abstractmethod
    async def get_storage_type_info(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取存储类型详细信息"""
        pass
```

#### 2.2 存储类型注册表实现

```python
import time
import asyncio
import logging
from typing import Dict, List, Optional, Type, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class StorageTypeRegistry(IStorageTypeRegistry):
    """存储类型注册表实现"""
    
    def __init__(self):
        self._registrations: Dict[str, Dict[str, StorageTypeRegistration]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._event_listeners: List[callable] = []
    
    async def register_storage_type(
        self, 
        metadata: StorageTypeMetadata, 
        storage_class: Type,
        factory_class: Optional[Type] = None
    ) -> bool:
        """注册存储类型"""
        async with self._lock:
            try:
                # 验证存储类
                self._validate_storage_class(storage_class)
                
                # 检查是否已存在
                if metadata.version in self._registrations[metadata.name]:
                    logger.warning(f"Storage type {metadata.name} v{metadata.version} already registered")
                    return False
                
                # 创建注册信息
                registration = StorageTypeRegistration(
                    metadata=metadata,
                    storage_class=storage_class,
                    factory_class=factory_class,
                    status=StorageTypeStatus.REGISTERED,
                    registration_time=time.time()
                )
                
                # 注册
                self._registrations[metadata.name][metadata.version] = registration
                
                # 触发事件
                await self._trigger_event("storage_type_registered", registration)
                
                logger.info(f"Registered storage type: {metadata.name} v{metadata.version}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register storage type {metadata.name}: {e}")
                return False
    
    async def unregister_storage_type(self, name: str, version: Optional[str] = None) -> bool:
        """注销存储类型"""
        async with self._lock:
            try:
                if name not in self._registrations:
                    logger.warning(f"Storage type {name} not found")
                    return False
                
                if version:
                    # 注销特定版本
                    if version not in self._registrations[name]:
                        logger.warning(f"Storage type {name} v{version} not found")
                        return False
                    
                    registration = self._registrations[name].pop(version)
                    await self._trigger_event("storage_type_unregistered", registration)
                    
                    # 如果没有其他版本，删除整个条目
                    if not self._registrations[name]:
                        del self._registrations[name]
                else:
                    # 注销所有版本
                    for version, registration in self._registrations[name].items():
                        await self._trigger_event("storage_type_unregistered", registration)
                    
                    del self._registrations[name]
                
                logger.info(f"Unregistered storage type: {name}" + (f" v{version}" if version else ""))
                return True
                
            except Exception as e:
                logger.error(f"Failed to unregister storage type {name}: {e}")
                return False
    
    async def get_storage_type(self, name: str, version: Optional[str] = None) -> Optional[StorageTypeRegistration]:
        """获取存储类型"""
        async with self._lock:
            if name not in self._registrations:
                return None
            
            if version:
                return self._registrations[name].get(version)
            else:
                # 返回最新版本
                versions = list(self._registrations[name].keys())
                if versions:
                    latest_version = max(versions, key=self._version_key)
                    return self._registrations[name][latest_version]
                return None
    
    async def list_storage_types(self, status: Optional[StorageTypeStatus] = None) -> List[StorageTypeRegistration]:
        """列出存储类型"""
        async with self._lock:
            registrations = []
            
            for name_versions in self._registrations.values():
                for registration in name_versions.values():
                    if status is None or registration.status == status:
                        registrations.append(registration)
            
            return registrations
    
    async def activate_storage_type(self, name: str, version: Optional[str] = None) -> bool:
        """激活存储类型"""
        async with self._lock:
            registration = await self.get_storage_type(name, version)
            if not registration:
                logger.error(f"Storage type {name} not found")
                return False
            
            try:
                # 验证依赖
                await self._validate_dependencies(registration.metadata)
                
                # 更新状态
                old_status = registration.status
                registration.status = StorageTypeStatus.ACTIVE
                registration.error_message = None
                
                # 触发事件
                await self._trigger_event("storage_type_activated", registration, old_status)
                
                logger.info(f"Activated storage type: {name} v{registration.metadata.version}")
                return True
                
            except Exception as e:
                registration.status = StorageTypeStatus.ERROR
                registration.error_message = str(e)
                logger.error(f"Failed to activate storage type {name}: {e}")
                return False
    
    async def deactivate_storage_type(self, name: str, version: Optional[str] = None) -> bool:
        """停用存储类型"""
        async with self._lock:
            registration = await self.get_storage_type(name, version)
            if not registration:
                logger.error(f"Storage type {name} not found")
                return False
            
            old_status = registration.status
            registration.status = StorageTypeStatus.INACTIVE
            registration.error_message = None
            
            # 触发事件
            await self._trigger_event("storage_type_deactivated", registration, old_status)
            
            logger.info(f"Deactivated storage type: {name} v{registration.metadata.version}")
            return True
    
    async def update_storage_type(self, name: str, version: str, metadata: StorageTypeMetadata) -> bool:
        """更新存储类型"""
        async with self._lock:
            if name not in self._registrations or version not in self._registrations[name]:
                logger.error(f"Storage type {name} v{version} not found")
                return False
            
            registration = self._registrations[name][version]
            old_metadata = registration.metadata
            registration.metadata = metadata
            
            # 触发事件
            await self._trigger_event("storage_type_updated", registration, old_metadata)
            
            logger.info(f"Updated storage type: {name} v{version}")
            return True
    
    async def get_storage_type_info(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取存储类型详细信息"""
        registration = await self.get_storage_type(name, version)
        if not registration:
            return None
        
        return {
            "name": registration.metadata.name,
            "version": registration.metadata.version,
            "description": registration.metadata.description,
            "author": registration.metadata.author,
            "license": registration.metadata.license,
            "homepage": registration.metadata.homepage,
            "repository": registration.metadata.repository,
            "tags": registration.metadata.tags,
            "category": registration.metadata.category,
            "features": registration.metadata.features,
            "dependencies": registration.metadata.dependencies,
            "optional_dependencies": registration.metadata.optional_dependencies,
            "python_requires": registration.metadata.python_requires,
            "status": registration.status.value,
            "registration_time": registration.registration_time,
            "last_used": registration.last_used,
            "usage_count": registration.usage_count,
            "error_message": registration.error_message,
            "config_schema": registration.metadata.config_schema,
            "default_config": registration.metadata.default_config,
            "health_check_method": registration.metadata.health_check_method,
            "migration_support": registration.metadata.migration_support,
            "backup_support": registration.metadata.backup_support,
            "replication_support": registration.metadata.replication_support,
            "clustering_support": registration.metadata.clustering_support,
        }
    
    def _validate_storage_class(self, storage_class: Type) -> None:
        """验证存储类"""
        from ...adapters.storage.backends.base import StorageBackend
        
        if not issubclass(storage_class, StorageBackend):
            raise ValueError(f"Storage class must inherit from StorageBackend")
    
    async def _validate_dependencies(self, metadata: StorageTypeMetadata) -> None:
        """验证依赖"""
        dependency_manager = DependencyManager()
        
        # 检查必需依赖
        for dependency in metadata.dependencies:
            if not await dependency_manager.is_dependency_satisfied(dependency):
                raise ValueError(f"Required dependency not satisfied: {dependency}")
    
    def _version_key(self, version: str) -> tuple:
        """版本排序键"""
        try:
            return tuple(map(int, version.split('.')))
        except ValueError:
            return (0, 0, 0)
    
    async def _trigger_event(self, event_name: str, *args, **kwargs) -> None:
        """触发事件"""
        for listener in self._event_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event_name, *args, **kwargs)
                else:
                    listener(event_name, *args, **kwargs)
            except Exception as e:
                logger.error(f"Event listener error: {e}")
    
    def add_event_listener(self, listener: callable) -> None:
        """添加事件监听器"""
        self._event_listeners.append(listener)
    
    def remove_event_listener(self, listener: callable) -> None:
        """移除事件监听器"""
        if listener in self._event_listeners:
            self._event_listeners.remove(listener)
```

### 3. 存储类型发现器

#### 3.1 发现器接口

```python
class IStorageTypeDiscovery(ABC):
    """存储类型发现器接口"""
    
    @abstractmethod
    async def discover_storage_types(self) -> List[StorageTypeMetadata]:
        """发现存储类型"""
        pass
    
    @abstractmethod
    async def scan_directory(self, directory: str) -> List[StorageTypeMetadata]:
        """扫描目录"""
        pass
    
    @abstractmethod
    async def scan_package(self, package_name: str) -> List[StorageTypeMetadata]:
        """扫描包"""
        pass
    
    @abstractmethod
    async def load_from_entry_points(self, group: str) -> List[StorageTypeMetadata]:
        """从入口点加载"""
        pass
```

#### 3.2 发现器实现

```python
import os
import importlib
import importlib.util
import pkg_resources
from pathlib import Path
from typing import List, Dict, Any

class StorageTypeDiscovery(IStorageTypeDiscovery):
    """存储类型发现器实现"""
    
    def __init__(self, registry: IStorageTypeRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)
    
    async def discover_storage_types(self) -> List[StorageTypeMetadata]:
        """发现存储类型"""
        discovered_types = []
        
        # 扫描内置存储类型
        builtin_types = await self._discover_builtin_types()
        discovered_types.extend(builtin_types)
        
        # 从入口点发现
        entry_point_types = await self.load_from_entry_points("storage.backends")
        discovered_types.extend(entry_point_types)
        
        # 扫描配置目录
        config_types = await self._scan_config_directories()
        discovered_types.extend(config_types)
        
        # 扫描插件目录
        plugin_types = await self._scan_plugin_directories()
        discovered_types.extend(plugin_types)
        
        return discovered_types
    
    async def scan_directory(self, directory: str) -> List[StorageTypeMetadata]:
        """扫描目录"""
        discovered_types = []
        
        if not os.path.exists(directory):
            return discovered_types
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    try:
                        metadata = await self._load_from_file(file_path)
                        if metadata:
                            discovered_types.append(metadata)
                    except Exception as e:
                        self.logger.error(f"Failed to load storage type from {file_path}: {e}")
        
        return discovered_types
    
    async def scan_package(self, package_name: str) -> List[StorageTypeMetadata]:
        """扫描包"""
        discovered_types = []
        
        try:
            package = importlib.import_module(package_name)
            package_path = package.__path__
            
            for root, dirs, files in os.walk(package_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        file_path = os.path.join(root, file)
                        try:
                            metadata = await self._load_from_file(file_path)
                            if metadata:
                                discovered_types.append(metadata)
                        except Exception as e:
                            self.logger.error(f"Failed to load storage type from {file_path}: {e}")
        
        except ImportError as e:
            self.logger.error(f"Failed to import package {package_name}: {e}")
        
        return discovered_types
    
    async def load_from_entry_points(self, group: str) -> List[StorageTypeMetadata]:
        """从入口点加载"""
        discovered_types = []
        
        try:
            for entry_point in pkg_resources.iter_entry_points(group):
                try:
                    metadata = await self._load_from_entry_point(entry_point)
                    if metadata:
                        discovered_types.append(metadata)
                except Exception as e:
                    self.logger.error(f"Failed to load entry point {entry_point.name}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to load entry points from group {group}: {e}")
        
        return discovered_types
    
    async def _discover_builtin_types(self) -> List[StorageTypeMetadata]:
        """发现内置存储类型"""
        builtin_types = []
        
        # Redis存储类型
        redis_metadata = StorageTypeMetadata(
            name="redis",
            version="1.0.0",
            description="Redis分布式存储后端",
            author="Storage Team",
            license="MIT",
            homepage="https://github.com/example/storage-redis",
            repository="https://github.com/example/storage-redis.git",
            tags=["redis", "nosql", "distributed", "cache"],
            category="nosql",
            features=["distributed", "persistent", "clustered", "high_performance"],
            dependencies=["redis>=5.0.0"],
            optional_dependencies=["msgpack>=1.0.0", "lz4>=4.0.0"],
            python_requires=">=3.8",
            entry_point="src.adapters.storage.backends.redis_backend:RedisStorageBackend",
            config_schema={},  # 从配置文件加载
            default_config={},  # 从配置文件加载
            health_check_method="health_check_impl",
            migration_support=False,
            backup_support=True,
            replication_support=True,
            clustering_support=True,
        )
        builtin_types.append(redis_metadata)
        
        # PostgreSQL存储类型
        postgresql_metadata = StorageTypeMetadata(
            name="postgresql",
            version="1.0.0",
            description="PostgreSQL企业级存储后端",
            author="Storage Team",
            license="MIT",
            homepage="https://github.com/example/storage-postgresql",
            repository="https://github.com/example/storage-postgresql.git",
            tags=["postgresql", "sql", "database", "enterprise"],
            category="database",
            features=["acid", "transactional", "indexed", "partitioning", "replication"],
            dependencies=["asyncpg>=0.28.0", "sqlalchemy[asyncio]>=2.0.0", "alembic>=1.10.0"],
            optional_dependencies=["psycopg2-binary>=2.9.0", "pgspecial>=2.0.0"],
            python_requires=">=3.8",
            entry_point="src.adapters.storage.backends.postgresql_backend:PostgreSQLStorageBackend",
            config_schema={},  # 从配置文件加载
            default_config={},  # 从配置文件加载
            health_check_method="health_check_impl",
            migration_support=True,
            backup_support=True,
            replication_support=True,
            clustering_support=False,
        )
        builtin_types.append(postgresql_metadata)
        
        return builtin_types
    
    async def _scan_config_directories(self) -> List[StorageTypeMetadata]:
        """扫描配置目录"""
        discovered_types = []
        
        config_directories = [
            "configs/storage/types",
            "configs/storage/backends",
            "/etc/storage/types",
            "/usr/local/etc/storage/types",
        ]
        
        for directory in config_directories:
            if os.path.exists(directory):
                types = await self.scan_directory(directory)
                discovered_types.extend(types)
        
        return discovered_types
    
    async def _scan_plugin_directories(self) -> List[StorageTypeMetadata]:
        """扫描插件目录"""
        discovered_types = []
        
        plugin_directories = [
            "plugins/storage",
            "src/plugins/storage",
            "/usr/local/lib/storage/plugins",
        ]
        
        for directory in plugin_directories:
            if os.path.exists(directory):
                types = await self.scan_directory(directory)
                discovered_types.extend(types)
        
        return discovered_types
    
    async def _load_from_file(self, file_path: str) -> Optional[StorageTypeMetadata]:
        """从文件加载存储类型"""
        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location("storage_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找存储类型元数据
            if hasattr(module, 'STORAGE_TYPE_METADATA'):
                return module.STORAGE_TYPE_METADATA
            
            # 查找存储类并推断元数据
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.endswith('StorageBackend') and
                    hasattr(attr, '__module__')):
                    
                    # 从类推断元数据
                    return await self._infer_metadata_from_class(attr, file_path)
        
        except Exception as e:
            self.logger.error(f"Failed to load storage type from {file_path}: {e}")
        
        return None
    
    async def _load_from_entry_point(self, entry_point) -> Optional[StorageTypeMetadata]:
        """从入口点加载存储类型"""
        try:
            # 加载入口点
            storage_class = entry_point.load()
            
            # 查找元数据
            if hasattr(storage_class, 'STORAGE_TYPE_METADATA'):
                return storage_class.STORAGE_TYPE_METADATA
            
            # 从类推断元数据
            return await self._infer_metadata_from_class(storage_class, entry_point.module_name)
        
        except Exception as e:
            self.logger.error(f"Failed to load entry point {entry_point.name}: {e}")
        
        return None
    
    async def _infer_metadata_from_class(self, storage_class: Type, source: str) -> Optional[StorageTypeMetadata]:
        """从类推断元数据"""
        try:
            class_name = storage_class.__name__
            
            # 从类名推断存储类型名称
            if class_name.endswith('StorageBackend'):
                name = class_name[:-14].lower()
            else:
                name = class_name.lower()
            
            # 基础元数据
            metadata = StorageTypeMetadata(
                name=name,
                version="1.0.0",
                description=f"{name} storage backend",
                author="Unknown",
                license="Unknown",
                homepage="",
                repository="",
                tags=[name],
                category="unknown",
                features=[],
                dependencies=[],
                optional_dependencies=[],
                python_requires=">=3.8",
                entry_point=f"{storage_class.__module__}:{class_name}",
                config_schema={},
                default_config={},
            )
            
            return metadata
        
        except Exception as e:
            self.logger.error(f"Failed to infer metadata from class {storage_class}: {e}")
        
        return None
```

### 4. 存储类型加载器

#### 4.1 加载器接口

```python
class IStorageTypeLoader(ABC):
    """存储类型加载器接口"""
    
    @abstractmethod
    async def load_storage_type(self, metadata: StorageTypeMetadata) -> Optional[Type]:
        """加载存储类型"""
        pass
    
    @abstractmethod
    async def unload_storage_type(self, metadata: StorageTypeMetadata) -> bool:
        """卸载存储类型"""
        pass
    
    @abstractmethod
    async def reload_storage_type(self, metadata: StorageTypeMetadata) -> Optional[Type]:
        """重新加载存储类型"""
        pass
    
    @abstractmethod
    async def is_storage_type_loaded(self, metadata: StorageTypeMetadata) -> bool:
        """检查存储类型是否已加载"""
        pass
```

#### 4.2 加载器实现

```python
class StorageTypeLoader(IStorageTypeLoader):
    """存储类型加载器实现"""
    
    def __init__(self, registry: IStorageTypeRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)
        self._loaded_modules: Dict[str, Any] = {}
    
    async def load_storage_type(self, metadata: StorageTypeMetadata) -> Optional[Type]:
        """加载存储类型"""
        try:
            # 检查依赖
            await self._check_dependencies(metadata)
            
            # 加载模块
            module_path, class_name = metadata.entry_point.split(':')
            module = await self._load_module(module_path)
            
            # 获取存储类
            storage_class = getattr(module, class_name)
            
            # 验证存储类
            self._validate_storage_class(storage_class)
            
            # 缓存模块
            self._loaded_modules[metadata.entry_point] = module
            
            self.logger.info(f"Loaded storage type: {metadata.name} v{metadata.version}")
            return storage_class
        
        except Exception as e:
            self.logger.error(f"Failed to load storage type {metadata.name}: {e}")
            return None
    
    async def unload_storage_type(self, metadata: StorageTypeMetadata) -> bool:
        """卸载存储类型"""
        try:
            entry_point = metadata.entry_point
            
            if entry_point in self._loaded_modules:
                # 从缓存中移除
                del self._loaded_modules[entry_point]
                
                # 清理模块缓存（如果可能）
                module_path, class_name = entry_point.split(':')
                if module_path in sys.modules:
                    del sys.modules[module_path]
                
                self.logger.info(f"Unloaded storage type: {metadata.name} v{metadata.version}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to unload storage type {metadata.name}: {e}")
            return False
    
    async def reload_storage_type(self, metadata: StorageTypeMetadata) -> Optional[Type]:
        """重新加载存储类型"""
        try:
            # 先卸载
            await self.unload_storage_type(metadata)
            
            # 再加载
            return await self.load_storage_type(metadata)
        
        except Exception as e:
            self.logger.error(f"Failed to reload storage type {metadata.name}: {e}")
            return None
    
    async def is_storage_type_loaded(self, metadata: StorageTypeMetadata) -> bool:
        """检查存储类型是否已加载"""
        return metadata.entry_point in self._loaded_modules
    
    async def _check_dependencies(self, metadata: StorageTypeMetadata) -> None:
        """检查依赖"""
        dependency_manager = DependencyManager()
        
        # 检查必需依赖
        for dependency in metadata.dependencies:
            if not await dependency_manager.is_dependency_satisfied(dependency):
                raise ImportError(f"Required dependency not satisfied: {dependency}")
        
        # 检查Python版本
        if metadata.python_requires:
            if not await dependency_manager.check_python_version(metadata.python_requires):
                raise RuntimeError(f"Python version {metadata.python_requires} required")
    
    async def _load_module(self, module_path: str) -> Any:
        """加载模块"""
        if module_path in self._loaded_modules:
            return self._loaded_modules[module_path]
        
        # 动态导入模块
        module = importlib.import_module(module_path)
        return module
    
    def _validate_storage_class(self, storage_class: Type) -> None:
        """验证存储类"""
        from ...adapters.storage.backends.base import StorageBackend
        
        if not issubclass(storage_class, StorageBackend):
            raise ValueError(f"Storage class must inherit from StorageBackend")
```

### 5. 插件管理器

#### 5.1 插件管理器接口

```python
class IPluginManager(ABC):
    """插件管理器接口"""
    
    @abstractmethod
    async def install_plugin(self, plugin_path: str) -> bool:
        """安装插件"""
        pass
    
    @abstractmethod
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        pass
    
    @abstractmethod
    async def list_plugins(self) -> List[Dict[str, Any]]:
        """列出插件"""
        pass
    
    @abstractmethod
    async def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        pass
    
    @abstractmethod
    async def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        pass
    
    @abstractmethod
    async def update_plugin(self, plugin_name: str) -> bool:
        """更新插件"""
        pass
```

#### 5.2 插件管理器实现

```python
import json
import shutil
import tempfile
from pathlib import Path

class PluginManager(IPluginManager):
    """插件管理器实现"""
    
    def __init__(self, registry: IStorageTypeRegistry, plugin_dir: str = "plugins"):
        self.registry = registry
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def install_plugin(self, plugin_path: str) -> bool:
        """安装插件"""
        try:
            plugin_path = Path(plugin_path)
            
            if plugin_path.is_file() and plugin_path.suffix == '.zip':
                # 从ZIP文件安装
                return await self._install_from_zip(plugin_path)
            elif plugin_path.is_dir():
                # 从目录安装
                return await self._install_from_directory(plugin_path)
            else:
                self.logger.error(f"Unsupported plugin format: {plugin_path}")
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to install plugin from {plugin_path}: {e}")
            return False
    
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        try:
            # 停用插件
            await self.disable_plugin(plugin_name)
            
            # 注销存储类型
            plugin_dir = self.plugin_dir / plugin_name
            if plugin_dir.exists():
                # 扫描插件中的存储类型
                discovery = StorageTypeDiscovery(self.registry)
                types = await discovery.scan_directory(str(plugin_dir))
                
                for metadata in types:
                    await self.registry.unregister_storage_type(metadata.name, metadata.version)
            
            # 删除插件目录
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
            
            # 清理元数据
            if plugin_name in self._plugin_metadata:
                del self._plugin_metadata[plugin_name]
            
            self.logger.info(f"Uninstalled plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to uninstall plugin {plugin_name}: {e}")
            return False
    
    async def list_plugins(self) -> List[Dict[str, Any]]:
        """列出插件"""
        plugins = []
        
        for plugin_dir in self.plugin_dir.iterdir():
            if plugin_dir.is_dir():
                plugin_info = await self._get_plugin_info(plugin_dir)
                if plugin_info:
                    plugins.append(plugin_info)
        
        return plugins
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        try:
            plugin_dir = self.plugin_dir / plugin_name
            if not plugin_dir.exists():
                self.logger.error(f"Plugin {plugin_name} not found")
                return False
            
            # 发现并注册存储类型
            discovery = StorageTypeDiscovery(self.registry)
            types = await discovery.scan_directory(str(plugin_dir))
            
            loader = StorageTypeLoader(self.registry)
            
            for metadata in types:
                # 加载存储类型
                storage_class = await loader.load_storage_type(metadata)
                if storage_class:
                    # 注册存储类型
                    await self.registry.register_storage_type(metadata, storage_class)
                    
                    # 激活存储类型
                    await self.registry.activate_storage_type(metadata.name, metadata.version)
            
            # 更新插件状态
            if plugin_name in self._plugin_metadata:
                self._plugin_metadata[plugin_name]['enabled'] = True
            
            self.logger.info(f"Enabled plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to enable plugin {plugin_name}: {e}")
            return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        try:
            # 获取插件的存储类型
            plugin_dir = self.plugin_dir / plugin_name
            if plugin_dir.exists():
                discovery = StorageTypeDiscovery(self.registry)
                types = await discovery.scan_directory(str(plugin_dir))
                
                for metadata in types:
                    # 停用存储类型
                    await self.registry.deactivate_storage_type(metadata.name, metadata.version)
            
            # 更新插件状态
            if plugin_name in self._plugin_metadata:
                self._plugin_metadata[plugin_name]['enabled'] = False
            
            self.logger.info(f"Disabled plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to disable plugin {plugin_name}: {e}")
            return False
    
    async def update_plugin(self, plugin_name: str) -> bool:
        """更新插件"""
        try:
            # 获取当前插件信息
            plugin_info = self._plugin_metadata.get(plugin_name)
            if not plugin_info:
                self.logger.error(f"Plugin {plugin_name} not found")
                return False
            
            # 备份当前插件
            backup_dir = self.plugin_dir / f"{plugin_name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(self.plugin_dir / plugin_name, backup_dir)
            
            try:
                # 下载更新（这里需要实现具体的更新逻辑）
                # await self._download_plugin_update(plugin_name, plugin_info['version'])
                
                # 重新安装
                await self.disable_plugin(plugin_name)
                await self.enable_plugin(plugin_name)
                
                # 删除备份
                shutil.rmtree(backup_dir)
                
                self.logger.info(f"Updated plugin: {plugin_name}")
                return True
            
            except Exception as e:
                # 恢复备份
                if backup_dir.exists():
                    shutil.rmtree(self.plugin_dir / plugin_name)
                    shutil.move(backup_dir, self.plugin_dir / plugin_name)
                    await self.enable_plugin(plugin_name)
                
                raise e
        
        except Exception as e:
            self.logger.error(f"Failed to update plugin {plugin_name}: {e}")
            return False
    
    async def _install_from_zip(self, zip_path: Path) -> bool:
        """从ZIP文件安装插件"""
        import zipfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找插件目录
            temp_path = Path(temp_dir)
            plugin_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
            
            if not plugin_dirs:
                self.logger.error("No plugin directory found in ZIP file")
                return False
            
            # 安装第一个插件目录
            plugin_dir = plugin_dirs[0]
            return await self._install_from_directory(plugin_dir)
    
    async def _install_from_directory(self, plugin_dir: Path) -> bool:
        """从目录安装插件"""
        try:
            # 读取插件元数据
            metadata_file = plugin_dir / "plugin.json"
            if not metadata_file.exists():
                self.logger.error("Plugin metadata file not found")
                return False
            
            with open(metadata_file, 'r') as f:
                plugin_metadata = json.load(f)
            
            plugin_name = plugin_metadata['name']
            
            # 检查插件是否已存在
            target_dir = self.plugin_dir / plugin_name
            if target_dir.exists():
                self.logger.error(f"Plugin {plugin_name} already exists")
                return False
            
            # 复制插件文件
            shutil.copytree(plugin_dir, target_dir)
            
            # 保存插件元数据
            self._plugin_metadata[plugin_name] = plugin_metadata
            
            self.logger.info(f"Installed plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to install plugin from {plugin_dir}: {e}")
            return False
    
    async def _get_plugin_info(self, plugin_dir: Path) -> Optional[Dict[str, Any]]:
        """获取插件信息"""
        try:
            metadata_file = plugin_dir / "plugin.json"
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                plugin_metadata = json.load(f)
            
            # 添加状态信息
            plugin_metadata['enabled'] = plugin_metadata.get('enabled', False)
            plugin_metadata['installed'] = True
            plugin_metadata['path'] = str(plugin_dir)
            
            return plugin_metadata
        
        except Exception as e:
            self.logger.error(f"Failed to get plugin info from {plugin_dir}: {e}")
            return None
```

### 6. 依赖管理器

```python
import sys
import subprocess
from typing import List, Dict, Any

class DependencyManager:
    """依赖管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def is_dependency_satisfied(self, dependency: str) -> bool:
        """检查依赖是否满足"""
        try:
            import pkg_resources
            
            # 解析依赖规范
            requirement = pkg_resources.Requirement.parse(dependency)
            
            # 检查是否已安装
            pkg_resources.get_distribution(requirement.name)
            
            return True
        
        except pkg_resources.DistributionNotFound:
            return False
        except pkg_resources.VersionConflict:
            return False
        except Exception as e:
            self.logger.error(f"Error checking dependency {dependency}: {e}")
            return False
    
    async def install_dependency(self, dependency: str) -> bool:
        """安装依赖"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dependency],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully installed dependency: {dependency}")
                return True
            else:
                self.logger.error(f"Failed to install dependency {dependency}: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout installing dependency: {dependency}")
            return False
        except Exception as e:
            self.logger.error(f"Error installing dependency {dependency}: {e}")
            return False
    
    async def check_python_version(self, version_spec: str) -> bool:
        """检查Python版本"""
        try:
            import pkg_resources
            
            # 解析版本规范
            requirement = pkg_resources.Requirement.parse(f"python{version_spec}")
            
            # 检查当前Python版本
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            return current_version in requirement
        
        except Exception as e:
            self.logger.error(f"Error checking Python version {version_spec}: {e}")
            return False
    
    async def get_dependency_info(self, dependency: str) -> Optional[Dict[str, Any]]:
        """获取依赖信息"""
        try:
            import pkg_resources
            
            requirement = pkg_resources.Requirement.parse(dependency)
            
            try:
                dist = pkg_resources.get_distribution(requirement.name)
                
                return {
                    "name": dist.project_name,
                    "version": dist.version,
                    "location": dist.location,
                    "requires": [str(req) for req in dist.requires()] if dist.requires() else [],
                    "satisfied": str(dist.version) in requirement,
                }
            
            except pkg_resources.DistributionNotFound:
                return {
                    "name": requirement.name,
                    "version": None,
                    "location": None,
                    "requires": [],
                    "satisfied": False,
                }
        
        except Exception as e:
            self.logger.error(f"Error getting dependency info for {dependency}: {e}")
            return None
```

### 7. 使用示例

```python
async def main():
    """主函数示例"""
    # 创建注册表
    registry = StorageTypeRegistry()
    
    # 创建发现器
    discovery = StorageTypeDiscovery(registry)
    
    # 创建加载器
    loader = StorageTypeLoader(registry)
    
    # 创建插件管理器
    plugin_manager = PluginManager(registry)
    
    # 发现存储类型
    discovered_types = await discovery.discover_storage_types()
    print(f"Discovered {len(discovered_types)} storage types")
    
    # 注册存储类型
    for metadata in discovered_types:
        storage_class = await loader.load_storage_type(metadata)
        if storage_class:
            await registry.register_storage_type(metadata, storage_class)
            await registry.activate_storage_type(metadata.name, metadata.version)
    
    # 列出已注册的存储类型
    registered_types = await registry.list_storage_types(StorageTypeStatus.ACTIVE)
    print(f"Active storage types: {[reg.metadata.name for reg in registered_types]}")
    
    # 安装插件
    await plugin_manager.install_plugin("path/to/plugin.zip")
    
    # 列出插件
    plugins = await plugin_manager.list_plugins()
    print(f"Installed plugins: {[plugin['name'] for plugin in plugins]}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 总结

存储类型注册和发现机制提供了：

1. **自动发现**: 自动发现内置、插件和配置中的存储类型
2. **动态注册**: 支持运行时注册和注销存储类型
3. **插件化**: 完整的插件管理系统
4. **依赖管理**: 自动检查和管理依赖关系
5. **版本控制**: 支持多版本存储类型管理
6. **热插拔**: 支持存储类型的动态加载和卸载

该机制为存储系统提供了强大的扩展能力，使得添加新的存储类型变得简单而可靠。