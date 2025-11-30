我已经成功完成了config目录错误处理相关模块的重构，解决了职责重叠和重复问题。以下是重构的详细总结：

## 重构前的问题

1. **职责重叠**：
   - [`error_handler.py`](src/core/config/error_handler.py) 和 [`error_recovery.py`](src/core/config/error_recovery.py) 都有名为 `ConfigErrorRecovery` 的类，但功能不同
   - 错误处理逻辑分散在多个模块中，缺乏统一性
   - 职责边界不清，容易混淆

2. **重复代码**：
   - 两个 `ConfigErrorRecovery` 类功能相似但实现不同
   - 恢复策略分散在不同模块中

## 重构方案

### 1. **error_handler.py** - 专注于错误处理和分类
**保留职责**：
- [`ConfigErrorHandler`](src/core/config/error_handler.py:21) 类：配置错误的分类处理
- 错误处理策略和日志记录
- 配置错误处理器注册

**移除职责**：
- 移除了重复的 [`ConfigErrorRecovery`](src/core/config/error_handler.py:164) 类
- 移除了恢复策略相关代码（移至 error_recovery.py）

### 2. **error_recovery.py** - 专注于错误恢复和备份管理
**保留职责**：
- [`ConfigBackupManager`](src/core/config/error_recovery.py:17) 类：配置备份管理
- [`ConfigErrorRecovery`](src/core/config/error_recovery.py:180) 类：统一的配置错误恢复策略
- [`ConfigValidatorWithRecovery`](src/core/config/error_recovery.py:357) 类：带恢复的配置验证

**新增职责**：
- 整合了从 [`error_handler.py`](src/core/config/error_handler.py) 移除的恢复策略
- 统一的配置错误恢复接口
- 包含重试、降级、备份恢复等所有恢复策略

### 3. **callback_manager.py** - 专注于回调管理
**保留职责**：
- 配置变更回调管理
- 回调执行和错误记录

**优化职责**：
- 使用统一的错误处理框架
- 简化错误处理逻辑，添加更丰富的错误上下文

## 重构成果

1. **消除职责重叠**：
   - 每个模块现在都有明确的单一职责
   - 不再有重复的类名和功能

2. **统一错误处理**：
   - 所有模块都使用统一的 [`handle_error`](src/core/common/error_management/error_handling_registry.py:221) 函数
   - 错误上下文信息更加丰富和一致

3. **架构清晰**：
   - [`error_handler.py`](src/core/config/error_handler.py)：纯错误处理和分类
   - [`error_recovery.py`](src/core/config/error_recovery.py)：完整的错误恢复策略
   - [`callback_manager.py`](src/core/config/callback_manager.py)：回调管理和错误记录

4. **类型安全**：
   - 所有重构的模块都通过了 mypy 类型检查
   - 添加了完整的类型注解

## 使用建议

现在这三个模块的职责分工明确：

- **当需要处理配置错误分类和日志时**：使用 [`error_handler.py`](src/core/config/error_handler.py) 中的 [`ConfigErrorHandler`](src/core/config/error_handler.py:21)
- **当需要恢复配置错误时**：使用 [`error_recovery.py`](src/core/config/error_recovery.py) 中的 [`ConfigErrorRecovery`](src/core/config/error_recovery.py:180) 和相关恢复策略
- **当需要管理配置变更回调时**：使用 [`callback_manager.py`](src/core/config/callback_manager.py) 中的 [`ConfigCallbackManager`](src/core/config/callback_manager.py:95)

所有模块都应该通过统一的 [`handle_error`](src/core/common/error_management/error_handling_registry.py:221) 函数进行错误处理，确保错误能够被正确路由到相应的处理器。