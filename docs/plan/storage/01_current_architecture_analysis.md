# 当前存储模块架构分析

## 概述

本文档分析当前存储模块的架构和配置系统，为添加Redis和PostgreSQL存储选项提供基础。

## 当前架构概览

### 1. 架构层次

当前存储模块采用扁平化架构，主要分为以下层次：

```
Adapters (适配器层)
├── storage/
│   ├── backends/          # 存储后端实现
│   ├── adapters/          # 存储适配器
│   ├── core/             # 核心组件
│   ├── utils/            # 工具类
│   ├── factory.py        # 工厂模式
│   └── registry.py       # 注册表
```

### 2. 核心组件分析

#### 2.1 接口层 (`src/interfaces/storage.py`)

定义了统一的存储接口：
- `IUnifiedStorage`: 统一存储接口，包含CRUD操作、查询操作、高级操作等
- `IStorageFactory`: 存储工厂接口，负责创建存储实例

#### 2.2 核心模型 (`src/core/storage/models.py`)

定义了存储相关的数据模型：
- `StorageData`: 统一存储数据模型
- `StorageConfig`: 存储配置模型
- `StorageQuery`: 存储查询模型
- `StorageTransaction`: 存储事务模型
- `StorageStatistics`: 存储统计模型
- `StorageHealth`: 存储健康状态模型

#### 2.3 存储后端实现

当前已实现的存储后端：

1. **SQLite存储后端** (`src/adapters/storage/backends/sqlite_backend.py`)
   - 继承自 `ConnectionPooledStorageBackend`
   - 支持连接池、事务、WAL模式、备份等功能
   - 丰富的配置选项：缓存大小、同步模式、日志模式等

2. **内存存储后端** (`src/adapters/storage/backends/memory_backend.py`)
   - 继承自 `StorageBackend`
   - 支持TTL、压缩、持久化等功能
   - 内存优化和容量管理

3. **文件存储后端** (`src/adapters/storage/backends/file_backend.py`)
   - 基于文件系统的存储实现

#### 2.4 注册表系统 (`src/adapters/storage/registry.py`)

- `StorageRegistry`: 轻量级存储注册表
- 支持插件化架构
- 支持从配置文件加载存储类型
- 支持模块和类路径注册

#### 2.5 工厂模式 (`src/adapters/storage/factory.py`)

- `StorageAdapterFactory`: 同步存储适配器工厂
- `AsyncStorageAdapterFactory`: 异步存储适配器工厂
- 支持配置验证和存储信息查询

### 3. 配置系统分析

#### 3.1 配置文件结构

当前配置系统采用YAML格式，支持：

1. **存储类型配置** (`configs/storage/storage_types.yaml`)
   - 全局存储配置
   - 存储类型定义
   - 环境特定配置

2. **存储适配器配置** (`configs/storage.yaml`)
   - 适配器配置
   - 管理器配置
   - 迁移服务配置
   - 监控配置
   - 安全配置

#### 3.2 配置特性

- **环境变量注入**: `${VAR:DEFAULT}` 格式
- **配置继承**: 支持环境特定覆盖
- **类型安全**: 使用Pydantic模型验证
- **热重载**: 开发环境支持文件监听

#### 3.3 配置加载器

- `ConfigLoader`: 基于YamlLoader的配置加载器
- 支持缓存、验证、环境变量解析
- 生命周期管理

## 当前架构优势

1. **模块化设计**: 清晰的分层架构，职责分离
2. **插件化支持**: 注册表系统支持动态加载存储类型
3. **配置驱动**: 丰富的配置选项，支持多环境
4. **类型安全**: 使用Pydantic进行配置验证
5. **异步支持**: 同时支持同步和异步操作
6. **监控集成**: 内置指标收集和健康检查

## 当前架构限制

1. **存储类型有限**: 仅支持SQLite、内存和文件存储
2. **配置复杂度**: 配置文件较多，管理复杂
3. **依赖管理**: 新存储类型需要手动添加依赖
4. **测试覆盖**: 缺乏对新存储类型的测试框架
5. **文档不足**: 缺乏添加新存储类型的详细文档

## 扩展点分析

### 1. 存储后端扩展

- 新存储后端需要继承 `StorageBackend` 或 `ConnectionPooledStorageBackend`
- 实现所有必需的抽象方法
- 注册到存储注册表

### 2. 配置扩展

- 在 `storage_types.yaml` 中添加新的存储类型配置
- 在 `storage.yaml` 中添加适配器配置
- 支持环境特定配置

### 3. 依赖管理

- 需要在 `pyproject.toml` 中添加新依赖
- 考虑可选依赖，避免强制安装

## 下一步计划

基于当前架构分析，我们将：

1. 设计Redis存储后端实现方案
2. 设计PostgreSQL存储后端实现方案
3. 扩展存储配置选项架构
4. 创建配置模板和验证机制
5. 制定迁移和测试策略

## 技术债务和改进建议

1. **统一配置接口**: 简化配置文件结构
2. **自动发现**: 实现存储类型的自动发现机制
3. **配置模板**: 提供更多开箱即用的配置模板
4. **性能优化**: 优化连接池和缓存策略
5. **错误处理**: 改进错误处理和重试机制