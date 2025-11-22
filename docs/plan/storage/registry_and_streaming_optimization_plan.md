# 存储注册表与流式操作优化方案

## 概述

本文档提供了针对新架构存储系统中注册表功能和流式操作的优化方案，旨在提升系统的可扩展性和性能，同时保持架构的简洁性。

## 1. 注册表功能优化方案

### 1.1 当前问题分析

新架构中的存储类型注册机制简化为工厂类中的硬编码支持类型，存在以下限制：

1. **扩展性限制**: 添加新存储类型需要修改工厂类代码
2. **插件化支持不足**: 无法在运行时动态注册新的存储类型
3. **元数据管理缺失**: 没有存储类型的元数据管理功能

### 1.2 优化方案设计

#### 1.2.1 轻量级注册表实现

创建一个轻量级的存储注册表，支持动态注册和配置文件加载：

```python
# src/adapters/storage/registry.py

from typing import Dict, Type, Any, List, Optional, Callable
import importlib
import inspect
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageRegistry:
    """轻量级存储注册表
    
    提供存储类型的注册、发现和管理功能，支持插件化架构。
    """
    
    def __init__(self):
        """初始化存储注册表"""
        self._storage_classes: Dict[str, Type] = {}
        self._storage_metadata: Dict[str, Dict[str, Any]] = {}
        self._storage_factories: Dict[str, Callable] = {}
        self._auto_loaded = False
    
    def register(
        self, 
        storage_type: str, 
        storage_class: Type, 
        metadata: Optional[Dict[str, Any]] = None,
        factory: Optional[Callable] = None
    ) -> None:
        """注册存储类型
        
        Args:
            storage_type: 存储类型名称
            storage_class: 存储类
            metadata: 存储元数据
            factory: 工厂函数（可选）
        """
        try:
            # 验证存储类
            self._validate_storage_class(storage_class)
            
            # 注册存储类
            self._storage_classes[storage_type] = storage_class
            
            # 注册元数据
            self._storage_metadata[storage_type] = metadata or {}
            
            # 注册工厂函数
            if factory:
                self._storage_factories[storage_type] = factory
            
            logger.info(f"Registered storage type '{storage_type}'")
            
        except Exception as e:
            logger.error(f"Failed to register storage type '{storage_type}': {e}")
            raise
    
    def unregister(self, storage_type: str) -> bool:
        """注销存储类型"""
        if storage_type in self._storage_classes:
            del self._storage_classes[storage_type]
            if storage_type in self._storage_metadata:
                del self._storage_metadata[storage_type]
            if storage_type in self._storage_factories:
                del self._storage_factories[storage_type]
            logger.info(f"Unregistered storage type '{storage_type}'")
            return True
        return False
    
    def get_storage_class(self, storage_type: str) -> Type:
        """获取存储类"""
        if storage_type not in self._storage_classes:
            self._load_builtin_types()
            
        if storage_type not in self._storage_classes:
            raise ValueError(f"Storage type '{storage_type}' is not registered")
        
        return self._storage_classes[storage_type]
    
    def get_storage_metadata(self, storage_type: str) -> Dict[str, Any]:
        """获取存储元数据"""
        if storage_type not in self._storage_metadata:
            raise ValueError(f"Storage type '{storage_type}' is not registered")
        
        return self._storage_metadata[storage_type].copy()
    
    def get_storage_factory(self, storage_type: str) -> Optional[Callable]:
        """获取存储工厂函数"""
        return self._storage_factories.get(storage_type)
    
    def get_registered_types(self) -> List[str]:
        """获取已注册的存储类型列表"""
        self._load_builtin_types()
        return list(self._storage_classes.keys())
    
    def is_registered(self, storage_type: str) -> bool:
        """检查存储类型是否已注册"""
        self._load_builtin_types()
        return storage_type in self._storage_classes
    
    def load_from_config(self, config_path: str) -> None:
        """从配置文件加载存储类型
        
        Args:
            config_path: 配置文件路径
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {config_path}")
                return
            
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            for storage_type, storage_config in config.get('storage_types', {}).items():
                if 'module' in storage_config:
                    self._register_from_module(
                        storage_type, 
                        storage_config['module'],
                        storage_config.get('metadata'),
                        storage_config.get('factory')
                    )
                elif 'class' in storage_config:
                    self._register_from_class_path(
                        storage_type,
                        storage_config['class'],
                        storage_config.get('metadata'),
                        storage_config.get('factory')
                    )
            
            logger.info(f"Loaded storage types from config: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load storage types from config: {e}")
    
    def _register_from_module(
        self, 
        storage_type: str, 
        module_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        factory_path: Optional[str] = None
    ) -> None:
        """从模块注册存储类型"""
        try:
            module = importlib.import_module(module_path)
            
            # 查找存储类
            storage_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if self._is_storage_class(obj):
                    storage_class = obj
                    break
            
            if storage_class is None:
                raise ValueError(f"No storage class found in module '{module_path}'")
            
            # 获取工厂函数
            factory = None
            if factory_path:
                factory_module_path, factory_name = factory_path.rsplit(".", 1)
                factory_module = importlib.import_module(factory_module_path)
                factory = getattr(factory_module, factory_name)
            
            self.register(storage_type, storage_class, metadata, factory)
            
        except Exception as e:
            logger.error(f"Failed to register storage from module '{module_path}': {e}")
            raise
    
    def _register_from_class_path(
        self,
        storage_type: str,
        class_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        factory_path: Optional[str] = None
    ) -> None:
        """从类路径注册存储类型"""
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            storage_class = getattr(module, class_name)
            
            # 获取工厂函数
            factory = None
            if factory_path:
                factory_module_path, factory_name = factory_path.rsplit(".", 1)
                factory_module = importlib.import_module(factory_module_path)
                factory = getattr(factory_module, factory_name)
            
            self.register(storage_type, storage_class, metadata, factory)
            
        except Exception as e:
            logger.error(f"Failed to register storage from class path '{class_path}': {e}")
            raise
    
    def _validate_storage_class(self, storage_class: Type) -> None:
        """验证存储类"""
        if not inspect.isclass(storage_class):
            raise ValueError("Storage class must be a class")
        
        # 检查是否实现了必要的接口
        if not self._is_storage_class(storage_class):
            raise ValueError("Storage class must implement required interface")
    
    def _is_storage_class(self, cls: Type) -> bool:
        """检查是否是存储类"""
        # 检查是否继承自基础存储类
        from ..adapters.base import StorageBackend
        return issubclass(cls, StorageBackend)
    
    def _load_builtin_types(self) -> None:
        """加载内置存储类型"""
        if self._auto_loaded:
            return
        
        try:
            # 注册内存存储
            self._register_from_module(
                'memory', 
                'src.adapters.storage.backends.memory_backend',
                {'description': 'In-memory storage backend'}
            )
            
            # 注册SQLite存储
            self._register_from_module(
                'sqlite', 
                'src.adapters.storage.backends.sqlite_backend',
                {'description': 'SQLite storage backend'}
            )
            
            # 注册文件存储
            self._register_from_module(
                'file', 
                'src.adapters.storage.backends.file_backend',
                {'description': 'File-based storage backend'}
            )
            
            self._auto_loaded = True
            logger.info("Loaded builtin storage types")
            
        except Exception as e:
            logger.warning(f"Failed to load builtin storage types: {e}")


# 全局注册表实例
storage_registry = StorageRegistry()
```

#### 1.2.2 增强的工厂实现

更新工厂类以使用注册表：

```python
# src/adapters/storage/enhanced_factory.py

from typing import Dict, Any, Optional, Union
import logging
from .registry import storage_registry
from .adapters.async_adapter import AsyncStateStorageAdapter
from .adapters.sync_adapter import SyncStateStorageAdapter
from .core.metrics import StorageMetrics
from .core.transaction import TransactionManager

logger = logging.getLogger(__name__)

class EnhancedStorageAdapterFactory:
    """增强的存储适配器工厂
    
    使用注册表管理存储类型，支持动态注册和配置文件加载。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化增强存储适配器工厂
        
        Args:
            config_path: 配置文件路径（可选）
        """
        # 从配置文件加载存储类型
        if config_path:
            storage_registry.load_from_config(config_path)
    
    def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> SyncStateStorageAdapter:
        """创建同步存储适配器"""
        try:
            # 获取存储类
            storage_class = storage_registry.get_storage_class(storage_type)
            
            # 获取工厂函数（如果有）
            factory = storage_registry.get_storage_factory(storage_type)
            
            if factory:
                # 使用工厂函数创建后端
                backend = factory(**config)
            else:
                # 直接实例化存储类
                backend = storage_class(**config)
            
            # 创建指标收集器
            metrics = StorageMetrics()
            
            # 创建事务管理器
            transaction_manager = TransactionManager(backend)
            
            # 创建适配器
            adapter = SyncStateStorageAdapter(
                backend=backend,
                metrics=metrics,
                transaction_manager=transaction_manager
            )
            
            logger.info(f"Created sync storage adapter for type: {storage_type}")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create adapter for type '{storage_type}': {e}")
            raise
    
    def get_supported_types(self) -> List[str]:
        """获取支持的存储类型"""
        return storage_registry.get_registered_types()
    
    def get_storage_info(self, storage_type: str) -> Dict[str, Any]:
        """获取存储类型信息"""
        if not storage_registry.is_registered(storage_type):
            raise ValueError(f"Storage type '{storage_type}' is not registered")
        
        storage_class = storage_registry.get_storage_class(storage_type)
        metadata = storage_registry.get_storage_metadata(storage_type)
        
        return {
            "type": storage_type,
            "class_name": storage_class.__name__,
            "module": storage_class.__module__,
            "metadata": metadata
        }


class EnhancedAsyncStorageAdapterFactory:
    """增强的异步存储适配器工厂"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化增强异步存储适配器工厂
        
        Args:
            config_path: 配置文件路径（可选）
        """
        # 从配置文件加载存储类型
        if config_path:
            storage_registry.load_from_config(config_path)
    
    async def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> AsyncStateStorageAdapter:
        """异步创建存储适配器"""
        try:
            # 获取存储类
            storage_class = storage_registry.get_storage_class(storage_type)
            
            # 获取工厂函数（如果有）
            factory = storage_registry.get_storage_factory(storage_type)
            
            if factory:
                # 使用工厂函数创建后端
                backend = factory(**config)
            else:
                # 直接实例化存储类
                backend = storage_class(**config)
            
            # 创建指标收集器
            metrics = StorageMetrics()
            
            # 创建事务管理器
            transaction_manager = TransactionManager(backend)
            
            # 创建适配器
            adapter = AsyncStateStorageAdapter(
                backend=backend,
                metrics=metrics,
                transaction_manager=transaction_manager
            )
            
            logger.info(f"Created async storage adapter for type: {storage_type}")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create async adapter for type '{storage_type}': {e}")
            raise
    
    def get_supported_types(self) -> List[str]:
        """获取支持的存储类型"""
        return storage_registry.get_registered_types()
```

#### 1.2.3 配置文件示例

创建配置文件示例：

```yaml
# config/storage_types.yaml

storage_types:
  # 自定义Redis存储
  redis:
    module: "src.adapters.storage.backends.redis_backend"
    metadata:
      description: "Redis storage backend"
      version: "1.0.0"
      author: "Storage Team"
    factory: "src.adapters.storage.factories.redis_factory"
  
  # 自定义MongoDB存储
  mongodb:
    class: "src.adapters.storage.backends.mongodb_backend.MongoDBStorageBackend"
    metadata:
      description: "MongoDB storage backend"
      version: "1.0.0"
      author: "Storage Team"
  
  # 云存储
  s3:
    module: "src.adapters.storage.backends.s3_backend"
    metadata:
      description: "AWS S3 storage backend"
      version: "1.0.0"
      author: "Storage Team"
```

### 1.3 实施计划

1. **第一阶段**: 实现轻量级注册表
   - 创建 `StorageRegistry` 类
   - 实现基本的注册和发现功能
   - 添加内置存储类型的自动加载

2. **第二阶段**: 增强工厂实现
   - 更新工厂类以使用注册表
   - 添加配置文件支持
   - 实现工厂函数支持

3. **第三阶段**: 插件化支持
   - 实现动态模块加载
   - 添加插件验证机制
   - 创建插件开发指南

## 2. 流式操作优化方案

### 2.1 当前问题分析

新架构中的流式操作实现较为简单，存在以下性能问题：

1. **内存占用高**: 需要先加载所有数据到内存，然后分批返回
2. **响应延迟**: 需要等待所有数据加载完成才能开始返回第一批数据
3. **资源消耗**: 对于大型数据集，可能造成内存压力

### 2.2 优化方案设计

#### 2.2.1 真正的流式查询实现

为SQLite后端实现真正的流式查询：

```python
# src/adapters/storage/backends/enhanced_sqlite_backend.py

import asyncio
import sqlite3
import time
from typing import Dict, Any, Optional, List, AsyncIterator
from .sqlite_backend import SQLiteStorageBackend

class EnhancedSQLiteStorageBackend(SQLiteStorageBackend):
    """增强的SQLite存储后端
    
    提供真正的流式查询支持，优化大数据集处理性能。
    """
    
    async def stream_list_impl(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """真正的流式列表实现
        
        使用数据库游标进行流式读取，避免一次性加载所有数据到内存。
        """
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            # 构建查询
            where_clause, params = self._build_where_clause(filters)
            
            # 使用游标进行流式查询
            query = f"""
                SELECT id, data, created_at, updated_at, expires_at, compressed, 
                       type, agent_id, thread_id, session_id, metadata
                FROM state_storage {where_clause}
                ORDER BY created_at DESC
            """
            
            cursor = conn.cursor()
            
            # 执行查询
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 流式处理结果
            batch = []
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                # 处理当前批次
                current_batch = []
                for row in rows:
                    # 转换为字典
                    data_dict = dict(row)
                    
                    # 检查是否过期
                    expires_at = data_dict.get("expires_at")
                    if expires_at and isinstance(expires_at, (int, float)) and expires_at < time.time():
                        continue
                    
                    # 反序列化数据
                    try:
                        data_str = data_dict.get("data")
                        if not isinstance(data_str, str):
                            continue
                        
                        data = StorageCommonUtils.deserialize_data(data_str)
                        current_batch.append(data)
                        
                    except Exception as e:
                        logger.error(f"Failed to deserialize data: {e}")
                        continue
                
                # 如果当前批次有数据，返回
                if current_batch:
                    yield current_batch
                
                # 更新统计信息
                self._update_stats("list")
            
        except Exception as e:
            logger.error(f"Error in stream_list_impl: {e}")
            raise
        finally:
            if conn:
                self._return_connection(conn)
    
    async def stream_query_impl(
        self, 
        query: str, 
        params: Dict[str, Any],
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式查询实现
        
        支持自定义SQL查询的流式处理。
        """
        conn = None
        try:
            # 获取连接
            conn = self._get_connection()
            
            cursor = conn.cursor()
            
            # 执行查询
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 流式处理结果
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                # 处理当前批次
                current_batch = []
                for row in rows:
                    data_dict = dict(row)
                    current_batch.append(data_dict)
                
                if current_batch:
                    yield current_batch
            
        except Exception as e:
            logger.error(f"Error in stream_query_impl: {e}")
            raise
        finally:
            if conn:
                self._return_connection(conn)
```

#### 2.2.2 基础适配器流式操作增强

更新基础适配器的流式操作实现：

```python
# src/adapters/storage/adapters/enhanced_base.py

from typing import Dict, Any, AsyncIterator
from .base import StorageBackend

class EnhancedStorageBackend(StorageBackend):
    """增强的存储后端基类
    
    提供更好的流式操作支持。
    """
    
    async def stream_list(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列出数据
        
        优先使用后端的流式实现，如果不可用则回退到基础实现。
        """
        try:
            # 清理过期项
            if self.enable_ttl:
                await self._cleanup_expired_items()
            
            # 使用后端的流式实现
            async for batch in self.stream_list_impl(filters, batch_size):
                # 过滤过期数据
                if self.enable_ttl:
                    filtered_batch = []
                    for data in batch:
                        if not StorageCommonUtils.is_data_expired(data):
                            filtered_batch.append(data)
                        else:
                            self._stats["expired_items_cleaned"] += 1
                    
                    if filtered_batch:
                        yield filtered_batch
                else:
                    yield batch
            
        except Exception as e:
            logger.error(f"Error in stream_list: {e}")
            raise
    
    async def stream_query(
        self, 
        query: str, 
        params: Dict[str, Any],
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式查询
        
        提供自定义查询的流式处理支持。
        """
        try:
            # 清理过期项
            if self.enable_ttl:
                await self._cleanup_expired_items()
            
            # 使用后端的流式查询实现
            if hasattr(self, 'stream_query_impl'):
                async for batch in self.stream_query_impl(query, params, batch_size):
                    # 过滤过期数据
                    if self.enable_ttl:
                        filtered_batch = []
                        for data in batch:
                            if not StorageCommonUtils.is_data_expired(data):
                                filtered_batch.append(data)
                            else:
                                self._stats["expired_items_cleaned"] += 1
                        
                        if filtered_batch:
                            yield filtered_batch
                    else:
                        yield batch
            else:
                # 回退到基础实现
                results = await self.query_impl(query, params)
                for i in range(0, len(results), batch_size):
                    yield results[i:i + batch_size]
            
        except Exception as e:
            logger.error(f"Error in stream_query: {e}")
            raise
```

#### 2.2.3 内存和文件存储的流式优化

为内存和文件存储实现流式优化：

```python
# src/adapters/storage/backends/enhanced_memory_backend.py

import asyncio
from typing import Dict, Any, AsyncIterator
from .memory_backend import MemoryStorageBackend

class EnhancedMemoryStorageBackend(MemoryStorageBackend):
    """增强的内存存储后端
    
    提供更好的流式操作支持。
    """
    
    async def stream_list_impl(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """内存存储的流式列表实现"""
        try:
            async with self._lock:
                with self._thread_lock:
                    # 收集所有匹配的数据ID
                    matching_ids = []
                    
                    for item_id, item in self._storage.items():
                        # 检查是否过期
                        if item.is_expired():
                            del self._storage[item_id]
                            self._stats["expired_items_cleaned"] += 1
                            continue
                        
                        # 获取数据
                        data = item.access()
                        
                        # 解压缩数据（如果需要）
                        if item.compressed and isinstance(data, bytes):
                            from src.core.state.base import BaseStateSerializer
                            serializer = BaseStateSerializer(compression=True)
                            data = serializer.deserialize_state(data)
                        
                        # 检查过滤器
                        if isinstance(data, dict) and StorageCommonUtils.matches_filters(data, filters):
                            matching_ids.append(item_id)
                    
                    # 分批返回数据
                    for i in range(0, len(matching_ids), batch_size):
                        batch_ids = matching_ids[i:i + batch_size]
                        batch_data = []
                        
                        for item_id in batch_ids:
                            if item_id in self._storage:
                                item = self._storage[item_id]
                                data = item.access()
                                
                                # 解压缩数据（如果需要）
                                if item.compressed and isinstance(data, bytes):
                                    from src.core.state.base import BaseStateSerializer
                                    serializer = BaseStateSerializer(compression=True)
                                    data = serializer.deserialize_state(data)
                                
                                if isinstance(data, dict):
                                    batch_data.append(data)
                        
                        if batch_data:
                            yield batch_data
            
        except Exception as e:
            logger.error(f"Error in stream_list_impl: {e}")
            raise


# src/adapters/storage/backends/enhanced_file_backend.py

import os
import asyncio
from typing import Dict, Any, AsyncIterator
from .file_backend import FileStorageBackend

class EnhancedFileStorageBackend(FileStorageBackend):
    """增强的文件存储后端
    
    提供更好的流式操作支持。
    """
    
    async def stream_list_impl(
        self, 
        filters: Dict[str, Any], 
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """文件存储的流式列表实现"""
        try:
            # 获取所有文件
            all_files = self._list_files_in_directory(
                self.base_path,
                f"*.{self.file_extension}",
                recursive=True
            )
            
            # 按修改时间排序（最新的在前）
            all_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
            
            # 分批处理文件
            batch = []
            for file_path in all_files:
                # 加载数据
                data = self._load_data_from_file(file_path)
                if data is None:
                    continue
                
                # 检查是否过期
                if self.enable_ttl and "expires_at" in data and data["expires_at"] < time.time():
                    os.remove(file_path)
                    self._stats["expired_files_cleaned"] += 1
                    continue
                
                # 检查过滤器
                if StorageCommonUtils.matches_filters(data, filters):
                    batch.append(data)
                    
                    # 如果批次满了，返回
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
            
            # 返回最后一批
            if batch:
                yield batch
            
        except Exception as e:
            logger.error(f"Error in stream_list_impl: {e}")
            raise
```

### 2.3 性能优化策略

#### 2.3.1 内存管理优化

1. **批次大小自适应**: 根据数据大小动态调整批次大小
2. **内存监控**: 监控内存使用情况，防止内存溢出
3. **垃圾回收**: 主动触发垃圾回收，释放内存

```python
# src/adapters/storage/utils/memory_optimizer.py

import gc
import psutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """内存优化器
    
    提供内存监控和优化功能。
    """
    
    def __init__(self, max_memory_mb: int = 1024):
        """初始化内存优化器
        
        Args:
            max_memory_mb: 最大内存使用量（MB）
        """
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()
    
    def get_memory_usage_mb(self) -> float:
        """获取当前内存使用量（MB）"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def should_trigger_gc(self) -> bool:
        """检查是否应该触发垃圾回收"""
        return self.get_memory_usage_mb() > self.max_memory_mb * 0.8
    
    def optimize_memory(self) -> None:
        """优化内存使用"""
        if self.should_trigger_gc():
            logger.info("Triggering garbage collection due to high memory usage")
            gc.collect()
    
    def calculate_optimal_batch_size(self, base_batch_size: int, avg_item_size: int) -> int:
        """计算最优批次大小
        
        Args:
            base_batch_size: 基础批次大小
            avg_item_size: 平均项目大小（字节）
            
        Returns:
            优化后的批次大小
        """
        available_memory_mb = self.max_memory_mb - self.get_memory_usage_mb()
        available_memory_bytes = available_memory_mb * 1024 * 1024
        
        # 保留50%内存作为缓冲
        safe_memory_bytes = available_memory_bytes * 0.5
        
        # 计算可以处理的项目数量
        optimal_batch_size = int(safe_memory_bytes / avg_item_size)
        
        # 确保在合理范围内
        optimal_batch_size = max(10, min(optimal_batch_size, base_batch_size * 2))
        
        return optimal_batch_size
```

#### 2.3.2 查询优化

1. **索引优化**: 为常用查询字段添加索引
2. **查询缓存**: 缓存常用查询结果
3. **预编译语句**: 使用预编译SQL语句提高性能

```python
# src/adapters/storage/utils/query_optimizer.py

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """查询优化器
    
    提供查询优化和缓存功能。
    """
    
    def __init__(self):
        """初始化查询优化器"""
        self._query_cache: Dict[str, Any] = {}
        self._prepared_statements: Dict[str, Any] = {}
    
    def optimize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """优化过滤器
        
        Args:
            filters: 原始过滤器
            
        Returns:
            优化后的过滤器
        """
        optimized = filters.copy()
        
        # 移除空的过滤器
        optimized = {k: v for k, v in optimized.items() if v is not None and v != ""}
        
        # 优化范围查询
        for key, value in optimized.items():
            if isinstance(value, dict):
                # 确保范围查询的顺序
                if "$gte" in value and "$lte" in value:
                    if value["$gte"] > value["$lte"]:
                        # 交换范围
                        value["$gte"], value["$lte"] = value["$lte"], value["$gte"]
        
        return optimized
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """获取缓存结果"""
        return self._query_cache.get(cache_key)
    
    def cache_result(self, cache_key: str, result: Any, ttl: int = 300) -> None:
        """缓存结果
        
        Args:
            cache_key: 缓存键
            result: 结果
            ttl: 生存时间（秒）
        """
        import time
        self._query_cache[cache_key] = {
            "result": result,
            "expires_at": time.time() + ttl
        }
    
    def cleanup_expired_cache(self) -> None:
        """清理过期缓存"""
        import time
        current_time = time.time()
        expired_keys = [
            key for key, value in self._query_cache.items()
            if value.get("expires_at", 0) < current_time
        ]
        
        for key in expired_keys:
            del self._query_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
```

### 2.4 实施计划

1. **第一阶段**: SQLite流式查询优化
   - 实现真正的流式查询
   - 添加游标支持
   - 优化内存使用

2. **第二阶段**: 基础适配器增强
   - 更新基础适配器的流式操作
   - 添加内存优化器
   - 实现查询优化

3. **第三阶段**: 其他存储后端优化
   - 优化内存存储的流式操作
   - 优化文件存储的流式操作
   - 添加性能监控

## 3. 总结

本优化方案针对新架构存储系统中的注册表功能和流式操作提供了全面的改进建议：

1. **注册表功能**: 通过轻量级注册表实现动态类型管理，支持插件化架构
2. **流式操作**: 通过真正的流式查询和内存优化，提升大数据集处理性能

这些优化将显著提升系统的可扩展性和性能，同时保持架构的简洁性和可维护性。建议按照分阶段实施计划逐步推进，确保每个阶段的稳定性和可靠性。