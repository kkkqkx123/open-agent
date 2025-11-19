# 存储架构迁移指南

本文档提供了从旧存储架构迁移到新架构的详细指南。

## 概述

存储架构迁移将 `src/infrastructure/storage` 目录的存储系统从传统的4层架构迁移到新的扁平化架构（Core + Services + Adapters）。

## 新架构概览

### 目录结构

```
src/
├── core/state/                    # 核心接口和实体
│   ├── interfaces.py             # 统一接口导出
│   ├── storage_interfaces.py     # 存储后端接口
│   ├── state_interfaces.py       # 状态管理接口
│   ├── adapter_interfaces.py     # 适配器接口
│   ├── entities.py               # 状态实体定义
│   ├── exceptions.py             # 存储相关异常
│   └── base.py                   # 基础存储抽象
├── adapters/storage/              # 存储适配器实现
│   ├── __init__.py               # 模块导出
│   ├── base.py                   # 适配器基类
│   ├── factory.py                # 适配器工厂
│   ├── memory.py                 # 内存存储适配器
│   ├── memory_backend.py         # 内存存储后端
│   ├── memory_utils.py           # 内存存储工具
│   ├── sqlite.py                 # SQLite存储适配器
│   ├── sqlite_backend.py         # SQLite存储后端
│   ├── sqlite_utils.py           # SQLite存储工具
│   ├── file.py                   # 文件存储适配器
│   ├── file_backend.py           # 文件存储后端
│   └── file_utils.py             # 文件存储工具
├── services/storage/             # 存储服务
│   ├── __init__.py               # 服务导出
│   ├── manager.py                # 存储管理服务
│   ├── config.py                 # 配置管理服务
│   └── migration.py              # 数据迁移服务
└── services/container/           # 依赖注入容器
    └── storage_registry.py       # 存储服务注册
```

### 架构优势

1. **扁平化架构**：从4层减少到3层，降低复杂性
2. **职责清晰**：Core定义接口，Adapters实现存储，Services提供业务逻辑
3. **配置统一**：Services层提供统一的配置管理
4. **易于测试**：清晰的依赖关系便于单元测试
5. **扩展性强**：通过工厂模式支持动态扩展

## 迁移步骤

### 步骤1：更新依赖导入

将旧的导入语句更新为新的导入：

```python
# 旧导入
from src.infrastructure.storage import StorageManager

# 新导入
from src.services.storage import StorageManager
```

### 步骤2：使用新的存储适配器

```python
from src.adapters.storage import create_storage_adapter

# 创建内存存储适配器
memory_adapter = create_storage_adapter("memory", {
    "max_size": 1000,
    "enable_ttl": False
})

# 创建SQLite存储适配器
sqlite_adapter = create_storage_adapter("sqlite", {
    "db_path": "storage.db",
    "enable_backup": True
})

# 创建文件存储适配器
file_adapter = create_storage_adapter("file", {
    "base_path": "file_storage",
    "enable_compression": True
})
```

### 步骤3：使用存储管理器

```python
from src.services.storage import StorageManager

# 创建存储管理器
manager = StorageManager()

# 注册存储适配器
await manager.register_adapter(
    "memory",
    "memory",
    {"max_size": 1000},
    set_as_default=True
)

# 获取适配器
adapter = await manager.get_adapter("memory")
```

### 步骤4：直接使用新适配器

现在可以直接使用新适配器，无需向后兼容层：

```python
from src.adapters.storage import MemoryStateStorageAdapter
from src.core.state.entities import StateHistoryEntry
import time

# 创建新适配器
adapter = MemoryStateStorageAdapter()

# 使用新接口
entry = StateHistoryEntry(
    history_id="test_id",
    agent_id="test_agent",
    session_id="test_session",
    thread_id="test_thread",
    timestamp=time.time(),
    data={"message": "Hello"}
)

# 保存数据
success = adapter.save_history_entry(entry)

# 加载数据
loaded_entry = adapter.get_history_entry("test_id")
```

## 配置管理

### 使用配置文件

```python
from src.services.storage import StorageConfigManager

# 创建配置管理器
config_manager = StorageConfigManager()

# 从模板创建配置
config_manager.create_config_from_template(
    "sqlite_default",
    "my_sqlite",
    {"db_path": "my_storage.db"}
)

# 获取配置
config = config_manager.get_config("my_sqlite")
```

### 环境变量支持

配置支持环境变量注入：

```yaml
# configs/storage.yaml
adapters:
  sqlite:
    config:
      db_path: "${STORAGE_DB_PATH:default.db}"
      backup_path: "${STORAGE_BACKUP_PATH:backups}"
```

## 数据迁移

### 使用迁移服务

```python
from src.services.storage import StorageMigrationService
from src.adapters.storage import MemoryStateStorageAdapter, SQLiteStateStorageAdapter

# 创建源和目标适配器
source_adapter = MemoryStateStorageAdapter()
target_adapter = SQLiteStateStorageAdapter(db_path="new_storage.db")

# 创建迁移服务
migration_service = StorageMigrationService()

# 创建迁移任务
task_id = await migration_service.create_migration_task(
    "memory_to_sqlite",
    source_adapter,
    target_adapter,
    {"batch_size": 100, "validate_data": True}
)

# 开始迁移
await migration_service.start_migration(task_id)

# 监控迁移进度
status = await migration_service.get_migration_status(task_id)
print(f"Migration progress: {status['progress']}%")
```

## 依赖注入集成

### 注册存储服务

```python
from src.services.container.storage_registry import (
    register_storage_services,
    register_storage_adapter,
    initialize_storage_services
)

# 注册存储服务
register_storage_services()

# 注册存储适配器
register_storage_adapter(
    name="my_adapter",
    adapter_type="sqlite",
    config={"db_path": "my.db"},
    set_as_default=True
)

# 初始化存储服务
initialize_storage_services()
```

### 使用依赖注入

```python
from src.services.container.storage_registry import get_storage_manager

# 获取存储管理器
manager = get_storage_manager()

# 使用存储管理器
adapter = await manager.get_adapter()
```

## 性能优化

### 内存存储优化

```python
# 配置内存存储
memory_config = {
    "max_size": 10000,              # 最大项目数
    "max_memory_mb": 100,           # 最大内存使用量
    "enable_compression": True,     # 启用压缩
    "compression_threshold": 1024,  # 压缩阈值
    "enable_ttl": True,             # 启用TTL
    "default_ttl_seconds": 3600     # 默认TTL
}
```

### SQLite存储优化

```python
# 配置SQLite存储
sqlite_config = {
    "db_path": "storage.db",
    "connection_pool_size": 10,     # 连接池大小
    "enable_wal_mode": True,        # 启用WAL模式
    "cache_size": 2000,             # 缓存大小
    "synchronous_mode": "NORMAL",   # 同步模式
    "journal_mode": "WAL",          # 日志模式
    "enable_backup": True,          # 启用备份
    "backup_interval_hours": 6      # 备份间隔
}
```

### 文件存储优化

```python
# 配置文件存储
file_config = {
    "base_path": "file_storage",
    "directory_structure": "by_date", # 目录结构
    "enable_compression": True,      # 启用压缩
    "max_files_per_directory": 1000, # 每目录最大文件数
    "enable_backup": True,           # 启用备份
    "backup_interval_hours": 12      # 备份间隔
}
```

## 故障排除

### 常见问题

1. **导入错误**
   ```
   ImportError: cannot import name 'StorageManager' from 'src.infrastructure.storage'
   ```
   **解决方案**：更新导入语句为 `from src.services.storage import StorageManager`

2. **配置错误**
   ```
   ConfigurationError: Invalid configuration for adapter type: sqlite
   ```
   **解决方案**：检查配置参数是否符合适配器要求

3. **连接错误**
   ```
   StorageConnectionError: Failed to connect SQLiteStorageBackend
   ```
   **解决方案**：检查数据库路径和权限

### 调试技巧

1. **启用日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **健康检查**
   ```python
   manager = StorageManager()
   health = await manager.health_check()
   print(health)
   ```

3. **性能监控**
   ```python
   adapter = create_storage_adapter("sqlite", config)
   stats = adapter.get_history_statistics()
   print(stats)
   ```

## 最佳实践

1. **选择合适的存储类型**
   - 内存存储：临时数据、测试环境
   - SQLite存储：生产环境、中等数据量
   - 文件存储：大量数据、需要直接文件访问

2. **配置管理**
   - 使用环境变量进行配置
   - 为不同环境创建不同的配置模板
   - 定期备份重要数据

3. **性能优化**
   - 根据数据量选择合适的存储类型
   - 启用压缩以节省存储空间
   - 配置适当的连接池大小

4. **监控和维护**
   - 定期执行健康检查
   - 监控存储使用情况
   - 定期清理过期数据

## 总结

新的存储架构提供了更好的可维护性、扩展性和性能。通过遵循本指南，您可以顺利地从旧架构迁移到新架构，并充分利用新架构的优势。

如果在迁移过程中遇到问题，请参考故障排除部分或联系开发团队获取支持。