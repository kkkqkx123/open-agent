# 使用示例和最佳实践

## 概述

本文档提供了日志模块的详细使用示例和最佳实践指南，帮助开发者快速上手并正确使用日志系统。

## 基础使用示例

### 1. 简单日志记录

```python
from src.services.logger import get_logger, LogLevel

# 获取日志记录器
logger = get_logger("MyApp")

# 记录不同级别的日志
logger.debug("调试信息：变量值", value=42)
logger.info("应用启动成功")
logger.warning("内存使用率较高", usage=85.6)
logger.error("数据库连接失败", error="Connection timeout")
logger.critical("系统内存不足", available_memory="128MB")
```

### 2. 带配置的日志记录器

```python
from src.services.logger import get_logger

# 使用配置创建日志记录器
config = {
    "log_level": "DEBUG",
    "log_outputs": [
        {
            "type": "console",
            "level": "INFO",
            "use_color": True
        },
        {
            "type": "file",
            "level": "DEBUG",
            "filename": "logs/app.log",
            "mode": "a",
            "encoding": "utf-8"
        }
    ]
}

logger = get_logger("MyApp", config)
logger.info("配置化的日志记录器已创建")
```

### 3. 多输出目标

```python
# 同时输出到控制台、文件和JSON
config = {
    "log_level": "INFO",
    "log_outputs": [
        {
            "type": "console",
            "level": "INFO",
            "use_color": True
        },
        {
            "type": "file",
            "level": "DEBUG",
            "filename": "logs/debug.log"
        },
        {
            "type": "json",
            "level": "WARNING",
            "filename": "logs/errors.json",
            "ensure_ascii": False
        }
    ]
}

logger = get_logger("MultiOutputApp", config)
```

## 高级使用示例

### 1. 自定义格式化器

```python
from src.core.logger.formatters import TextFormatter
from src.services.logger import get_logger

# 创建自定义格式化器
custom_formatter = TextFormatter(
    fmt="[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s | %(user_id)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 获取日志记录器并设置格式化器
logger = get_logger("CustomFormatApp")
console_handler = logger.get_handlers()[0]  # 假设第一个是控制台处理器
console_handler.set_formatter(custom_formatter)

# 使用自定义格式记录日志
logger.info("用户操作", user_id=12345, action="login")
# 输出: [2023-01-01 12:00:00] INFO     | CustomFormatApp | 用户操作 | 12345
```

### 2. 自定义处理器

```python
from src.core.logger.handlers import BaseHandler
from src.core.logger.formatters import JsonFormatter
import requests

class WebhookHandler(BaseHandler):
    """自定义Webhook处理器"""
    
    def __init__(self, webhook_url: str, level: LogLevel = LogLevel.ERROR):
        super().__init__(level)
        self.webhook_url = webhook_url
        self.set_formatter(JsonFormatter())
    
    def emit(self, record: Dict[str, Any]) -> None:
        """发送日志到Webhook"""
        formatted_record = self.format(record)
        
        try:
            response = requests.post(
                self.webhook_url,
                json=formatted_record,
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            self.handleError(record)

# 使用自定义处理器
logger = get_logger("WebhookApp")
webhook_handler = WebhookHandler("https://api.example.com/webhooks/logs")
logger.add_handler(webhook_handler)

logger.error("严重错误", error="Database connection failed")
```

### 3. 脱敏功能使用

```python
from src.services.logger import LogRedactor, get_logger

# 创建脱敏器
redactor = LogRedactor(hash_sensitive=True)

# 添加自定义脱敏规则
redactor.add_pattern(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b', '****-****-****-****')

# 设置脱敏器
logger = get_logger("SecureApp")
logger.set_redactor(redactor)

# 记录包含敏感信息的日志
logger.info("用户支付", 
           user_id=12345, 
           credit_card="1234-5678-9012-3456",
           api_key="sk-abc123def456")

# 输出（脱敏后）:
# 用户支付 user_id=12345 credit_card=****-****-****-**** api_key=sk-abc123a1b2c3d4def456
```

### 4. 错误处理集成

```python
from src.services.logger import handle_error, ErrorType, error_handler

# 基本错误处理
try:
    # 一些可能出错的操作
    result = 1 / 0
except Exception as e:
    handle_error(e, ErrorType.APPLICATION_ERROR, operation="division")

# 自定义错误处理程序
def handle_database_error(error: Exception, **context):
    """处理数据库错误"""
    logger = get_logger("DatabaseErrorHandler")
    logger.error(f"数据库错误: {error}", **context)
    
    # 发送告警
    send_alert(f"数据库错误: {error}")

# 注册错误处理程序
from src.services.logger import register_error_handler
register_error_handler(ErrorType.DATABASE_ERROR, handle_database_error)

# 使用错误处理装饰器
@error_handler(ErrorType.NETWORK_ERROR)
def make_api_request(url: str):
    """API请求函数"""
    import requests
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# 使用装饰器保护的函数
try:
    data = make_api_request("https://api.example.com/data")
except Exception:
    # 错误已被处理，但仍然抛出
    pass
```

### 5. 指标收集

```python
from src.services.logger import get_global_metrics_collector, get_logger

# 获取全局指标收集器
metrics = get_global_metrics_collector()

# 在应用中使用指标
logger = get_logger("MetricsApp")

def process_user_request(user_id: int, request_type: str):
    """处理用户请求"""
    start_time = time.time()
    
    try:
        # 增加请求计数
        metrics.increment_counter("user_requests", labels={"type": request_type})
        
        # 处理请求
        logger.info(f"处理用户请求: {request_type}", user_id=user_id)
        
        # 记录成功
        metrics.increment_counter("successful_requests", labels={"type": request_type})
        
    except Exception as e:
        # 记录失败
        metrics.increment_counter("failed_requests", labels={"type": request_type})
        handle_error(e, ErrorType.APPLICATION_ERROR, user_id=user_id, request_type=request_type)
        raise
    
    finally:
        # 记录响应时间
        response_time = time.time() - start_time
        metrics.observe_histogram("request_duration", response_time, labels={"type": request_type})
        
        # 更新活跃用户数
        metrics.set_gauge("active_users", get_active_user_count())

# 使用示例
process_user_request(12345, "login")
process_user_request(12346, "data_query")
```

### 6. 结构化日志

```python
from src.services.logger import StructuredFileLogger, LogRedactor

# 创建结构化日志记录器
structured_logger = StructuredFileLogger(
    "logs/structured.json",
    LogLevel.INFO,
    LogRedactor()
)

# 记录结构化日志
structured_logger.info(
    "用户登录",
    user_id=12345,
    username="john_doe",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    session_id="sess_abc123def456",
    timestamp="2023-01-01T12:00:00Z"
)

# 输出JSON格式:
# {
#     "timestamp": "2023-01-01T12:00:00",
#     "level": "INFO",
#     "message": "用户登录",
#     "thread_id": 12345,
#     "process_id": 6789,
#     "user_id": 12345,
#     "username": "john_doe",
#     "ip_address": "192.168.1.100",
#     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
#     "session_id": "sess_abc123def456"
# }
```

## 最佳实践

### 1. 日志级别使用指南

```python
# DEBUG: 详细的调试信息，仅在开发环境使用
logger.debug("进入函数", function="process_data", args={"data": data})

# INFO: 一般信息，记录程序正常运行状态
logger.info("用户操作", user_id=123, action="login", ip="192.168.1.1")

# WARNING: 警告信息，表示潜在问题但不影响正常运行
logger.warning("内存使用率较高", usage=85.6, threshold=80.0)

# ERROR: 错误信息，表示程序出现错误但可继续运行
logger.error("API调用失败", url="https://api.example.com", status_code=500, error="Internal Server Error")

# CRITICAL: 严重错误，表示程序可能无法继续运行
logger.critical("数据库连接池耗尽", active_connections=100, max_connections=100)
```

### 2. 结构化日志最佳实践

```python
# 好的实践：使用结构化字段
logger.info(
    "订单处理完成",
    order_id="ORD123456",
    user_id=789,
    amount=99.99,
    currency="USD",
    payment_method="credit_card",
    processing_time=1.23,
    status="success"
)

# 避免的实践：将所有信息放在消息中
logger.info("订单处理完成: 订单ID=ORD123456, 用户ID=789, 金额=99.99 USD, 支付方式=credit_card, 处理时间=1.23s, 状态=success")
```

### 3. 敏感信息处理

```python
# 好的实践：使用脱敏器
logger.info("API调用", 
           endpoint="/api/users",
           method="POST",
           api_key="sk-abc123def456")  # 会被自动脱敏

# 好的实践：避免记录敏感信息
logger.info("用户认证", 
           user_id=123,
           auth_method="password")
# 不要记录: logger.info("用户认证", password="secret123")

# 好的实践：使用占位符
logger.info("数据库连接", 
           host="localhost",
           port=5432,
           database="myapp",
           username="admin",
           password="***")  # 手动脱敏
```

### 4. 性能考虑

```python
# 好的实践：使用级别检查避免不必要的字符串格式化
if logger.isEnabledFor(LogLevel.DEBUG):
    logger.debug(f"复杂数据处理: {expensive_operation()}")

# 或者使用延迟格式化
logger.debug("复杂数据处理: %s", lambda: expensive_operation())

# 避免的实践：总是进行字符串格式化
logger.debug(f"复杂数据处理: {expensive_operation()}")  # 即使DEBUG级别关闭也会执行
```

### 5. 异常处理

```python
# 好的实践：记录异常信息
try:
    result = risky_operation()
except Exception as e:
    logger.error("操作失败", 
                operation="risky_operation",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True)  # 记录完整的异常堆栈
    raise

# 好的实践：使用全局错误处理器
@error_handler(ErrorType.DATABASE_ERROR)
def execute_query(query: str):
    """执行数据库查询"""
    # 数据库操作
    pass
```

### 6. 日志轮转和归档

```python
# 好的实践：按日期和大小轮转日志
import logging.handlers
from src.core.logger.handlers import FileHandler

class RotatingFileHandler(FileHandler):
    """支持轮转的文件处理器"""
    
    def __init__(self, filename: str, max_bytes: int = 10*1024*1024, backup_count: int = 5):
        super().__init__(filename)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._setup_rotation()
    
    def _setup_rotation(self):
        """设置日志轮转"""
        # 实现日志轮转逻辑
        pass

# 使用轮转处理器
rotating_handler = RotatingFileHandler(
    "logs/app.log",
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5
)
logger.add_handler(rotating_handler)
```

### 7. 配置管理

```python
# 好的实践：使用环境变量配置
import os
from src.services.logger import set_global_config

config = {
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "log_outputs": [
        {
            "type": "console",
            "level": os.getenv("CONSOLE_LOG_LEVEL", "INFO"),
            "use_color": os.getenv("LOG_COLOR", "false").lower() == "true"
        },
        {
            "type": "file",
            "level": os.getenv("FILE_LOG_LEVEL", "DEBUG"),
            "filename": os.getenv("LOG_FILE", "logs/app.log")
        }
    ]
}

set_global_config(config)
```

### 8. 测试中的日志使用

```python
# 好的实践：在测试中使用内存处理器
import io
from src.core.logger.handlers import BaseHandler

class MemoryHandler(BaseHandler):
    """内存处理器，用于测试"""
    
    def __init__(self):
        super().__init__()
        self.records = []
    
    def emit(self, record: Dict[str, Any]) -> None:
        self.records.append(record)

# 测试示例
def test_user_login():
    memory_handler = MemoryHandler()
    logger = get_logger("TestApp")
    logger.add_handler(memory_handler)
    
    # 执行测试
    user_login("testuser", "password")
    
    # 验证日志
    assert len(memory_handler.records) == 1
    assert memory_handler.records[0]["message"] == "用户登录成功"
    assert memory_handler.records[0]["user_id"] == 123
```

## 常见问题和解决方案

### 1. 日志性能问题

**问题**：高频日志记录影响性能

**解决方案**：
- 使用适当的日志级别
- 实现异步日志处理器
- 使用日志缓冲和批量写入

```python
class AsyncHandler(BaseHandler):
    """异步处理器"""
    
    def __init__(self, target_handler: BaseHandler, buffer_size: int = 100):
        super().__init__()
        self.target_handler = target_handler
        self.buffer = []
        self.buffer_size = buffer_size
        self._lock = threading.Lock()
    
    def emit(self, record: Dict[str, Any]) -> None:
        with self._lock:
            self.buffer.append(record)
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """刷新缓冲区"""
        for record in self.buffer:
            self.target_handler.emit(record)
        self.buffer.clear()
```

### 2. 日志文件过大

**问题**：日志文件增长过快

**解决方案**：
- 实现日志轮转
- 使用压缩归档
- 设置日志保留策略

### 3. 敏感信息泄露

**问题**：日志中包含敏感信息

**解决方案**：
- 使用脱敏器
- 审查日志输出
- 实施日志访问控制

### 4. 多进程日志

**问题**：多进程环境下日志冲突

**解决方案**：
- 使用进程安全的处理器
- 实现日志队列
- 使用专门的日志服务

通过遵循这些最佳实践，可以构建一个高效、安全、可维护的日志系统。