# `src\infrastructure\config` 文件迁移详细列表

## 文件迁移总览

本文件提供了 `src\infrastructure\config` 目录下所有文件的详细迁移计划，包括原路径、新路径、迁移类型和优先级。

## 核心功能迁移到 `src/core/config/`

### 配置模型文件

| 原文件路径 | 新文件路径 | 迁移类型 | 优先级 | 说明 |
|------------|------------|----------|---------|------|
| `models/base.py` | `src/core/config/models.py` | 内容合并 | 高 | 基础配置模型 |
| `models/global_config.py` | `src/core/config/models.py` | 内容合并 | 高 | 全局配置模型 |
| `models/llm_config.py` | `src/core/config/models.py` | 内容合并 | 高 | LLM配置模型 |
| `models/tool_config.py` | `src/core/config/models.py` | 内容合并 | 高 | 工具配置模型 |
| `models/token_counter_config.py` | `src/core/config/models.py` | 内容合并 | 中 | Token计数器配置模型 |
| `models/task_group_config.py` | `src/core/config/models.py` | 内容合并 | 中 | 任务组配置模型 |
| `models/checkpoint_config.py` | `src/core/config/models.py` | 内容合并 | 中 | 检查点配置模型 |
| `models/connection_pool_config.py` | `src/core/config/models.py` | 内容合并 | 中 | 连接池配置模型 |
| `models/retry_timeout_config.py` | `src/core/config/models.py` | 内容合并 | 中 | 重试超时配置模型 |

### 配置加载器文件

| 原文件路径 | 新文件路径 | 迁移类型 | 优先级 | 说明 |
|------------|------------|----------|---------|------|
| `loader/file_config_loader.py` | `src/core/config/yaml_loader.py` | 功能整合 | 高 | YAML文件加载器 |
| `config_loader.py` | `src/core/config/config_loader.py` | 功能整合 | 高 | 配置加载器包装器 |

### 配置处理器文件

| 原文件路径 | 新文件路径 | 迁移类型 | 优先级 | 说明 |
|------------|------------|----------|---------|------|
| `processor/validator.py` | `src/core/config/config_processor.py` | 功能整合 | 高 | 配置验证器 |
| `processor/enhanced_validator.py` | `src/core/config/config_processor.py` | 功能整合 | 中 | 增强验证器 |

## 业务逻辑适配到 `src/adapters/config/`

### 配置系统适配器

| 原文件路径 | 新文件路径 | 迁移类型 | 优先级 | 说明 |
|------------|------------|----------|---------|------|
| `config_system.py` | `src/adapters/config/config_system_adapter.py` | 重构 | 高 | 配置系统适配器 |
| `interfaces.py` | `src/adapters/config/interfaces.py` | 保留 | 高 | 适配器接口 |

### 配置服务适配器

| 原文件路径 | 新文件路径 | 迁移类型 | 优先级 | 说明 |
|------------|------------|----------|---------|------|
| `service/config_factory.py` | `src/adapters/config/services/config_factory.py` | 移动 | 中 | 配置工厂服务 |
| `service/checkpoint_service.py` | `src/adapters/config/services/checkpoint_service.py` | 移动 | 中 | 检查点配置服务 |
| `service/callback_manager.py` | `src/adapters/config/services/callback_manager.py` | 移动 | 中 | 回调管理器 |
| `service/error_recovery.py` | `src/adapters/config/services/error_recovery.py` | 移动 | 中 | 错误恢复服务 |

## 工具类整合到 `src/core/common/utils/`

| 原文件路径 | 新文件路径 | 迁移类型 | 优先级 | 说明 |
|------------|------------|----------|---------|------|
| `utils/config_operations.py` | `src/core/common/utils/config_ops.py` | 整合 | 低 | 配置操作工具 |
| `utils/redactor.py` | `src/core/common/utils/redactor.py` | 整合 | 低 | 敏感信息脱敏工具 |
| `utils/inheritance_handler.py` | `src/core/common/utils/inheritance.py` | 整合 | 低 | 继承处理工具 |
| `utils/schema_loader.py` | `src/core/common/utils/schema.py` | 整合 | 低 | 模式加载工具 |

## 需要删除的文件

以下文件在新架构中功能已被替代，建议删除：

| 文件路径 | 删除原因 | 替代方案 |
|----------|----------|----------|
| `config_cache.py` | 功能已整合到通用缓存 | `src/core/common/cache.py` |
| `config_loader.py` | 功能重复 | `src/core/config/config_loader.py` |
| `base.py` | 模型已整合 | `src/core/config/models.py` |
| `config_system.py` | 重构为适配器 | `src/adapters/config/config_system_adapter.py` |

## 迁移依赖关系

### 第一阶段依赖（高优先级）
1. 核心配置模型迁移 (`models/` → `src/core/config/models.py`)
2. 配置加载器迁移 (`loader/` → `src/core/config/yaml_loader.py`)
3. 配置处理器迁移 (`processor/` → `src/core/config/config_processor.py`)

### 第二阶段依赖（中优先级）
1. 配置系统适配器创建 (`config_system.py` → `src/adapters/config/config_system_adapter.py`)
2. 服务适配器迁移 (`service/` → `src/adapters/config/services/`)
3. 接口适配 (`interfaces.py` → `src/adapters/config/interfaces.py`)

### 第三阶段依赖（低优先级）
1. 工具类整合 (`utils/` → `src/core/common/utils/`)
2. 清理冗余文件

## 迁移检查清单

### 第一阶段检查项
- [ ] 核心配置模型整合完成
- [ ] YAML加载器功能正常
- [ ] 配置处理器功能正常
- [ ] 单元测试通过

### 第二阶段检查项
- [ ] 配置系统适配器创建完成
- [ ] 服务适配器迁移完成
- [ ] 接口适配完成
- [ ] 集成测试通过

### 第三阶段检查项
- [ ] 工具类整合完成
- [ ] 冗余文件清理完成
- [ ] 性能测试通过
- [ ] 回归测试通过

## 注意事项

1. **向后兼容性**: 迁移过程中需要确保现有代码的兼容性
2. **依赖更新**: 需要更新所有依赖配置系统的模块
3. **测试覆盖**: 每个迁移阶段都需要充分的测试覆盖
4. **文档更新**: 迁移完成后需要更新相关文档

## 风险控制

1. **备份策略**: 迁移前备份所有相关文件
2. **回滚计划**: 准备快速回滚方案
3. **监控机制**: 迁移过程中监控系统稳定性
4. **分阶段实施**: 避免一次性大规模迁移

## 总结

本文件提供了详细的文件迁移列表和依赖关系，建议按照优先级分阶段实施迁移。每个阶段完成后都需要进行充分的测试验证，确保系统功能正常。

**文档版本**: 1.0  
**创建时间**: 2025-11-18