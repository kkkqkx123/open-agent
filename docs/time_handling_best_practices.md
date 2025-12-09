# Python时间处理最佳实践指南

## 概述

本文档为Modular Agent Framework项目提供Python时间处理的最佳实践指导，帮助开发者在不同场景下正确选择和使用datetime与time模块。

## 核心原则

### 1. datetime模块适用场景
- **业务时间处理**：需要完整日期时间信息的场景
- **时区感知操作**：跨时区的时间计算和显示
- **日期时间格式化**：需要人类可读的时间格式
- **时间间隔计算**：使用timedelta进行精确的时间运算

### 2. time模块适用场景
- **性能监控**：代码执行时间测量
- **简单时间戳**：Unix时间戳格式的轻量级操作
- **延迟等待**：使用time.sleep()进行精确延迟
- **缓存过期检查**：轻量级的时间戳比较

## 具体使用指南

### datetime使用示例

#### 业务时间戳存储
```python
from datetime import datetime, timezone

# 创建时区感知的时间戳
timestamp = datetime.now(timezone.utc)

# 存储到数据库或返回给客户端
return timestamp.isoformat()
```

#### 时间间隔计算
```python
from datetime import datetime, timedelta

# 计算时间差
start_time = datetime.now()
# ... 执行操作 ...
end_time = datetime.now()
duration = end_time - start_time

# 添加时间间隔
new_time = start_time + timedelta(hours=2)
```

### time使用示例

#### 性能监控
```python
import time

# 精确的性能计时
start_time = time.perf_counter()
# ... 执行性能关键代码 ...
end_time = time.perf_counter()
execution_time = end_time - start_time
```

#### 缓存过期检查
```python
import time

class CacheItem:
    def __init__(self, value, ttl_seconds):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl_seconds
    
    def is_expired(self):
        return time.time() - self.created_at > self.ttl
```

## 常见场景指导

### 场景1：工作流执行时间戳
**推荐使用datetime**
```python
from datetime import datetime

class WorkflowExecution:
    def __init__(self):
        self.started_at = datetime.now()
        self.completed_at = None
    
    def complete(self):
        self.completed_at = datetime.now()
        return self.completed_at - self.started_at
```

### 场景2：性能监控
**推荐使用time**
```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.perf_counter()
    
    def get_elapsed_time(self):
        return time.perf_counter() - self.start_time
```

### 场景3：缓存系统
**推荐使用time**
```python
import time

class CacheManager:
    def __init__(self):
        self._cache = {}
    
    def set(self, key, value, ttl_seconds):
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }
    
    def get(self, key):
        item = self._cache.get(key)
        if item and time.time() < item['expires_at']:
            return item['value']
        return None
```

### 场景4：时区处理
**必须使用datetime**
```python
from datetime import datetime, timezone
import pytz

# 创建时区感知的时间
utc_time = datetime.now(timezone.utc)
local_time = utc_time.astimezone()

# 转换到特定时区
tokyo_tz = pytz.timezone('Asia/Tokyo')
tokyo_time = utc_time.astimezone(tokyo_tz)
```

## 最佳实践总结

### 选择标准
| 场景 | 推荐模块 | 理由 |
|------|----------|------|
| 业务时间记录 | datetime | 提供完整的日期时间信息 |
| 性能计时 | time | 精度更高，开销更小 |
| 缓存过期 | time | 轻量级操作，性能更好 |
| 时区处理 | datetime | 内置时区支持 |
| 延迟等待 | time | time.sleep()更精确 |

### 避免的常见错误
1. **不要混用**：避免在同一功能中混用datetime和time的时间戳
2. **时区一致性**：确保所有时间戳使用相同的时区标准（推荐UTC）
3. **精度选择**：根据需求选择合适的精度（秒、毫秒、微秒）

### 代码质量检查
在代码审查时检查：
- 业务逻辑是否使用datetime
- 性能监控是否使用time.perf_counter()
- 缓存系统是否使用time.time()
- 时区处理是否正确使用timezone

## 相关工具和库

### 标准库
- `datetime`：日期时间处理
- `time`：时间相关操作
- `calendar`：日历相关功能

### 第三方库
- `pytz`：时区处理（Python 3.9+推荐使用zoneinfo）
- `dateutil`：扩展的日期时间功能
- `arrow`：更友好的日期时间API

## 版本兼容性

- Python 3.8+：推荐使用datetime.timestamp()方法
- Python 3.9+：推荐使用zoneinfo替代pytz
- Python 3.11+：time.perf_counter()精度更高

## 参考资料

- [Python datetime文档](https://docs.python.org/3/library/datetime.html)
- [Python time文档](https://docs.python.org/3/library/time.html)
- [PEP 615 - zoneinfo模块](https://peps.python.org/pep-0615/)

---

*本文档最后更新：2024年*  
*维护者：架构团队*