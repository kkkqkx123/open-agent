# 统一日志系统使用指南

## 概述

本项目已全面采用统一日志系统，替换了所有直接使用Python标准库`logging`模块的代码。统一日志系统提供了更强大的功能，包括日志脱敏、结构化输出、多处理器支持等。

## 系统架构

### 核心组件

1. **接口层**：`src/interfaces/common_infra.py` - 定义 `ILogger` 接口
2. **实现层**：`src/services/logger/logger.py` - 实现 `Logger` 类
3. **工具层**：`src/services/logger/` - 提供日志脱敏、错误处理等功能

### 主要特性

- **统一接口**：所有模块使用相同的日志接口
- **日志脱敏**：自动脱敏敏感信息
- **多处理器**：支持控制台、文件、JSON等多种输出格式
- **线程安全**：支持多线程环境
- **配置驱动**：通过配置文件控制日志行为

## 使用方法

### 基本用法

```python
# 导入统一日志系统
from src.services.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 记录日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 带参数的日志

```python
# 支持关键字参数
logger.info("用户操作", user_id="123", action="login", ip="192.168.1.1")

# 支持格式化字符串
logger.error("处理失败: %s", error_message)
```

### 日志级别设置

```python
from src.services.logger import LogLevel

# 设置日志级别
logger.set_level(LogLevel.DEBUG)
```

## 配置说明

### 全局配置

通过 `set_global_config()` 设置全局配置：

```python
from src.services.logger import set_global_config

config = {
    "log_level": "INFO",
    "log_outputs": [
        {
            "type": "console",
            "level": "INFO"
        },
        {
            "type": "file",
            "level": "DEBUG",
            "filename": "logs/app.log"
        },
        {
            "type": "json",
            "level": "ERROR",
            "filename": "logs/errors.json"
        }
    ]
}

set_global_config(config)
```

### 配置参数说明

- `log_level`: 全局日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_outputs`: 日志输出配置列表
  - `type`: 输出类型 (console, file, json)
  - `level`: 该输出的日志级别
  - `filename`: 文件输出路径（仅file和json类型需要）

## 迁移指南

### 从标准logging迁移

**旧代码**：
```python
import logging

logger = logging.getLogger(__name__)
logger.info("信息日志")
```

**新代码**：
```python
from src.services.logger import get_logger

logger = get_logger(__name__)
logger.info("信息日志")
```

### 批量替换

项目已使用自动化脚本完成了所有文件的替换：

- 核心模块：127个文件
- 服务层：70个文件  
- 适配器层：49个文件

总计246个文件成功迁移到统一日志系统。

## 最佳实践

### 1. 日志记录器命名

使用 `__name__` 作为日志记录器名称，确保日志来源清晰：

```python
logger = get_logger(__name__)  # 推荐
logger = get_logger("CustomName")  # 不推荐
```

### 2. 日志级别使用

- **DEBUG**: 详细的调试信息，仅在开发时使用
- **INFO**: 一般信息，记录正常运行状态
- **WARNING**: 警告信息，表示潜在问题但不影响运行
- **ERROR**: 错误信息，表示错误但程序可继续
- **CRITICAL**: 严重错误，表示程序可能无法继续

### 3. 结构化日志

使用关键字参数记录结构化信息：

```python
# 推荐
logger.info("用户登录", user_id="123", ip="192.168.1.1", timestamp="2023-01-01T10:00:00")

# 不推荐
logger.info("用户123从192.168.1.1在2023-01-01T10:00:00登录")
```

### 4. 敏感信息处理

系统会自动脱敏敏感信息，但建议在记录时避免直接记录敏感数据：

```python
# 系统会自动脱敏
logger.info("用户认证", token="sk-1234567890abcdef")

# 或者手动脱敏
logger.info("用户认证", token=mask_token(token))
```

## 错误处理

### 日志记录错误

日志系统内置了错误处理机制，即使日志记录本身出错也不会影响主程序：

```python
# 日志处理器错误会被捕获并打印，不会抛出异常
logger.error("这条日志可能因为处理器问题而失败")
```

### 自定义错误处理

```python
from src.services.logger import get_global_error_handler

error_handler = get_global_error_handler()
error_handler.register_error_handler("custom", handle_custom_error)
```

## 性能考虑

### 1. 日志级别检查

在高频代码中，先检查日志级别：

```python
if logger.should_log(LogLevel.DEBUG):
    expensive_operation()
    logger.debug("调试信息", result=result)
```

### 2. 异步日志

对于高性能场景，考虑使用异步日志处理器：

```python
config = {
    "log_outputs": [
        {
            "type": "async_file",
            "level": "INFO",
            "filename": "logs/app.log"
        }
    ]
}
```

## 故障排除

### 常见问题

1. **日志不显示**
   - 检查日志级别设置
   - 确认处理器配置正确

2. **日志格式异常**
   - 检查配置文件格式
   - 确认所有必需参数都已提供

3. **性能问题**
   - 调整日志级别
   - 使用异步处理器
   - 优化日志记录频率

### 调试技巧

```python
# 启用详细日志来调试日志系统本身
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查日志记录器状态
print(f"当前级别: {logger.get_level()}")
print(f"处理器数量: {len(logger.get_handlers())}")
```

## 总结

统一日志系统为项目提供了强大、灵活、安全的日志记录能力。通过遵循本文档的指南，开发者可以有效地使用日志系统来监控、调试和维护应用程序。

所有代码已成功迁移到统一日志系统，享受更好的日志管理体验！