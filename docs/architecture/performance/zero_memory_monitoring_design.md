# 零内存性能监控系统设计

## 概述

基于用户需求，重新设计性能监控系统，采用"零内存存储"策略，完全依赖日志和外部存储，不在内存中保存任何指标数据。

## 设计原则

1. **零内存存储** - 所有性能指标立即写入日志，不保存在内存中
2. **日志驱动** - 通过结构化日志记录性能指标
3. **外部存储** - 依赖日志系统和外部存储进行数据持久化
4. **API查询** - API通过读取日志或外部存储提供性能数据

## 架构设计

### 核心组件

1. **性能指标日志写入器** (`logger_writer.py`)
   - 负责将性能指标写入结构化日志
   - 支持JSON格式的日志输出
   - 异步写入，避免阻塞主流程

2. **轻量级监控器** (`lightweight_monitor.py`)
   - 替换当前的BasePerformanceMonitor
   - 不保存任何状态，直接调用日志写入器
   - 提供简单的接口用于记录指标

3. **日志配置** (`monitoring_logging.yaml`)
   - 专门用于性能监控的日志配置
   - 独立的日志文件和格式

### 数据流

```
应用代码 → 轻量级监控器 → 日志写入器 → 结构化日志 → 外部存储系统
                                                    ↓
API查询 ← 日志解析器 ← 日志文件 ← 日志轮转
```

## 实现计划

### 1. 创建日志写入器

```python
class PerformanceMetricsLogger:
    """性能指标日志写入器"""
    
    def __init__(self, logger_name: str = "performance_metrics"):
        self.logger = logging.getLogger(logger_name)
    
    def log_metric(self, metric_type: str, name: str, value: float, 
                   labels: Dict[str, str] = None, timestamp: float = None):
        """记录性能指标到日志"""
        
    def log_checkpoint_save(self, duration: float, size: int, success: bool):
        """记录检查点保存操作"""
        
    def log_llm_call(self, model: str, provider: str, response_time: float, 
                     tokens: Dict[str, int], success: bool):
        """记录LLM调用"""
```

### 2. 创建轻量级监控器

```python
class LightweightPerformanceMonitor:
    """轻量级性能监控器 - 零内存存储"""
    
    def __init__(self, logger: PerformanceMetricsLogger):
        self.logger = logger
    
    def record_checkpoint_save(self, duration: float, size: int, success: bool):
        """记录检查点保存 - 直接写入日志"""
        self.logger.log_checkpoint_save(duration, size, success)
    
    def record_llm_call(self, model: str, provider: str, response_time: float, 
                       prompt_tokens: int, completion_tokens: int, success: bool):
        """记录LLM调用 - 直接写入日志"""
        self.logger.log_llm_call(model, provider, response_time, 
                                {"prompt": prompt_tokens, "completion": completion_tokens}, 
                                success)
```

### 3. 更新具体实现

```python
class CheckpointPerformanceMonitor(LightweightPerformanceMonitor):
    """检查点性能监控器 - 零内存版本"""
    
    def record_checkpoint_save(self, duration: float, size: int, success: bool = True):
        """记录检查点保存操作"""
        self.logger.log_checkpoint_save(duration, size, success)
```

### 4. 日志格式设计

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "performance_metrics",
  "message": "checkpoint_save",
  "data": {
    "metric_type": "timer",
    "operation": "save",
    "duration": 0.5,
    "size": 1024,
    "success": true,
    "module": "checkpoint"
  }
}
```

### 5. API接口更新

```python
class PerformanceMetricsAPI:
    """性能指标API - 从日志读取数据"""
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
    
    def get_recent_metrics(self, time_range: str = "1h") -> List[Dict]:
        """从日志文件读取最近的性能指标"""
        
    def get_checkpoint_metrics(self, time_range: str = "1h") -> Dict:
        """获取检查点性能指标"""
```

## 优势

1. **内存效率** - 零内存存储，大大减少内存占用
2. **可扩展性** - 不受内存限制，可以处理大量指标
3. **持久性** - 数据立即写入日志，不会丢失
4. **简单性** - 架构更简单，减少状态管理
5. **可观测性** - 日志本身就是很好的可观测性工具

## 注意事项

1. **日志性能** - 需要确保日志写入不会成为性能瓶颈
2. **日志轮转** - 需要配置适当的日志轮转策略
3. **查询性能** - API查询可能需要优化，特别是大量日志文件时
4. **实时性** - 实时查询可能需要额外的缓存机制

## 实施步骤

1. 创建性能指标日志写入器
2. 创建轻量级监控器基类
3. 更新所有具体监控器实现
4. 配置专门的性能监控日志
5. 更新API接口从日志读取数据
6. 更新文档和配置
7. 测试和验证