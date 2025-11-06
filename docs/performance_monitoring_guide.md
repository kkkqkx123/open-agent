# 性能监控系统使用指南

## 概述

本指南介绍了如何在项目中使用新的统一性能监控系统。该系统提供了一套标准化的接口和实现，用于监控不同模块的性能指标，采用零内存存储架构。

## 架构设计

### 核心组件

1. **接口定义** (`interfaces.py`) - 定义了统一的性能监控接口
2. **抽象基类** (`base_monitor.py`) - 提供通用的性能监控实现
3. **具体实现** (`implementations/`) - 针对不同模块的具体监控器
4. **工厂类** (`factory.py`) - 用于创建和管理监控器实例
5. **日志写入器** (`logger_writer.py`) - 将性能指标写入结构化日志
6. **日志清理器** (`log_cleaner.py`) - 基于时间戳的日志文件清理
7. **调度器** (`scheduler.py`) - 定期执行日志清理的调度机制
8. **依赖注入配置** (`di_config.py`) - 将监控器注册到DI容器

## 零内存存储架构

### 设计原则

- **零内存存储** - 所有性能指标立即写入日志，不保存在内存中
- **日志驱动** - 通过结构化日志记录性能指标
- **外部存储** - 依赖日志系统和外部存储进行数据持久化
- **自动清理** - 定期清理过期的日志文件

### 数据流

```
应用代码 → 轻量级监控器 → 日志写入器 → 结构化日志 → 外部存储系统
                                                    ↓
API查询 ← 日志解析器 ← 日志文件 ← 日志轮转 ← 定期清理器
```

## 使用方法

### 1. 获取监控器实例

```python
from src.infrastructure.monitoring import PerformanceMonitorFactory

# 获取工厂实例
factory = PerformanceMonitorFactory.get_instance()

# 创建特定类型的监控器
checkpoint_monitor = factory.create_monitor("checkpoint")
llm_monitor = factory.create_monitor("llm")
```

### 2. 记录性能指标

```python
# 记录检查点保存操作
checkpoint_monitor.record_checkpoint_save(duration=0.5, size=1024, success=True)

# 记录LLM调用
llm_monitor.record_llm_call(
    model="gpt-4",
    provider="openai",
    response_time=2.1,
    prompt_tokens=100,
    completion_tokens=200,
    total_tokens=300,
    success=True
)
```

### 3. 日志清理

#### 手动清理

```python
from src.infrastructure.monitoring import PerformanceMonitorFactory

factory = PerformanceMonitorFactory.get_instance()

# 强制执行日志清理
result = factory.force_log_cleanup()
print(f"清理结果: {result}")
```

#### 定期清理

```python
from src.infrastructure.monitoring import LogCleanupService

# 获取日志清理服务
factory = PerformanceMonitorFactory.get_instance()
cleanup_service = factory.get_scheduled_cleaner()

# 配置清理参数
cleanup_config = {
    "retention_days": 30,
    "log_patterns": ["logs/*.log", "logs/*.log.*"],
    "enabled": True,
    "dry_run": False
}

# 设置日志清理器
log_cleaner = factory.setup_log_cleaner(cleanup_config)

# 执行清理
result = log_cleaner.cleanup_logs()
```

## 模块集成

### 检查点模块

```python
from src.infrastructure.checkpoint import get_checkpoint_monitor

# 获取监控器实例
monitor = get_checkpoint_monitor()

# 直接记录操作
monitor.record_checkpoint_save(duration=0.5, size=1024, success=True)
monitor.record_checkpoint_load(duration=0.3, size=1024, success=True)
```

### LLM模块

```python
from src.infrastructure.monitoring import PerformanceMonitorFactory

factory = PerformanceMonitorFactory.get_instance()
llm_monitor = factory.create_monitor("llm")

# 记录LLM调用
llm_monitor.record_llm_call(
    model="gpt-4",
    provider="openai",
    response_time=2.1,
    prompt_tokens=100,
    completion_tokens=200,
    total_tokens=300,
    success=True
)
```

## 配置管理

### 日志配置 (`configs/monitoring_logging.yaml`)

```yaml
# 日志清理配置
log_cleanup:
  # 是否启用日志清理
  enabled: true
  
  # 日志保留天数
  retention_days: 30
  
  # 要清理的日志文件模式
  log_patterns:
    - "logs/*.log"
    - "logs/*.log.*"
    - "logs/*_metrics.log"
    - "logs/*_metrics.log.*"
  
  # 是否为试运行模式（不实际删除文件）
  dry_run: false
  
  # 清理检查间隔（小时）
  check_interval_hours: 24
```

### 日志格式

性能指标以JSON格式写入日志：

```json
{
  "timestamp": 1704110400.0,
  "metric_type": "timer",
  "operation": "checkpoint_save",
  "duration": 0.5,
  "size": 1024,
  "success": true,
  "module": "checkpoint"
}
```

## 日志清理功能

### 自动清理

系统提供自动日志清理功能：

1. **定期检查** - 默认每天检查一次
2. **基于时间戳** - 根据文件修改时间判断是否过期
3. **配置驱动** - 通过配置文件控制清理行为
4. **零内存架构** - 清理过程不保存已删除文件的记录

### 清理配置选项

- `retention_days`: 日志保留天数（默认30天）
- `log_patterns`: 要清理的日志文件模式
- `enabled`: 是否启用清理功能
- `dry_run`: 试运行模式（不实际删除文件）

### 清理统计

清理过程会记录以下统计信息：

- 删除的文件数量
- 释放的磁盘空间
- 遇到的错误数量
- 清理耗时

## 扩展自定义监控器

要创建自定义监控器，只需继承`LightweightPerformanceMonitor`类：

```python
from src.infrastructure.monitoring.lightweight_monitor import LightweightPerformanceMonitor

class CustomPerformanceMonitor(LightweightPerformanceMonitor):
    def __init__(self, logger=None):
        super().__init__(logger)
        
    def record_custom_metric(self, metric_name: str, value: float):
        """记录自定义指标"""
        self.logger.log_timer(f"custom.{metric_name}", value)
```

## 最佳实践

1. **合理配置保留期** - 根据磁盘空间和合规要求设置合适的保留天数
2. **监控清理过程** - 定期检查清理日志，确保系统正常运行
3. **试运行模式** - 在生产环境使用前先用试运行模式测试
4. **日志轮转** - 配置适当的日志轮转策略，避免单个文件过大
5. **异常处理** - 在监控代码中添加适当的异常处理

## 架构说明

### 文件职责分离

- **`logger_writer.py`** - 核心日志写入器，负责将指标写入结构化日志
- **`lightweight_monitor.py`** - 轻量级监控器基类，零内存存储
- **`log_cleaner.py`** - 日志清理器，基于时间戳删除过期文件
- **`scheduler.py`** - 调度器，提供定期检查机制
- **具体监控器实现** - 针对不同模块的专用监控器

这种设计实现了完全的零内存存储，同时保持了易用性和可扩展性。