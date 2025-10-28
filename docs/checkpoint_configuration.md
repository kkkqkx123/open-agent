# Checkpoint配置指南

## 概述

Checkpoint系统支持多种存储后端和灵活的配置选项，可以根据不同的环境需求进行配置。

## 配置选项

### 全局配置

在`configs/global.yaml`文件中可以配置以下选项：

```yaml
checkpoint:
  enabled: true                    # 是否启用checkpoint功能
  storage_type: "sqlite"          # 存储类型："sqlite" 或 "memory"
  auto_save: true                 # 是否自动保存
  save_interval: 5                # 每N步保存一次
  max_checkpoints: 100            # 最大保存的checkpoint数量
  retention_days: 30              # 保留天数
  trigger_conditions:             # 触发保存的条件
    - "tool_call"
    - "state_change"
  db_path: "storage/checkpoints.db"  # SQLite数据库路径
  compression: false              # 是否压缩存储
```

### 存储路径说明

- **生产环境**：默认使用 `storage/checkpoints.db`
- **测试环境**：默认使用 `storage/test/checkpoints.db`
- **自定义路径**：可以通过 `db_path` 配置项指定

## 使用示例

### 1. 使用默认配置创建管理器

```python
from src.infrastructure.checkpoint.factory import CheckpointFactory

# 从全局配置创建
config_dict = {
    "storage_type": "sqlite",
    "db_path": "storage/checkpoints.db"
}
manager = CheckpointFactory.create_from_config(config_dict)
```

### 2. 创建生产环境管理器

```python
from src.infrastructure.checkpoint.factory import CheckpointFactory

# 创建生产环境管理器
manager = CheckpointFactory.create_production_manager("storage/prod_checkpoints.db")
```

### 3. 创建测试环境管理器

```python
from src.infrastructure.checkpoint.factory import CheckpointFactory

# 创建测试管理器
manager = CheckpointFactory.create_test_manager()
```

## 目录结构

```
project/
├── storage/                    # 存储目录
│   ├── checkpoints.db         # 生产环境数据库
│   └── test/                  # 测试环境目录
│       └── checkpoints.db     # 测试环境数据库
├── configs/
│   └── global.yaml           # 全局配置文件
└── src/
    └── infrastructure/
        └── checkpoint/
```

## 最佳实践

1. **生产环境**：使用SQLite存储以确保数据持久化
2. **开发环境**：可以使用内存存储以提高性能
3. **测试环境**：使用独立的测试数据库避免数据污染
4. **路径配置**：始终使用相对路径，系统会自动处理目录创建