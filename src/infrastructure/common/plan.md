基于对 `src/core/common` 和 `src/infrastructure/common` 目录的深入分析，我强烈建议将基础设施相关模块从核心层迁移到基础设施层。

## 主要发现

### 重复代码问题严重
- cache.py、serialization.py、utils/temporal.py 等核心模块在两个目录中完全重复
- 总计约1500行重复代码需要清理

### 架构层级混乱
- 基础设施组件（缓存、序列化、时间管理等）错误地放置在核心层
- 违反了分层架构原则和依赖方向约束

## 迁移建议

### 应该迁移到 infrastructure/common 的模块：
- cache.py - 通用缓存功能
- serialization.py - 序列化工具
- storage.py - 基础存储实现
- utils/temporal.py - 时间管理工具
- utils/metadata.py - 元数据管理工具
- utils/dict_merger.py - 字典合并工具
- utils/validator.py - 验证工具
- utils/id_generator.py - ID生成器
- exceptions/config.py - 配置异常

### 应该保留在 core/common 的模块：
- 业务异常定义（除配置异常外）
- 核心业务类型定义
- 错误处理框架
- 业务特定的工具类

## 实施策略

1. **分阶段迁移**：先迁移通用工具，再更新依赖，最后清理重复代码
2. **向后兼容**：通过重新导出确保现有代码不受影响
3. **风险控制**：每个阶段充分测试，确保功能完整性

## 预期收益

- **架构清晰性**：符合分层架构原则
- **代码复用**：消除重复代码，提高维护效率
- **职责明确**：核心层专注业务逻辑，基础设施层提供通用功能
- **未来扩展性**：为新的基础设施组件提供清晰的归属

这次迁移是必要的架构优化，能够显著提高代码质量和架构一致性。