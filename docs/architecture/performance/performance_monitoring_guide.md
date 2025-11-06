# 性能监控系统使用指南

## 概述

本指南介绍了如何在项目中使用新的统一性能监控系统。该系统提供了一套标准化的接口和实现，用于监控不同模块的性能指标。

## 架构设计

### 核心组件

1. **接口定义** (`interfaces.py`) - 定义了统一的性能监控接口
2. **抽象基类** (`base_monitor.py`) - 提供通用的性能监控实现
3. **具体实现** (`implementations/`) - 针对不同模块的具体监控器
4. **工厂类** (`factory.py`) - 用于创建和管理监控器实例
5. **依赖注入配置** (`di_config.py`) - 将监控器注册到DI容器

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

### 3. 获取和导出指标

```python
# 获取所有指标
metrics = checkpoint_monitor.get_all_metrics()

# 生成报告
report = checkpoint_monitor.generate_report()

# 重置指标
checkpoint_monitor.reset_metrics()
```

## 模块集成

### 检查点模块

检查点模块提供了两种使用方式：

#### 方式1：直接使用监控器

```python
from src.infrastructure.checkpoint import get_checkpoint_monitor

# 获取监控器实例
monitor = get_checkpoint_monitor()

# 直接记录操作
monitor.record_checkpoint_save(duration=0.5, size=1024, success=True)
monitor.record_checkpoint_load(duration=0.3, size=1024, success=True)
```

#### 方式2：使用装饰器

```python
from src.infrastructure.checkpoint import monitor_checkpoint_performance

# 使用装饰器监控函数
@monitor_checkpoint_performance("checkpoint_save")
def save_checkpoint(data):
    # 保存检查点的实现
    pass
```

### LLM模块

LLM模块可以直接使用LLM性能监控器：

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

性能监控系统支持通过YAML配置文件进行配置：

```yaml
# configs/monitoring.yaml
monitoring:
  max_history_size: 1000
  sampling_rate: 1.0
  enabled: true
  
  modules:
    checkpoint:
      enabled: true
      sampling_rate: 1.0
    llm:
      enabled: true
      sampling_rate: 1.0
```

## 扩展自定义监控器

要创建自定义监控器，只需继承`BasePerformanceMonitor`类：

```python
from src.infrastructure.monitoring.base_monitor import BasePerformanceMonitor

class CustomPerformanceMonitor(BasePerformanceMonitor):
    def __init__(self, max_history_size: int = 1000):
        super().__init__(max_history_size)
        
    def record_custom_metric(self, metric_name: str, value: float):
        """记录自定义指标"""
        self.set_gauge(f"custom.{metric_name}", value)
```

## 最佳实践

1. **合理采样** - 对于高频操作，使用适当的采样率以避免性能影响
2. **标签使用** - 使用标签来区分不同的操作维度
3. **定期清理** - 定期重置指标以避免内存泄漏
4. **异常处理** - 在监控代码中添加适当的异常处理
5. **直接使用监控器** - 避免不必要的抽象层，直接使用核心监控器类

## 架构说明

### 文件职责分离

- **`src/infrastructure/monitoring/implementations/checkpoint_monitor.py`** - 核心监控器实现，定义具体的监控逻辑
- **`src/infrastructure/checkpoint/utils.py`** - 便利工具，提供装饰器和工厂函数
- **`src/infrastructure/checkpoint/__init__.py`** - 模块导出，统一接口

这种设计避免了重复代码，同时保持了易用性。