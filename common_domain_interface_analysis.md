# common_domain.py 接口分析报告

## 概述

`src/interfaces/common_domain.py` 文件包含了通用领域层接口定义，主要提供了以下几类接口：

1. **领域层枚举定义**：`AbstractSessionStatus`
2. **领域层抽象实体**：`AbstractSessionData`, `AbstractThreadData`, `AbstractThreadBranchData`, `AbstractThreadSnapshotData`
3. **领域层基础接口**：`ISerializable`, `ICacheable`, `ITimestamped`

## 分析结果

### 1. 接口与现有模块的对应关系

#### 1.1 会话相关接口
- `AbstractSessionStatus` 和 `AbstractSessionData` 应该合并到 `src/interfaces/sessions/` 目录
- 现有 `sessions/` 目录已包含 `base.py` 和 `service.py`，但缺少基础实体接口

#### 1.2 线程相关接口
- `AbstractThreadData`, `AbstractThreadBranchData`, `AbstractThreadSnapshotData` 应该合并到 `src/interfaces/threads/` 目录
- 现有 `threads/` 目录已包含服务层接口，但缺少基础实体接口

#### 1.3 通用基础接口
- `ISerializable`, `ICacheable`, `ITimestamped` 是跨模块的通用接口
- 可以保留在 `common_domain.py` 中，或者创建专门的 `src/interfaces/common/` 目录

### 2. 接口重复性分析

#### 2.1 与现有接口的重复
- `AbstractSessionData` 与 `src/interfaces/sessions/base.py` 中的 `ISessionManager` 功能不重复
- `AbstractThreadData` 与 `src/interfaces/threads/service.py` 中的 `IThreadService` 功能不重复
- `AbstractThreadBranchData` 与 `src/interfaces/threads/branch_service.py` 中的 `IThreadBranchService` 功能不重复
- `AbstractThreadSnapshotData` 与 `src/interfaces/repository/snapshot.py` 中的 `ISnapshotRepository` 功能不重复

#### 2.2 接口层次关系
- `common_domain.py` 中的接口更偏向于**数据实体**的定义
- 现有模块中的接口更偏向于**服务层**的定义
- 两者是互补关系，不是重复关系

### 3. 架构一致性分析

#### 3.1 符合分层架构原则
- `common_domain.py` 中的接口定义了领域层的核心实体和值对象
- 符合 DDD（领域驱动设计）中的实体和值对象定义
- 与现有的服务层接口形成了良好的分层结构

#### 3.2 接口职责清晰
- **实体接口**：定义了领域对象的基本属性和行为
- **服务接口**：定义了业务操作和流程
- **仓储接口**：定义了数据访问和持久化

## 建议方案

### 方案一：保持现状（推荐）

**理由：**
1. `common_domain.py` 中的接口是真正的"通用领域接口"，被多个模块共享
2. 集中管理通用领域接口，便于维护和复用
3. 避免在多个子目录中重复定义相似的接口
4. 符合"通用接口集中管理"的设计原则

**优点：**
- 接口定义集中，易于查找和维护
- 避免循环依赖问题
- 保持接口层的清晰结构
- 符合当前项目的架构设计

### 方案二：拆分到各模块（不推荐）

**理由：**
1. 会破坏接口的通用性和复用性
2. 可能导致接口定义的重复
3. 增加维护复杂度
4. 可能引入循环依赖问题

**缺点：**
- 接口分散，难以管理
- 可能导致接口不一致
- 增加模块间的耦合度

## 具体实施建议

### 1. 保持 `common_domain.py` 文件
- 继续作为通用领域接口的定义文件
- 确保所有模块都从这里导入通用接口

### 2. 更新导入路径
- 确保各模块正确导入 `common_domain.py` 中的接口
- 在 `src/interfaces/__init__.py` 中继续导出这些接口

### 3. 文档完善
- 为 `common_domain.py` 添加更详细的文档说明
- 明确各接口的使用场景和职责

### 4. 接口使用规范
- 制定明确的接口使用规范
- 确保新开发的模块正确使用这些通用接口

## 结论

`src/interfaces/common_domain.py` 文件中的接口**不应该**合并到接口层已有的子目录中，而应该**保持现状**。这些接口是真正的通用领域接口，被多个模块共享，集中管理更有利于项目的维护和扩展。

当前的接口层结构是合理的：
- 通用领域接口集中在 `common_domain.py`
- 各模块的服务接口在各自的子目录中
- 通过 `__init__.py` 统一导出所有接口

这种结构既保持了接口的集中管理，又实现了模块化的清晰分离，符合项目的整体架构设计原则。