# 服务层组件文档

## 概述

服务层组件位于 `src/services/logger/` 目录，提供了日志系统的高级功能和业务逻辑。这些组件构建在核心层之上，提供了完整的日志服务解决方案。

## 日志记录器 (Logger)

### 功能描述

`Logger` 是日志系统的主要入口，实现了 `ILogger` 接口，提供了完整的日志记录功能。它整合了格式化器、处理器和脱敏器，支持多线程安全和配置驱动。

### 核心接口

```python
class ILogger(ABC):
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        pass
```

### 主要功能

#### 1. 日志记录
```python
# 基本日志记录
logger.debug("调试信息")
logger.info("用户登录", user_id=123, ip="192.168.1.1")
logger.warning("内存使用率过高", usage=85.6)
logger.error("数据库连接失败", error="Connection timeout")
logger.critical("系统崩溃", exception="OutOfMemoryError")
```

#### 2. 级别管理
```python
# 设置日志级别
logger.set_level(LogLevel.WARNING)

# 获取当前级别
current_level = logger.get_level()
```

#### 3. 处理器管理
```python
# 添加处理器
logger.add_handler(console_handler)
logger.add_handler(file_handler)

# 移除处理器
logger.remove_handler(console_handler)

# 获取所有处理器
handlers = logger.get_handlers()
```

#### 4. 脱敏器设置
```python
# 设置脱敏器
logger.set_redactor(custom_redactor)
```

### 高级特性

#### 1. 线程安全
```python
# 使用RLock确保线程安全
with self._lock:
    for handler in self._handlers:
        try:
            handler.handle(redacted_record)
        except Exception as e:
            print(f"日志处理器错误: {e}")
```

#### 2. 配置驱动
```python
def _setup_handlers_from_config(self, config: Dict[str, Any]) -> None:
    """根据配置设置处理器"""
    log_outputs = config.get("log_outputs", [{"type": "console"}])
    for output_config in log_outputs:
        handler_type = output_config.get("type", "console")
        handler_level = LogLevel.from_string(output_config.get("level", "INFO"))
        
        if handler_type == "console":
            handler = ConsoleHandler(handler_level, output_config)
        elif handler_type == "file":
            handler = FileHandler(handler_level, output_config)
        elif handler_type == "json":
            handler = JsonHandler(handler_level, output_config)
        
        self.add_handler(handler)
```

#### 3. 日志记录结构
```python
def _create_log_record(self, level: LogLevel, message: str, **kwargs: Any) -> Dict[str, Any]:
    """创建日志记录"""
    return {
        "name": self.name,
        "level": level,
        "message": message,
        "timestamp": datetime.now(),
        "thread_id": threading.get_ident(),
        "process_id": os.getpid(),
        **kwargs,
    }
```

### 全局日志管理

#### 1. 日志记录器注册表
```python
# 全局日志记录器字典
_loggers: Dict[str, Logger] = {}
_loggers_lock = threading.RLock()

def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> Logger:
    """获取或创建日志记录器"""
    with _loggers_lock:
        if name not in _loggers:
            _loggers[name] = Logger(name, config)
        return _loggers[name]
```

#### 2. 全局配置管理
```python
def set_global_config(config: Dict[str, Any]) -> None:
    """设置全局配置，更新所有已创建的日志记录器"""
    global _global_config
    _global_config = config
    
    with _loggers_lock:
        for logger in _loggers.values():
            # 更新配置和处理器
            logger._config = config
            logger._setup_handlers_from_config(config)
```

## 脱敏器 (LogRedactor)

### 功能描述

`LogRedactor` 提供了日志敏感信息脱敏功能，通过正则表达式模式识别和替换敏感信息，保护系统安全。

### 默认敏感信息模式

| 类型 | 模式 | 替换 | 示例 |
|------|------|------|------|
| OpenAI API Key | `sk-[a-zA-Z0-9]{20,}` | `sk-***` | `sk-abc123def456` → `sk-***` |
| 邮箱地址 | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b` | `***@***.***` | `user@example.com` → `***@***.***` |
| 手机号（中国） | `1[3-9]\d{9}` | `1*********` | `13812345678` → `1*********` |
| 身份证号 | `\b[1-9]\d{5}(18\|19\|20)\d{2}(0[1-9]\|1[0-2])(0[1-9]\|[12]\d\|3[01])\d{3}[\dXx]\b` | `***************` | `110101199001011234` → `***************` |
| 密码字段 | `(["\']?password["\']?\s*[:=]\s*["\']?)[^"\',\s}]+` | `\1***PASSWORD***` | `password: secret123` → `password: ***PASSWORD***` |
| Token | `(["\']?token["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_-]{20,}` | `\1***TOKEN***` | `token: abc123def456` → `token: ***TOKEN***` |
| JWT Token | `eyJ[a-zA-Z0-9._-]*\.eyJ[a-zA-Z0-9._-]*\.[a-zA-Z0-9._-]*` | `JWT.***.***` | `eyJhbGciOi...` → `JWT.***.***` |

### 核心功能

#### 1. 基本脱敏
```python
redactor = LogRedactor()

# 脱敏文本
text = "API Key: sk-abc123def456, Email: user@example.com"
redacted = redactor.redact(text)
# 结果: "API Key: sk-***, Email: ***@***.***"
```

#### 2. 级别感知脱敏
```python
# DEBUG级别不脱敏
redacted_debug = redactor.redact(text, LogLevel.DEBUG)  # 原样返回

# 其他级别进行脱敏
redacted_info = redactor.redact(text, LogLevel.INFO)    # 脱敏处理
```

#### 3. 哈希脱敏
```python
# 启用哈希脱敏
redactor = LogRedactor(hash_sensitive=True)

# 对敏感信息进行哈希替换
text = "API Key: sk-abc123def456"
redacted = redactor.redact(text)
# 结果: "API Key: sk-abc123a1b2c3d4def456" (保留前后3位，中间8位哈希)
```

### 高级功能

#### 1. 自定义模式
```python
# 添加自定义模式
redactor.add_pattern(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b', '****-****-****-****')

# 移除模式
redactor.remove_pattern(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b')

# 清除所有模式
redactor.clear_patterns()

# 重置为默认模式
redactor.reset_to_default()
```

#### 2. 脱敏测试
```python
# 测试脱敏效果
result = redactor.test_redaction("API Key: sk-abc123def456")
print(result)
# {
#     "original": "API Key: sk-abc123def456",
#     "redacted": "API Key: sk-***",
#     "has_changes": True,
#     "matched_patterns": [
#         {
#             "pattern": "sk-[a-zA-Z0-9]{20,}",
#             "replacement": "sk-***",
#             "matches": 1
#         }
#     ]
# }
```

#### 3. 缓存机制
```python
# 脱敏结果缓存，提高性能
cache_key = f"{text}_{level.value}"
if cache_key in self._cache:
    return self._cache[cache_key]
```

### 自定义脱敏器

```python
class CustomLogRedactor(LogRedactor):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        patterns = self._load_patterns_from_config()
        hash_sensitive = self.config.get("hash_sensitive", False)
        super().__init__(patterns, hash_sensitive)
    
    def _load_patterns_from_config(self) -> Optional[List[tuple[Pattern, str]]]:
        """从配置加载模式"""
        patterns_config = self.config.get("patterns")
        if not patterns_config:
            return None
        
        compiled_patterns = []
        for pattern_config in patterns_config:
            pattern_str = pattern_config.get("pattern")
            replacement = pattern_config.get("replacement", "***")
            if pattern_str:
                compiled_pattern = re.compile(pattern_str)
                compiled_patterns.append((compiled_pattern, replacement))
        
        return compiled_patterns if compiled_patterns else None
```

## 错误处理器 (ErrorHandler)

### 功能描述

`GlobalErrorHandler` 提供了全局错误处理功能，支持分类错误处理、错误上下文记录和自定义错误处理程序注册。

### 错误类型

```python
class ErrorType(Enum):
    APPLICATION_ERROR = "application_error"      # 应用程序错误
    CONFIGURATION_ERROR = "configuration_error"  # 配置错误
    VALIDATION_ERROR = "validation_error"        # 验证错误
    NETWORK_ERROR = "network_error"              # 网络错误
    DATABASE_ERROR = "database_error"            # 数据库错误
    SECURITY_ERROR = "security_error"            # 安全错误
```

### 核心功能

#### 1. 错误处理
```python
# 获取全局错误处理器
error_handler = get_global_error_handler()

# 处理错误
error_handler.handle_error(
    error="数据库连接失败",
    error_type=ErrorType.DATABASE_ERROR,
    host="localhost",
    port=5432,
    database="myapp"
)

# 处理异常
try:
    # 一些可能出错的操作
    pass
except Exception as e:
    error_handler.handle_error(e, ErrorType.APPLICATION_ERROR, user_id=123)
```

#### 2. 错误信息构建
```python
def _build_error_info(self, error: Union[Exception, str], error_type: ErrorType, **context: Any) -> Dict[str, Any]:
    """构建错误信息"""
    error_info = {
        "type": error_type.value,
        "timestamp": datetime.now().isoformat(),
        "context": context
    }
    
    if isinstance(error, Exception):
        error_info["message"] = str(error)
        error_info["exception_type"] = type(error).__name__
        error_info["traceback"] = traceback.format_exception(type(error), error, error.__traceback__)
    else:
        error_info["message"] = error
        error_info["exception_type"] = "StringError"
        error_info["traceback"] = traceback.format_stack()
    
    return error_info
```

#### 3. 自定义错误处理程序
```python
# 注册错误处理程序
def handle_database_error(error: Exception, **context):
    """处理数据库错误"""
    # 发送告警
    send_alert(f"数据库错误: {error}")
    # 记录到监控系统
    monitor.increment_counter("database_errors")

register_error_handler(ErrorType.DATABASE_ERROR, handle_database_error)

# 使用装饰器
@error_handler(ErrorType.NETWORK_ERROR)
def make_api_request():
    """API请求函数"""
    # 如果出现网络错误，会自动处理
    pass
```

### 便捷函数

```python
# 便捷的错误处理函数
handle_error("配置文件不存在", ErrorType.CONFIGURATION_ERROR, file_path="config.yaml")

# 错误处理装饰器
@error_handler(ErrorType.VALIDATION_ERROR)
def validate_user_input(data):
    """验证用户输入"""
    if not data:
        raise ValueError("输入数据不能为空")
    return True
```

## 指标收集器 (MetricsCollector)

### 功能描述

`MetricsCollector` 提供了日志相关的指标收集功能，支持计数器、仪表盘和直方图三种指标类型，便于监控系统运行状态。

### 指标类型

#### 1. 计数器 (Counter)
```python
# 增加计数器
metrics.increment_counter("api_requests")
metrics.increment_counter("api_requests", value=5)
metrics.increment_counter("api_requests", labels={"endpoint": "/api/users", "method": "GET"})
```

#### 2. 仪表盘 (Gauge)
```python
# 设置仪表盘值
metrics.set_gauge("memory_usage", 85.6)
metrics.set_gauge("cpu_usage", 45.2, labels={"host": "server1"})
```

#### 3. 直方图 (Histogram)
```python
# 观察直方图
metrics.observe_histogram("response_time", 0.123)
metrics.observe_histogram("response_time", 0.456, labels={"endpoint": "/api/users"})
```

### 核心功能

#### 1. 指标键生成
```python
def _create_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
    """创建指标键"""
    if not labels:
        return name
    
    # 将标签按字母顺序排序以确保一致性
    sorted_labels = sorted(labels.items())
    labels_str = ",".join([f"{k}={v}" for k, v in sorted_labels])
    return f"{name}{{{labels_str}}}"
```

#### 2. 线程安全
```python
# 使用锁确保线程安全
with self._lock:
    if key in self._counters:
        self._counters[key] += value
    else:
        self._counters[key] = value
```

#### 3. 指标获取
```python
# 获取所有指标
all_metrics = metrics.get_metrics()
print(all_metrics)
# {
#     "counters": {"api_requests": 100.0, "api_requests{endpoint=/api/users,method=GET}": 25.0},
#     "gauges": {"memory_usage": 85.6, "cpu_usage{host=server1}": 45.2},
#     "histograms": {"response_time": [0.123, 0.456, 0.789]},
#     "timestamp": "2023-01-01T12:00:00"
# }
```

#### 4. 指标重置
```python
# 重置所有指标
metrics.reset()
```

### 全局指标收集器

```python
# 获取全局指标收集器
metrics = get_global_metrics_collector()

# 在日志记录器中使用
class Logger:
    def _log(self, level: LogLevel, message: str, **kwargs: Any):
        # 记录日志
        # ...
        
        # 更新指标
        metrics = get_global_metrics_collector()
        metrics.increment_counter(f"log_messages_{level.name.lower()}")
```

## 结构化文件日志记录器 (StructuredFileLogger)

### 功能描述

`StructuredFileLogger` 提供了专门的结构化文件日志记录功能，直接输出JSON格式的日志，适用于日志分析系统。

### 主要功能

#### 1. 结构化日志记录
```python
# 创建结构化日志记录器
logger = StructuredFileLogger("logs/structured.json", LogLevel.INFO)

# 记录结构化日志
logger.info("用户登录", user_id=123, ip="192.168.1.1", user_agent="Mozilla/5.0...")
logger.error("支付失败", order_id="ORD123", amount=99.99, error_code="INSUFFICIENT_BALANCE")
```

#### 2. 自动脱敏
```python
# 使用自定义脱敏器
redactor = LogRedactor()
logger = StructuredFileLogger("logs/structured.json", LogLevel.INFO, redactor)

# 敏感信息会自动脱敏
logger.info("API调用", api_key="sk-abc123def456")
# 输出: {"api_key": "sk-***", ...}
```

#### 3. 线程安全
```python
def _write_record(self, record: Dict[str, Any]) -> None:
    """写入日志记录到文件"""
    json_str = json.dumps(record, ensure_ascii=False, default=str)
    
    with self._lock:
        with open(self.filename, "a", encoding=self.encoding) as f:
            f.write(json_str + "\n")
```

### 输出格式

```json
{
    "timestamp": "2023-01-01T12:00:00",
    "level": "INFO",
    "message": "用户登录",
    "thread_id": 12345,
    "process_id": 6789,
    "user_id": 123,
    "ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
}
```

## 组件集成

### 完整的日志服务示例

```python
# 创建日志记录器
logger = get_logger("MyApp", {
    "log_level": "INFO",
    "log_outputs": [
        {"type": "console", "use_color": True},
        {"type": "file", "filename": "logs/app.log"},
        {"type": "json", "filename": "logs/structured.json"}
    ]
})

# 设置脱敏器
redactor = LogRedactor(hash_sensitive=True)
logger.set_redactor(redactor)

# 记录日志
logger.info("应用启动", version="1.0.0", port=8080)

# 处理错误
try:
    # 一些操作
    pass
except Exception as e:
    handle_error(e, ErrorType.APPLICATION_ERROR, operation="startup")

# 收集指标
metrics = get_global_metrics_collector()
metrics.increment_counter("app_startups")
metrics.set_gauge("app_version", 1.0)
```

服务层组件提供了完整的日志服务解决方案，通过统一的接口和配置驱动的设计，使得日志系统既强大又易于使用。