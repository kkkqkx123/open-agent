# 配置系统重构计划

## 目标

重构 `src\infrastructure\config` 和 `src\core\config` 目录，消除重复代码，明确分层职责，提高系统的可维护性和可扩展性。

## 当前问题

1. **严重的代码重复**: ConfigLoader 在两个目录中几乎完全相同
2. **职责边界不清**: Infrastructure 层和 Core 层功能重叠
3. **违反分层原则**: Infrastructure 层依赖 Core 层
4. **过度设计**: Core 层配置系统过于复杂

## 重构策略

### 阶段一：基础设施层简化 (1-2天)

**目标**: 简化 Infrastructure 层，只保留最基础的功能

**任务**:
1. 简化 `infrastructure/config/config_loader.py`，只保留文件读取和格式解析
2. 保留 `infrastructure/config/schema_loader.py` 用于模式加载
3. 删除 `infrastructure/config/inheritance_handler.py`（功能移至 Core 层）
4. 删除 `infrastructure/config/config_operations.py`（功能移至 Services 层）

**验收标准**:
- Infrastructure 层只依赖 Interfaces 层
- 所有测试通过
- 基础配置加载功能正常

### 阶段二：核心层重构 (2-3天)

**目标**: 重新组织 Core 层，统一配置处理逻辑

**任务**:
1. 删除 `core/config/config_loader.py`（使用 Infrastructure 层的实现）
2. 统一继承处理逻辑到 `core/config/processor/`
3. 整合验证功能到 `core/config/validation.py`
4. 简化 `core/config/models/` 中的配置模型
5. 重构 `core/config/config_manager.py`，移除高级功能

**验收标准**:
- Core 层只依赖 Infrastructure 层和 Interfaces 层
- 配置处理逻辑统一
- 所有测试通过

### 阶段三：服务层创建 (2-3天)

**目标**: 创建 Services 层，提供高级配置管理功能

**任务**:
1. 创建 `services/config/` 目录
2. 实现 `config_service.py`（高级配置管理）
3. 实现 `callback_service.py`（配置变更回调）
4. 实现 `cache_service.py`（配置缓存）
5. 迁移错误恢复功能到服务层

**验收标准**:
- Services 层只依赖 Core 层和 Interfaces 层
- 高级功能正常工作
- 所有测试通过

### 阶段四：接口统一 (1天)

**目标**: 统一配置系统接口设计

**任务**:
1. 在 `interfaces/config/` 中定义统一接口
2. 更新所有实现以符合统一接口
3. 实现依赖注入配置

**验收标准**:
- 所有层实现相同的接口
- 依赖注入正常工作
- 所有测试通过

## 重构后的目录结构

```
src/
├── interfaces/
│   └── config/
│       ├── interfaces.py (统一接口定义)
│       └── exceptions.py (统一异常定义)
├── infrastructure/
│   └── config/
│       ├── __init__.py
│       ├── config_loader.py (简化版)
│       └── schema_loader.py
├── core/
│   └── config/
│       ├── __init__.py
│       ├── config_manager.py
│       ├── base.py
│       ├── processor/
│       │   ├── __init__.py
│       │   ├── config_processor_chain.py
│       │   ├── inheritance_processor.py
│       │   ├── environment_processor.py
│       │   └── reference_processor.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── base.py (简化版)
│       └── validation.py
└── services/
    └── config/
        ├── __init__.py
        ├── config_service.py
        ├── callback_service.py
        └── cache_service.py
```

## 风险评估

### 高风险
- 破坏现有功能
- 影响其他模块的配置加载

### 缓解措施
- 渐进式重构，每阶段都确保功能正常
- 保持向后兼容性
- 充分的测试覆盖

## 时间估算

- 总计：6-9天
- 阶段一：1-2天
- 阶段二：2-3天
- 阶段三：2-3天
- 阶段四：1天

## 成功标准

1. 消除所有重复代码
2. 明确分层职责
3. 所有测试通过
4. 性能不低于重构前
5. 代码可读性和可维护性显著提升