# Threads层迁移计划

## 概述

本文档描述了将threads层从旧的四层架构（Domain-Infrastructure）迁移到新的扁平化架构（Core + Services + Adapters）的详细计划。

## 迁移目标

1. **保持功能完整性**：确保所有现有功能在迁移后正常工作
2. **提升代码质量**：利用新架构的优势改进代码组织
3. **增强可维护性**：通过更清晰的职责分离提高可维护性
4. **保持向后兼容**：尽量保持API的向后兼容性

## 架构对比

### 旧架构（4层DDD）
```
Domain Layer (领域层)
├── Thread实体模型
├── 领域服务接口
└── 仓储接口

Infrastructure Layer (基础设施层)
├── 存储实现
└── 外部服务适配器
```

### 新架构（扁平化）
```
Core Layer (核心层)
├── Thread实体模型（Pydantic）
├── 核心接口
└── 基础抽象类

Services Layer (服务层)
├── 线程业务服务
├── 分支管理服务
├── 快照管理服务
└── 协调器服务

Interfaces Layer (接口层)
├── 仓储接口
├── 服务接口
└── 存储适配器接口

Adapters Layer (适配器层)
├── SQLite存储适配器
├── 内存存储适配器
└── 文件存储适配器
```

## 迁移步骤

### 阶段1：核心实体迁移

**目标**：将实体模型从dataclass迁移到Pydantic模型

**任务**：
1. 分析现有的Thread、ThreadBranch、ThreadSnapshot实体
2. 使用Pydantic重新定义实体模型
3. 添加验证规则和业务逻辑方法
4. 确保向后兼容性

**文件映射**：
- `src/domain/threads/models.py` → `src/core/threads/entities.py`

**关键改进**：
- 使用Pydantic的Field进行字段验证
- 添加模型配置（Config类）
- 实现自动类型转换
- 添加业务方法（如状态转换验证）

### 阶段2：核心接口迁移

**目标**：定义核心业务接口

**任务**：
1. 提取核心业务接口
2. 定义IThreadCore、IThreadBranchCore、IThreadSnapshotCore
3. 创建基础抽象类
4. 确保接口的一致性

**文件映射**：
- `src/domain/threads/interfaces.py`（部分）→ `src/core/threads/interfaces.py`
- 新增：`src/core/threads/base.py`

### 阶段3：服务层实现

**目标**：实现业务逻辑服务

**任务**：
1. 创建ThreadService实现主线程业务逻辑
2. 创建ThreadBranchService处理分支管理
3. 创建ThreadSnapshotService处理快照管理
4. 创建ThreadCoordinatorService处理协调逻辑
5. 实现依赖注入

**文件映射**：
- `src/domain/threads/domain_service.py` → `src/services/threads/service.py`
- `src/domain/threads/collaboration.py` → `src/services/threads/coordinator_service.py`
- 新增：`src/services/threads/branch_service.py`
- 新增：`src/services/threads/snapshot_service.py`

### 阶段4：接口层标准化

**目标**：统一和标准化所有接口

**任务**：
1. 将所有接口迁移到interfaces层
2. 标准化接口命名和参数
3. 添加类型注解
4. 创建服务接口

**文件映射**：
- `src/domain/threads/interfaces.py` → `src/interfaces/threads/interfaces.py`
- 新增：`src/interfaces/threads/service.py`
- 新增：`src/interfaces/threads/branch_service.py`
- 新增：`src/interfaces/threads/snapshot_service.py`
- 新增：`src/interfaces/threads/coordinator_service.py`

### 阶段5：存储适配器迁移

**目标**：将存储实现迁移到适配器层

**任务**：
1. 创建统一的存储接口IThreadStore
2. 实现SQLite存储适配器
3. 实现内存存储适配器（用于测试）
4. 添加存储工厂模式

**文件映射**：
- `src/infrastructure/threads/metadata_store.py` → `src/adapters/storage/sqlite_thread_store.py`
- `src/infrastructure/threads/branch_store.py` → 集成到统一存储
- `src/infrastructure/threads/snapshot_store.py` → 集成到统一存储

### 阶段6：依赖注入配置

**目标**：配置服务的依赖注入

**任务**：
1. 在服务容器中注册threads相关服务
2. 配置存储适配器
3. 设置生命周期管理
4. 添加配置绑定

**文件影响**：
- `src/services/container/di_config.py`
- `configs/threads.yaml`

## 迁移检查清单

### 功能验证
- [ ] 线程创建和删除
- [ ] 线程状态管理
- [ ] 分支创建和合并
- [ ] 快照创建和恢复
- [ ] 元数据管理
- [ ] 协调器功能

### 性能验证
- [ ] 存储性能测试
- [ ] 内存使用测试
- [ ] 并发操作测试

### 兼容性验证
- [ ] API向后兼容性
- [ ] 数据格式兼容性
- [ ] 配置兼容性

## 风险评估

### 高风险项
1. **数据模型变更**：从dataclass到Pydantic可能影响序列化
2. **存储接口变更**：统一存储接口可能影响现有代码

### 缓解措施
1. **渐进式迁移**：分阶段进行，每个阶段都可独立验证
2. **适配器模式**：创建适配器保持旧接口的兼容性
3. **全面测试**：每个阶段都进行充分的单元测试和集成测试

## 时间估算

- 阶段1（核心实体）：2-3天
- 阶段2（核心接口）：1-2天
- 阶段3（服务层）：3-4天
- 阶段4（接口层）：2-3天
- 阶段5（存储适配器）：3-4天
- 阶段6（依赖注入）：1-2天

**总计：12-18天**

## 后续优化

迁移完成后的优化方向：
1. **性能优化**：缓存机制、批量操作
2. **监控增强**：添加性能指标和健康检查
3. **文档完善**：API文档和使用示例
4. **测试覆盖**：提高单元测试和集成测试覆盖率

## 总结

本迁移计划旨在将threads层从传统的DDD架构迁移到更灵活、更易维护的扁平化架构。通过分阶段的迁移方式，我们可以确保功能的完整性和系统的稳定性，同时充分利用新架构的优势。