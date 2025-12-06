

基于我对代码的分析，我发现 `src\infrastructure\graph\checkpoint` 目录存在明显的架构越权问题。让我详细分析：

## 架构越权问题分析

### 1. 违反分层架构原则

根据项目的分层架构规则，**基础设施层只能依赖于接口层**，不能包含业务逻辑。但checkpoint模块包含了大量业务逻辑：

#### 越权功能一：业务逻辑管理
- [`CheckpointManager`](src/infrastructure/graph/checkpoint/manager.py:15) 包含了复杂的业务逻辑：
  - 检查点缓存管理（第35-36行）
  - Hook系统集成（第34行）
  - 资源管理集成（第33行）
  - 检查点生命周期管理（第54-124行）

#### 越权功能二：业务规则实现
- [`CheckpointManager.save_checkpoint()`](src/infrastructure/graph/checkpoint/manager.py:54) 包含业务规则：
  - 执行Hook前后的业务逻辑（第71-77行，104-110行）
  - 资源限制检查（第81-82行）
  - 版本生成逻辑（第85-88行）
  - 错误处理和恢复逻辑（第114-124行）

#### 越权功能三：高级业务功能
- [`CheckpointManager.cleanup_old_checkpoints()`](src/infrastructure/graph/checkpoint/manager.py:213) 实现了业务策略：
  - 基于时间的清理策略
  - 资源管理策略

### 2. 与存储模块的集成问题

当前checkpoint模块直接实现了存储逻辑，而不是使用统一的存储接口：

#### 问题一：重复实现存储功能
- [`MemoryCheckpointSaver`](src/infrastructure/graph/checkpoint/memory.py:20) 和 [`SqliteCheckpointSaver`](src/infrastructure/graph/checkpoint/sqlite.py:22) 直接实现了存储逻辑
- 这些实现与 [`BaseStorage`](src/infrastructure/storage/base_storage.py:14) 功能重复
- 没有利用统一的存储接口 [`IStorage`](src/interfaces/storage/base.py:12)

#### 问题二：缺乏存储抽象
- checkpoint模块没有使用存储工厂模式
- 直接依赖具体的存储实现（SQLite、内存）
- 无法利用存储模块的高级功能（缓存、元数据管理、事务等）

---



现在让我详细识别checkpoint模块中不应该在基础设施层实现的功能：

## 不应该在基础设施层实现的功能

### 1. 业务逻辑层功能（应移至服务层）

#### A. 检查点管理业务逻辑
- **位置**: [`CheckpointManager`](src/infrastructure/graph/checkpoint/manager.py:15) 整个类
- **问题**: 包含复杂的业务逻辑，属于服务层职责
- **具体功能**:
  - 检查点生命周期管理
  - 缓存策略实现
  - Hook系统集成
  - 资源管理集成
  - 错误处理和恢复策略

#### B. 业务规则实现
- **位置**: [`save_checkpoint()`](src/infrastructure/graph/checkpoint/manager.py:54) 方法
- **问题**: 实现了业务规则，属于服务层职责
- **具体功能**:
  - Hook执行逻辑
  - 资源限制检查
  - 版本生成策略
  - 事务性操作

#### C. 高级业务功能
- **位置**: [`cleanup_old_checkpoints()`](src/infrastructure/graph/checkpoint/manager.py:213) 方法
- **问题**: 实现了业务策略，属于服务层职责
- **具体功能**:
  - 基于时间的清理策略
  - 资源管理策略

### 2. 核心层功能（应移至核心层）

#### A. 检查点数据模型
- **位置**: [`Checkpoint`](src/infrastructure/graph/checkpoint/base.py:45) 类
- **问题**: 核心数据模型应该在核心层定义
- **具体功能**:
  - 检查点数据结构
  - 属性访问器
  - 数据验证逻辑

#### B. 检查点元数据模型
- **位置**: [`CheckpointMetadata`](src/infrastructure/graph/checkpoint/base.py:17) 类
- **问题**: 核心数据模型应该在核心层定义
- **具体功能**:
  - 元数据结构
  - 属性访问器

#### C. 检查点元组模型
- **位置**: [`CheckpointTuple`](src/infrastructure/graph/checkpoint/base.py:83) 类
- **问题**: 核心数据模型应该在核心层定义
- **具体功能**:
  - 检查点组合数据结构
  - 关联数据管理

### 3. 接口层功能（应移至接口层）

#### A. 检查点保存器接口
- **位置**: [`BaseCheckpointSaver`](src/infrastructure/graph/checkpoint/base.py:110) 类
- **问题**: 接口定义应该在接口层
- **具体功能**:
  - 检查点操作抽象
  - 同步/异步操作定义

### 4. 基础设施层保留功能

#### A. 存储适配器实现
- **位置**: [`MemoryCheckpointSaver`](src/infrastructure/graph/checkpoint/memory.py:20) 和 [`SqliteCheckpointSaver`](src/infrastructure/graph/checkpoint/sqlite.py:22)
- **问题**: 应该重构为使用统一存储接口的适配器
- **应该保留**:
  - 存储适配逻辑
  - 数据序列化/反序列化
  - 存储特定优化

#### B. 基础设施工具
- **位置**: 各种工具方法
- **应该保留**:
  - 数据转换工具
  - 存储特定配置
  - 性能优化实现
