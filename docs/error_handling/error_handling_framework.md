# 统一错误处理框架文档

## 概述

统一错误处理框架为 Modular Agent Framework 提供了一个集中、标准化的错误处理机制。该框架基于分层架构设计，支持错误分类、严重度评估、恢复策略和统一处理。

## 核心组件

### 1. 错误分类系统 (`ErrorCategory`)

定义了11种错误分类：

- `VALIDATION` - 验证错误
- `CONFIGURATION` - 配置错误
- `RESOURCE` - 资源错误
- `NETWORK` - 网络错误
- `STORAGE` - 存储错误
- `STATE` - 状态错误
- `EXECUTION` - 执行错误
- `INTEGRATION` - 集成错误
- `TOOL` - 工具错误
- `WORKFLOW` - 工作流错误
- `LLM` - LLM错误
- `PROMPT` - 提示词错误

### 2. 错误严重度 (`ErrorSeverity`)

定义了5个严重度级别：

- `CRITICAL` - 必须立即处理
- `HIGH` - 需要立即处理
- `MEDIUM` - 应该处理
- `LOW` - 可以延迟处理
- `INFO` - 信息性错误

### 3. 错误处理器接口 (`IErrorHandler`)

定义了错误处理器的标准接口：

```python
class IErrorHandler(ABC):
    def can_handle(self, error: Exception) -> bool:
        """是否可以处理该错误"""
        
    def handle(self, error: Exception, context: Dict[str, Any]) -> None:
        """处理错误"""
```

### 4. 错误处理注册表 (`ErrorHandlingRegistry`)

核心的单例注册表，负责：

- 注册错误处理器
- 注册恢复策略
- 注册错误映射
- 统一错误处理

### 5. 标准错误处理模式

提供了3种标准错误处理模式：

- `operation_with_retry` - 带重试的操作执行
- `operation_with_fallback` - 带降级的操作执行
- `safe_execution` - 安全执行模式

## 快速开始

### 1. 基本使用

```python
from src.core.common.error_management import (
    ErrorHandlingRegistry, ErrorCategory, ErrorSeverity,
    BaseErrorHandler, register_error_handler, handle_error
)
from src.core.common.exceptions import ConfigError

# 创建自定义错误处理器
class MyErrorHandler(BaseErrorHandler):
    def __init__(self):
        super().__init__(ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH)
    
    def can_handle(self, error: Exception) -> bool:
        return isinstance(error, ConfigError)
    
    def handle(self, error: Exception, context: Dict = None) -> None:
        print(f"处理配置错误: {error}")

# 注册处理器
register_error_handler(ConfigError, MyErrorHandler())

# 使用统一错误处理
try:
    raise ConfigError("配置文件错误")
except Exception as e:
    handle_error(e, context={"module": "config_loader"})
```

### 2. 使用标准模式

```python
from src.core.common.error_management import operation_with_retry

# 带重试的操作
result = operation_with_retry(
    lambda: some_operation(),
    max_retries=3,
    backoff_factor=2.0
)

# 带降级的操作
result = operation_with_fallback(
    primary_operation,
    fallback_operation
)

# 安全执行
result = safe_execution(
    operation,
    validation_func=validate_input,
    cleanup_func=cleanup
)
```

## 架构设计

### 分层错误处理

框架支持分层错误处理策略：

1. **模块级处理** - 各模块定义自己的错误处理器
2. **服务级处理** - 服务层提供统一的错误处理
3. **全局级处理** - 应用层提供全局错误处理

### 错误处理流程

```
异常发生 → 查找处理器 → 执行处理 → 记录日志 → 决定恢复策略
```

### 恢复策略

框架支持多种恢复策略：

- **重试机制** - 指数退避重试
- **降级机制** - 主备切换
- **回滚机制** - 状态回滚
- **优雅降级** - 功能降级

## 集成指南

### 1. 现有代码集成

对于现有代码，建议逐步集成：

```python
# 传统方式
try:
    operation()
except Exception as e:
    logger.error(f"操作失败: {e}")
    raise

# 新框架方式
try:
    operation()
except Exception as e:
    handle_error(e, context={"operation": "some_operation"})
    raise
```

### 2. 新代码开发

新代码应该直接使用框架提供的模式：

```python
from src.core.common.error_management import safe_execution

class MyService:
    def critical_operation(self, data):
        return safe_execution(
            lambda: self._do_operation(data),
            validation_func=lambda: self._validate(data),
            context={"service": "MyService", "operation": "critical_operation"}
        )
```

## 配置管理

### 错误映射配置

可以通过注册表配置错误映射：

```python
registry = ErrorHandlingRegistry()
registry.register_error_mapping(
    "network_error",
    {
        "severity": ErrorSeverity.HIGH,
        "category": ErrorCategory.NETWORK,
        "recovery_strategy": "retry_with_backoff"
    }
)
```

### 恢复策略配置

```python
registry.register_recovery_strategy(
    "retry_with_backoff",
    lambda error, context: operation_with_retry(...)
)
```

## 最佳实践

### 1. 错误分类

- 根据业务领域选择合适的错误分类
- 避免过度细分，保持分类的简洁性

### 2. 严重度评估

- 根据错误对系统的影响评估严重度
- 关键路径的错误应该标记为 HIGH 或 CRITICAL

### 3. 上下文信息

- 在处理错误时提供丰富的上下文信息
- 上下文信息有助于问题诊断和恢复

### 4. 恢复策略选择

- 根据错误类型选择合适的恢复策略
- 网络错误适合重试，配置错误可能需要人工干预

## 性能考虑

- 错误处理不应该成为性能瓶颈
- 使用轻量级的错误处理器
- 避免在错误处理中进行复杂的计算

## 监控和日志

- 所有错误都应该被记录
- 使用结构化日志记录错误信息
- 监控错误率和恢复成功率

## 扩展性

框架设计具有良好的扩展性：

- 可以添加新的错误分类
- 可以自定义错误处理器
- 可以集成第三方监控工具

## 故障排除

### 常见问题

1. **处理器未注册** - 确保错误处理器已正确注册
2. **上下文信息缺失** - 提供足够的上下文信息
3. **恢复策略无效** - 检查恢复策略配置

### 调试技巧

- 启用详细日志记录
- 使用错误处理演示程序测试
- 检查错误映射配置

## 版本兼容性

框架设计为向后兼容：

- 新版本不会破坏现有API
- 新增功能通过扩展实现
- 废弃功能会有明确的标记和迁移指南

## 总结

统一错误处理框架为 Modular Agent Framework 提供了强大而灵活的错误处理能力。通过标准化错误分类、严重度评估和恢复策略，框架能够显著提高系统的可靠性和可维护性。