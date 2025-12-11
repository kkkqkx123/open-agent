# Core目录配置文件迁移清单

## 📋 概述

本文档详细列出了 `src/core` 目录中所有需要迁移到 `src/infrastructure/config` 的配置相关文件，以及它们的迁移优先级和依赖关系。

## 🗂️ 文件分类

### 1. 核心配置模块（高优先级）

#### 1.1 配置模型定义
- **`src/core/config/models/`** - 整个目录需要迁移
  - `__init__.py` - 配置模型导出
  - `base.py` - 基础配置模型
  - `global_config.py` - 全局配置模型
  - `llm_config.py` - LLM配置模型
  - `tool_config.py` - 工具配置模型
  - `token_counter_config.py` - Token计数器配置模型
  - `task_group_config.py` - 任务组配置模型
  - `retry_timeout_config.py` - 重试超时配置模型
  - `checkpoint_config.py` - 检查点配置模型
  - `connection_pool_config.py` - 连接池配置模型

#### 1.2 配置基础设施
- **`src/core/config/base.py`** - 基础配置类和枚举定义
- **`src/core/config/config_manager.py`** - 统一配置管理器
- **`src/core/config/config_manager_factory.py`** - 配置管理器工厂
- **`src/core/config/adapter_factory.py`** - 配置适配器工厂
- **`src/core/config/adapters.py`** - 配置适配器实现

#### 1.3 配置处理和验证
- **`src/core/config/processor/validator.py`** - 配置验证器
- **`src/core/config/validation/validation_rules.py`** - 验证规则定义
- **`src/core/config/validation/business_validators.py`** - 业务验证器

### 2. 模块特定配置（中优先级）

#### 2.1 状态管理配置
- **`src/core/state/config/settings.py`** - 状态管理配置类
  - 包含449行代码，定义了完整的状态管理配置逻辑
  - 需要拆分为配置模型和业务逻辑

#### 2.2 LLM配置处理
- **`src/core/llm/llm_config_processor.py`** - LLM配置处理器
  - 作为适配器模式，但增加了配置系统复杂性
  - 需要重新设计为纯业务逻辑

#### 2.3 存储配置
- **`src/core/storage/config.py`** - 存储配置定义
  - `StorageConfig`、`MemoryStorageConfig`、`SQLiteStorageConfig`、`FileStorageConfig`
  - 与 `src/core/config/models/` 中的配置模型重复

#### 2.4 工具配置
- **`src/core/tools/config.py`** - 工具注册表配置
- **`src/core/tools/factory.py`** - 工具工厂中的配置逻辑

### 3. 工作流配置（中优先级）

#### 3.1 工作流配置适配器
- **`src/core/workflow/templates/state_machine/config_adapter.py`** - 状态机配置适配器
- **`src/core/workflow/templates/state_machine/workflow_config.py`** - 工作流配置领域实体
- **`src/core/workflow/templates/state_machine/templates.py`** - 状态机模板配置

#### 3.2 工作流配置映射
- **`src/core/workflow/mappers/config_mapper.py`** - 工作流配置映射器
- **`src/core/workflow/validation.py`** - 工作流配置验证

#### 3.3 工作流注册表配置
- **`src/core/workflow/registry/trigger_registry.py`** - 触发器配置
- **`src/core/workflow/registry/function_registry.py`** - 函数配置
- **`src/core/workflow/registry/node_registry.py`** - 节点配置
- **`src/core/workflow/registry/edge_registry.py`** - 边配置

### 4. 执行策略配置（低优先级）

#### 4.1 执行策略配置
- **`src/core/workflow/execution/strategies/batch_strategy.py`** - 批量执行配置
- **`src/core/workflow/execution/strategies/retry_strategy.py`** - 重试配置
- **`src/core/workflow/execution/strategies/streaming_strategy.py`** - 流式执行配置
- **`src/core/workflow/execution/strategies/collaboration_strategy.py`** - 协作执行配置

#### 4.2 执行服务配置
- **`src/core/workflow/execution/services/execution_scheduler.py`** - 调度器配置
- **`src/core/workflow/execution/services/execution_manager.py`** - 执行管理器配置

### 5. 图节点配置（低优先级）

#### 5.1 节点配置
- **`src/core/workflow/graph/nodes/wait_node.py`** - 等待节点配置
- **`src/core/workflow/graph/nodes/tool_node.py`** - 工具节点配置
- **`src/core/workflow/graph/nodes/state_machine/`** - 状态机节点配置

#### 5.2 图服务配置
- **`src/core/workflow/graph/service.py`** - 图构建服务配置
- **`src/core/workflow/registry/graph_cache.py`** - 图缓存配置

## 📊 迁移影响分析

### 1. 文件数量统计
- **总文件数**: 约60+个文件
- **高优先级**: 15个文件
- **中优先级**: 25个文件
- **低优先级**: 20+个文件

### 2. 代码行数统计
- **核心配置模块**: 约2000+行
- **模块特定配置**: 约1500+行
- **工作流配置**: 约3000+行
- **执行策略配置**: 约800+行
- **图节点配置**: 约1200+行

### 3. 依赖关系复杂度
- **高复杂度**: 核心配置模块（相互依赖紧密）
- **中复杂度**: 模块特定配置（依赖核心配置）
- **低复杂度**: 执行策略和图节点配置（相对独立）

## 🚀 迁移策略

### 1. 迁移批次

#### 第一批次：核心配置基础设施
1. `src/core/config/models/` - 所有配置模型
2. `src/core/config/base.py` - 基础配置类
3. `src/core/config/config_manager.py` - 配置管理器
4. `src/core/config/validation/` - 验证相关

#### 第二批次：模块特定配置
1. `src/core/state/config/settings.py` - 状态配置
2. `src/core/llm/llm_config_processor.py` - LLM配置
3. `src/core/storage/config.py` - 存储配置
4. `src/core/tools/config.py` - 工具配置

#### 第三批次：工作流配置
1. `src/core/workflow/mappers/config_mapper.py` - 配置映射
2. `src/core/workflow/validation.py` - 配置验证
3. `src/core/workflow/registry/` - 注册表配置
4. `src/core/workflow/templates/` - 模板配置

#### 第四批次：执行和节点配置
1. `src/core/workflow/execution/strategies/` - 执行策略
2. `src/core/workflow/graph/nodes/` - 节点配置
3. `src/core/workflow/graph/service.py` - 图服务

### 2. 迁移原则

#### 2.1 保持功能完整性
- 每个批次迁移后，系统必须能正常运行
- 提供向后兼容的适配器
- 逐步废弃旧接口

#### 2.2 最小化影响范围
- 优先迁移独立性强的模块
- 后迁移依赖性强的模块
- 提供平滑的过渡期

#### 2.3 保证代码质量
- 迁移过程中进行重构优化
- 消除重复代码
- 改进代码结构

## 🔧 迁移工具和方法

### 1. 自动化迁移脚本
```python
# scripts/migrate_config.py
def migrate_config_file(source_path: str, target_path: str):
    """迁移配置文件"""
    # 1. 分析源文件结构
    # 2. 提取配置模型定义
    # 3. 转换为Infrastructure层格式
    # 4. 生成目标文件
    # 5. 创建适配器
```

### 2. 依赖关系分析工具
```python
# scripts/analyze_dependencies.py
def analyze_config_dependencies():
    """分析配置文件依赖关系"""
    # 1. 扫描所有配置文件
    # 2. 分析import关系
    # 3. 生成依赖图
    # 4. 确定迁移顺序
```

### 3. 兼容性测试工具
```python
# scripts/test_compatibility.py
def test_config_compatibility():
    """测试配置兼容性"""
    # 1. 加载旧配置
    # 2. 使用新接口访问
    # 3. 验证结果一致性
    # 4. 生成兼容性报告
```

## 📋 迁移检查清单

### 1. 迁移前检查
- [ ] 备份所有相关文件
- [ ] 创建迁移分支
- [ ] 准备回滚方案
- [ ] 建立测试环境

### 2. 迁移过程检查
- [ ] 按批次执行迁移
- [ ] 每批次后运行测试
- [ ] 验证功能完整性
- [ ] 检查性能影响

### 3. 迁移后检查
- [ ] 清理旧代码
- [ ] 更新文档
- [ ] 培训团队
- [ ] 监控运行状态

## 🎯 预期收益

### 1. 架构改进
- **统一的配置管理**: 所有配置集中在Infrastructure层
- **清晰的职责分离**: 业务逻辑与配置管理完全分离
- **更好的可测试性**: 配置测试和业务测试独立

### 2. 开发效率提升
- **减少重复代码**: 消除各模块重复的配置逻辑
- **提高一致性**: 统一的配置加载、验证和处理
- **更好的开发体验**: 清晰的配置接口和文档

### 3. 维护性改善
- **配置变更不影响业务**: 降低维护成本
- **更好的错误处理**: 统一的配置验证和错误处理
- **更容易的调试**: 清晰的配置加载流程

## 📝 注意事项

### 1. 风险控制
- **渐进式迁移**: 分批次实施，降低风险
- **向后兼容**: 保持API兼容性
- **充分测试**: 每个阶段都有完整测试

### 2. 团队协作
- **详细文档**: 提供迁移指南和最佳实践
- **代码审查**: 严格审查迁移代码
- **知识分享**: 及时分享迁移经验

### 3. 质量保证
- **自动化测试**: 建立完整的测试套件
- **性能监控**: 监控配置加载性能
- **错误监控**: 及时发现和修复问题

---

*本文档将随着迁移进展持续更新，确保迁移过程的透明度和可控性。*