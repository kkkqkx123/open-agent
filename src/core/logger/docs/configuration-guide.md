# 配置指南

## 概述

日志模块支持灵活的配置方式，包括YAML配置文件、环境变量和程序化配置。本指南详细介绍各种配置方法和最佳实践。

## 配置方式

### 1. YAML配置文件

#### 基本配置结构

```yaml
# configs/logging.yaml
log_level: INFO
log_outputs:
  - type: console
    level: INFO
    use_color: true
  - type: file
    level: DEBUG
    filename: logs/app.log
    mode: a
    encoding: utf-8
  - type: json
    level: WARNING
    filename: logs/errors.json
    ensure_ascii: false
```

#### 完整配置示例

```yaml
# configs/logging.yaml
# 全局日志级别
log_level: INFO

# 日志输出配置
log_outputs:
  # 控制台输出
  - type: console
    level: INFO
    use_color: true
    stream: stdout  # stdout 或 stderr
    
  # 应用日志文件
  - type: file
    level: DEBUG
    filename: logs/app.log
    mode: a
    encoding: utf-8
    
  # 错误日志文件
  - type: file
    level: ERROR
    filename: logs/error.log
    mode: a
    encoding: utf-8
    
  # 结构化JSON日志
  - type: json
    level: INFO
    filename: logs/structured.json
    ensure_ascii: false
    
  # 审计日志
  - type: json
    level: INFO
    filename: logs/audit.json
    ensure_ascii: false

# 脱敏配置
redaction:
  enabled: true
  hash_sensitive: false
  patterns:
    - pattern: '\b\d{4}-\d{4}-\d{4}-\d{4}\b'
      replacement: '****-****-****-****'
    - pattern: '(["\']?secret["\']?\s*[:=]\s*["\']?)[^"\',\s}]+'
      replacement: '\1***SECRET***'

# 错误处理配置
error_handling:
  enabled: true
  types:
    application_error:
      enabled: true
      log_level: ERROR
    database_error:
      enabled: true
      log_level: CRITICAL
      alert: true
    security_error:
      enabled: true
      log_level: CRITICAL
      alert: true
      notify: true

# 指标收集配置
metrics:
  enabled: true
  collection_interval: 60  # 秒
  metrics:
    - name: log_messages_total
      type: counter
      labels: [level, logger]
    - name: log_message_size
      type: histogram
      buckets: [100, 500, 1000, 5000]
```

### 2. 环境变量配置

#### 基本环境变量

```bash
# 日志级别
LOG_LEVEL=INFO

# 控制台日志配置
CONSOLE_LOG_LEVEL=INFO
CONSOLE_LOG_COLOR=true

# 文件日志配置
FILE_LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
LOG_FILE_ENCODING=utf-8

# JSON日志配置
JSON_LOG_LEVEL=WARNING
JSON_LOG_FILE=logs/errors.json
JSON_LOG_ENSURE_ASCII=false

# 脱敏配置
REDACTION_ENABLED=true
REDACTION_HASH_SENSITIVE=false

# 错误处理配置
ERROR_HANDLING_ENABLED=true
DATABASE_ERROR_ALERT=true

# 指标配置
METRICS_ENABLED=true
METRICS_COLLECTION_INTERVAL=60
```

#### 环境变量配置示例

```python
import os
from src.services.logger import set_global_config

def load_config_from_env():
    """从环境变量加载配置"""
    config = {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_outputs": []
    }
    
    # 控制台输出配置
    if os.getenv("CONSOLE_LOG_ENABLED", "true").lower() == "true":
        console_config = {
            "type": "console",
            "level": os.getenv("CONSOLE_LOG_LEVEL", "INFO"),
            "use_color": os.getenv("CONSOLE_LOG_COLOR", "false").lower() == "true"
        }
        config["log_outputs"].append(console_config)
    
    # 文件输出配置
    if os.getenv("FILE_LOG_ENABLED", "true").lower() == "true":
        file_config = {
            "type": "file",
            "level": os.getenv("FILE_LOG_LEVEL", "DEBUG"),
            "filename": os.getenv("LOG_FILE", "logs/app.log"),
            "encoding": os.getenv("LOG_FILE_ENCODING", "utf-8")
        }
        config["log_outputs"].append(file_config)
    
    # JSON输出配置
    if os.getenv("JSON_LOG_ENABLED", "false").lower() == "true":
        json_config = {
            "type": "json",
            "level": os.getenv("JSON_LOG_LEVEL", "INFO"),
            "filename": os.getenv("JSON_LOG_FILE", "logs/structured.json"),
            "ensure_ascii": os.getenv("JSON_LOG_ENSURE_ASCII", "false").lower() == "true"
        }
        config["log_outputs"].append(json_config)
    
    # 脱敏配置
    if os.getenv("REDACTION_ENABLED", "true").lower() == "true":
        config["redaction"] = {
            "enabled": True,
            "hash_sensitive": os.getenv("REDACTION_HASH_SENSITIVE", "false").lower() == "true"
        }
    
    return config

# 设置全局配置
config = load_config_from_env()
set_global_config(config)
```

### 3. 程序化配置

#### 基本程序化配置

```python
from src.services.logger import get_logger, LogLevel
from src.core.logger.handlers import ConsoleHandler, FileHandler, JsonHandler
from src.core.logger.formatters import ColorFormatter, TextFormatter, JsonFormatter

def create_logger_config():
    """创建日志配置"""
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
                "filename": "logs/app.log"
            },
            {
                "type": "json",
                "level": "WARNING",
                "filename": "logs/errors.json"
            }
        ]
    }
    return config

# 使用配置创建日志记录器
config = create_logger_config()
logger = get_logger("MyApp", config)
```

#### 高级程序化配置

```python
from src.services.logger import Logger, LogLevel, LogRedactor
from src.core.logger.handlers import ConsoleHandler, FileHandler
from src.core.logger.formatters import ColorFormatter, JsonFormatter

def create_advanced_logger():
    """创建高级日志记录器"""
    # 创建日志记录器
    logger = Logger("AdvancedApp")
    
    # 创建控制台处理器
    console_handler = ConsoleHandler(
        level=LogLevel.INFO,
        config={"use_color": True}
    )
    console_handler.set_formatter(ColorFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    # 创建文件处理器
    file_handler = FileHandler(
        level=LogLevel.DEBUG,
        config={"filename": "logs/app.log"}
    )
    file_handler.set_formatter(TextFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(user_id)s"
    ))
    
    # 创建JSON处理器
    json_handler = JsonHandler(
        level=LogLevel.WARNING,
        config={"filename": "logs/errors.json"}
    )
    
    # 添加处理器
    logger.add_handler(console_handler)
    logger.add_handler(file_handler)
    logger.add_handler(json_handler)
    
    # 设置脱敏器
    redactor = LogRedactor(hash_sensitive=True)
    redactor.add_pattern(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b', '****-****-****-****')
    logger.set_redactor(redactor)
    
    return logger

# 使用高级日志记录器
logger = create_advanced_logger()
```

## 配置详解

### 1. 日志级别配置

#### 级别优先级

```
DEBUG (10) < INFO (20) < WARNING (30) < ERROR (40) < CRITICAL (50)
```

#### 配置示例

```yaml
# 全局级别
log_level: INFO

# 处理器级别（可以覆盖全局级别）
log_outputs:
  - type: console
    level: DEBUG  # 控制台显示DEBUG及以上级别
  - type: file
    level: INFO   # 文件记录INFO及以上级别
  - type: json
    level: ERROR  # JSON文件只记录ERROR及以上级别
```

### 2. 处理器配置

#### 控制台处理器 (ConsoleHandler)

```yaml
- type: console
  level: INFO
  use_color: true        # 是否使用彩色输出
  stream: stdout         # 输出流: stdout 或 stderr
```

#### 文件处理器 (FileHandler)

```yaml
- type: file
  level: DEBUG
  filename: logs/app.log    # 文件路径
  mode: a                   # 文件模式: a(追加), w(覆盖)
  encoding: utf-8           # 文件编码
  max_size: 10485760        # 最大文件大小(字节)
  backup_count: 5           # 备份文件数量
```

#### JSON处理器 (JsonHandler)

```yaml
- type: json
  level: WARNING
  filename: logs/errors.json
  ensure_ascii: false       # 是否确保ASCII编码
  indent: 2                 # JSON缩进(可选)
  sort_keys: true           # 是否排序键名(可选)
```

### 3. 格式化器配置

#### 文本格式化器

```yaml
formatters:
  text:
    fmt: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
  
  detailed:
    fmt: "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
```

#### JSON格式化器

```yaml
formatters:
  json:
    datefmt: "%Y-%m-%d %H:%M:%S"
    ensure_ascii: false
    include_extra: true      # 是否包含额外字段
```

#### 彩色格式化器

```yaml
formatters:
  color:
    fmt: "%(asctime)s - %(levelname)s - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
    colors:                  # 自定义颜色
      DEBUG: "\033[36m"      # 青色
      INFO: "\033[32m"       # 绿色
      WARNING: "\033[33m"    # 黄色
      ERROR: "\033[31m"      # 红色
      CRITICAL: "\033[35m"   # 紫色
```

### 4. 脱敏配置

#### 基本脱敏配置

```yaml
redaction:
  enabled: true
  hash_sensitive: false      # 是否使用哈希脱敏
  debug_level_exemption: true  # DEBUG级别是否豁免脱敏
```

#### 自定义脱敏模式

```yaml
redaction:
  patterns:
    # 信用卡号
    - pattern: '\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
      replacement: '****-****-****-****'
    
    # 社会安全号码
    - pattern: '\b\d{3}-\d{2}-\d{4}\b'
      replacement: '***-**-****'
    
    # 自定义密钥
    - pattern: '(["\']?custom_key["\']?\s*[:=]\s*["\']?)[^"\',\s}]+'
      replacement: '\1***CUSTOM***'
```

### 5. 错误处理配置

```yaml
error_handling:
  enabled: true
  
  # 全局错误处理配置
  global:
    log_level: ERROR
    include_traceback: true
    max_traceback_lines: 20
  
  # 特定错误类型配置
  types:
    application_error:
      enabled: true
      log_level: ERROR
      alert: false
    
    database_error:
      enabled: true
      log_level: CRITICAL
      alert: true
      retry_count: 3
    
    security_error:
      enabled: true
      log_level: CRITICAL
      alert: true
      notify: true
      block_ip: true
    
    network_error:
      enabled: true
      log_level: WARNING
      alert: false
      retry_count: 2
```

### 6. 指标收集配置

```yaml
metrics:
  enabled: true
  collection_interval: 60    # 收集间隔(秒)
  
  # 指标定义
  metrics:
    - name: log_messages_total
      type: counter
      description: "Total number of log messages"
      labels: [level, logger]
    
    - name: log_message_size_bytes
      type: histogram
      description: "Size of log messages in bytes"
      buckets: [100, 500, 1000, 5000, 10000]
      labels: [level]
    
    - name: log_errors_total
      type: counter
      description: "Total number of error logs"
      labels: [logger, error_type]
  
  # 输出配置
  output:
    type: prometheus
    port: 9090
    path: /metrics
```

## 环境特定配置

### 1. 开发环境

```yaml
# configs/logging-dev.yaml
log_level: DEBUG
log_outputs:
  - type: console
    level: DEBUG
    use_color: true
  - type: file
    level: DEBUG
    filename: logs/dev.log

redaction:
  enabled: false  # 开发环境不脱敏，便于调试

error_handling:
  enabled: true
  global:
    log_level: DEBUG

metrics:
  enabled: false  # 开发环境不收集指标
```

### 2. 测试环境

```yaml
# configs/logging-test.yaml
log_level: INFO
log_outputs:
  - type: console
    level: INFO
    use_color: false
  - type: file
    level: DEBUG
    filename: logs/test.log
  - type: json
    level: INFO
    filename: logs/test.json

redaction:
  enabled: true
  hash_sensitive: false

error_handling:
  enabled: true

metrics:
  enabled: true
  collection_interval: 30
```

### 3. 生产环境

```yaml
# configs/logging-prod.yaml
log_level: WARNING
log_outputs:
  - type: file
    level: INFO
    filename: logs/app.log
    max_size: 104857600    # 100MB
    backup_count: 10
  - type: json
    level: ERROR
    filename: logs/errors.json
    ensure_ascii: false

redaction:
  enabled: true
  hash_sensitive: true

error_handling:
  enabled: true
  global:
    log_level: ERROR
  types:
    database_error:
      alert: true
    security_error:
      alert: true
      notify: true

metrics:
  enabled: true
  collection_interval: 60
  output:
    type: prometheus
    port: 9090
```

## 配置加载

### 1. 配置文件加载

```python
import yaml
from pathlib import Path
from src.services.logger import set_global_config

def load_config_from_file(config_path: str):
    """从YAML文件加载配置"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config

# 加载配置
config = load_config_from_file("configs/logging.yaml")
set_global_config(config)
```

### 2. 环境感知配置加载

```python
import os
from src.services.logger import set_global_config

def load_environment_config():
    """根据环境加载配置"""
    env = os.getenv("ENVIRONMENT", "development")
    
    config_files = {
        "development": "configs/logging-dev.yaml",
        "testing": "configs/logging-test.yaml",
        "production": "configs/logging-prod.yaml"
    }
    
    config_file = config_files.get(env, "configs/logging.yaml")
    config = load_config_from_file(config_file)
    
    # 应用环境变量覆盖
    apply_env_overrides(config)
    
    return config

def apply_env_overrides(config):
    """应用环境变量覆盖"""
    # 日志级别覆盖
    if "LOG_LEVEL" in os.environ:
        config["log_level"] = os.environ["LOG_LEVEL"]
    
    # 其他环境变量覆盖...
    
    return config

# 加载环境特定配置
config = load_environment_config()
set_global_config(config)
```

### 3. 配置验证

```python
from typing import Dict, Any
from src.core.logger.log_level import LogLevel

def validate_config(config: Dict[str, Any]) -> bool:
    """验证配置"""
    # 验证日志级别
    if "log_level" in config:
        try:
            LogLevel.from_string(config["log_level"])
        except ValueError:
            raise ValueError(f"无效的日志级别: {config['log_level']}")
    
    # 验证输出配置
    if "log_outputs" in config:
        for output in config["log_outputs"]:
            if "type" not in output:
                raise ValueError("输出配置必须包含type字段")
            
            output_type = output["type"]
            if output_type not in ["console", "file", "json"]:
                raise ValueError(f"不支持的输出类型: {output_type}")
            
            if output_type in ["file", "json"] and "filename" not in output:
                raise ValueError(f"{output_type}输出必须指定filename")
    
    return True

# 使用验证
config = load_config_from_file("configs/logging.yaml")
if validate_config(config):
    set_global_config(config)
```

## 配置最佳实践

### 1. 配置分离

```yaml
# 基础配置
base.yaml:
  log_level: INFO
  redaction:
    enabled: true

# 环境特定配置
dev.yaml:
  log_level: DEBUG
  log_outputs:
    - type: console
      use_color: true

prod.yaml:
  log_level: WARNING
  log_outputs:
    - type: file
      filename: logs/app.log
```

### 2. 配置继承

```python
def merge_configs(base_config: Dict, override_config: Dict) -> Dict:
    """合并配置"""
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged

# 使用配置继承
base_config = load_config_from_file("configs/base.yaml")
env_config = load_config_from_file("configs/dev.yaml")
final_config = merge_configs(base_config, env_config)
```

### 3. 配置热重载

```python
import os
import time
from pathlib import Path
from src.services.logger import set_global_config

class ConfigWatcher:
    """配置文件监视器"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.last_modified = 0
    
    def watch(self, interval: int = 60):
        """监视配置文件变化"""
        while True:
            try:
                current_modified = self.config_path.stat().st_mtime
                if current_modified > self.last_modified:
                    print("配置文件已更新，重新加载...")
                    config = load_config_from_file(str(self.config_path))
                    set_global_config(config)
                    self.last_modified = current_modified
            except Exception as e:
                print(f"重新加载配置失败: {e}")
            
            time.sleep(interval)

# 启动配置监视
watcher = ConfigWatcher("configs/logging.yaml")
# 在单独的线程中运行监视器
import threading
threading.Thread(target=watcher.watch, daemon=True).start()
```

通过合理配置日志系统，可以满足不同环境和场景的需求，提供灵活、高效的日志服务。