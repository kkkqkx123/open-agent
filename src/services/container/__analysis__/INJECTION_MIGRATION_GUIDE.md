# 依赖注入便利层迁移指南

## 概述

本指南帮助开发者从现有的 `get_global_*()` 模式迁移到新的通用依赖注入便利层框架。

## 迁移优势

### 性能提升
- **缓存机制**：避免重复的容器查找操作
- **直接访问**：全局实例访问比容器解析更快
- **减少开销**：避免依赖注入的运行时开销

### 开发便利性
- **简洁API**：更简洁的服务获取方式
- **多种模式**：支持装饰器、属性、自动注入等多种模式
- **类型安全**：完整的类型注解支持

### 系统稳定性
- **多级降级**：全局实例 → 容器查找 → fallback实现
- **错误处理**：统一的异常处理机制
- **测试友好**：内置测试隔离支持

## 迁移步骤

### 步骤1：识别现有的全局服务获取模式

搜索项目中的以下模式：

```python
# 旧模式
from src.services.container import get_global_container
container = get_global_container()
service = container.get(IServiceType)

# 或者直接的全局函数
service = get_global_service()
```

### 步骤2：选择合适的迁移模式

#### 模式A：装饰器模式（推荐）

**适用场景**：需要简洁API的服务获取

**旧代码：**
```python
from src.services.container import get_global_container

def get_logger():
    container = get_global_container()
    return container.get(ILogger)

def process_data():
    logger = get_logger()
    logger.info("处理数据")
```

**新代码：**
```python
from src.services.container.injection_decorators import injectable

@injectable(ILogger)
def get_logger():
    """获取日志记录器"""
    pass

def process_data():
    logger = get_logger()
    logger.info("处理数据")
```

#### 模式B：服务访问器模式

**适用场景**：类中需要频繁使用多个服务

**旧代码：**
```python
class MyService:
    def __init__(self):
        from src.services.container import get_global_container
        self.container = get_global_container()
    
    def process_data(self):
        logger = self.container.get(ILogger)
        llm = self.container.get(ILLMManager)
        # 使用服务...
```

**新代码：**
```python
from src.services.container.injection_decorators import service_accessor

@service_accessor(ILogger)
@service_accessor(ILLMManager)
class MyService:
    def process_data(self):
        logger = self.get_ilogger()
        llm = self.get_illmmanager()
        # 使用服务...
```

#### 模式C：自动注入模式

**适用场景**：函数参数中需要多个服务

**旧代码：**
```python
def process_data(data):
    from src.services.container import get_global_container
    container = get_global_container()
    logger = container.get(ILogger)
    llm = container.get(ILLMManager)
    
    logger.info(f"处理: {data}")
    return llm.process(data)
```

**新代码：**
```python
from src.services.container.injection_decorators import auto_inject

@auto_inject(ILogger, ILLMManager)
def process_data(data, logger, llm_manager):
    logger.info(f"处理: {data}")
    return llm_manager.process(data)
```

#### 模式D：注入属性模式

**适用场景**：类属性形式的服务访问

**旧代码：**
```python
class MyService:
    def __init__(self):
        from src.services.container import get_global_container
        self._container = get_global_container()
    
    @property
    def logger(self):
        return self._container.get(ILogger)
    
    def process_data(self):
        self.logger.info("处理数据")
```

**新代码：**
```python
from src.services.container.injection_decorators import inject_property

class MyService:
    logger = inject_property(ILogger)
    
    def process_data(self):
        self.logger.info("处理数据")
```

### 步骤3：更新服务绑定

确保服务绑定类继承 `BaseServiceBindings` 并设置注入层：

```python
from src.services.container.base_service_bindings import BaseServiceBindings

class MyServiceBindings(BaseServiceBindings):
    def _do_register_services(self, container, config, environment):
        # 注册服务到容器
        container.register_factory(IMyService, my_service_factory)
    
    def _post_register(self, container, config, environment):
        # 设置注入层
        self.setup_service_injection(container, IMyService)
```

### 步骤4：处理测试代码

更新测试代码以使用新的注入层：

```python
def test_my_service():
    from src.services.container.injection_base import get_global_injection_registry
    from unittest.mock import Mock
    
    # 获取注入注册表
    registry = get_global_injection_registry()
    
    # 设置测试用的mock
    mock_service = Mock(spec=IMyService)
    service_injection = registry.get_injection(IMyService)
    service_injection.set_instance(mock_service)
    
    try:
        # 执行测试
        result = my_function_that_uses_service()
        # 验证结果...
    finally:
        # 清理测试状态
        service_injection.clear_instance()
```

## 具体迁移示例

### 示例1：日志服务迁移

**旧代码：**
```python
# src/services/logger/injection.py (旧版本)
_logger_instance = None

def get_logger(module_name=None):
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance
    
    try:
        from src.services.container import get_global_container
        container = get_global_container()
        if container.has_service(ILogger):
            logger = container.get(ILogger)
            _logger_instance = logger
            return logger
    except Exception:
        pass
    
    return _StubLogger()
```

**新代码：**
```python
# src/services/logger/injection.py (新版本)
from src.services.container.injection_base import get_global_injection_registry
from src.services.container.injection_decorators import injectable

# 注册注入
_logger_injection = get_global_injection_registry().register(ILogger, _create_fallback_logger)

@injectable(ILogger, _create_fallback_logger)
def get_logger(module_name=None):
    """获取日志记录器实例"""
    return _logger_injection.get_instance()
```

### 示例2：LLM服务迁移

**旧代码：**
```python
# src/services/llm/manager.py
def get_global_llm_manager():
    if not hasattr(_global_llm_manager, '_instance'):
        from src.services.container import get_global_container
        container = get_global_container()
        _global_llm_manager._instance = container.get(ILLMManager)
    return _global_llm_manager._instance
```

**新代码：**
```python
# src/services/llm/injection.py
from src.services.container.injection_decorators import injectable

@injectable(ILLMManager)
def get_llm_manager():
    """获取LLM管理器实例"""
    pass
```

### 示例3：配置服务迁移

**旧代码：**
```python
# src/services/config/config.py
_global_config_manager = None

def get_global_config_manager():
    global _global_config_manager
    if _global_config_manager is None:
        from src.services.container import get_global_container
        container = get_global_container()
        _global_config_manager = container.get(IConfigManager)
    return _global_config_manager
```

**新代码：**
```python
# src/services/config/injection.py
from src.services.container.injection_decorators import injectable

@injectable(IConfigManager)
def get_config_manager():
    """获取配置管理器实例"""
    pass
```

## 批量迁移脚本

创建一个迁移脚本来帮助批量更新：

```python
# migration_script.py
import re
import os
from pathlib import Path

def migrate_global_getters(file_path):
    """迁移文件中的全局getter模式"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换常见的全局getter模式
    patterns = [
        (r'get_global_container\(\)\.get\(([^)]+)\)', r'get_\1()'),
        (r'from src\.services\.container import get_global_container', ''),
        (r'container = get_global_container\(\)', ''),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # 清理多余的空行
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def migrate_directory(directory):
    """迁移目录中的所有Python文件"""
    for py_file in Path(directory).rglob('*.py'):
        migrate_global_getters(py_file)

if __name__ == '__main__':
    migrate_directory('src')
```

## 验证迁移结果

### 1. 功能验证

确保迁移后的代码功能正常：

```python
def test_migration():
    """验证迁移结果"""
    # 测试服务获取
    logger = get_logger()
    assert logger is not None
    
    # 测试注入状态
    from src.services.container.injection_base import get_injection_status
    status = get_injection_status()
    assert 'ILogger' in status
    
    print("迁移验证通过")
```

### 2. 性能验证

比较迁移前后的性能：

```python
import time

def benchmark_old_way():
    """旧方式性能测试"""
    start = time.time()
    for _ in range(1000):
        from src.services.container import get_global_container
        container = get_global_container()
        logger = container.get(ILogger)
    return time.time() - start

def benchmark_new_way():
    """新方式性能测试"""
    start = time.time()
    for _ in range(1000):
        logger = get_logger()
    return time.time() - start

old_time = benchmark_old_way()
new_time = benchmark_new_way()
print(f"性能提升: {old_time / new_time:.2f}x")
```

## 常见问题和解决方案

### Q1: 迁移后出现循环依赖怎么办？

**A:** 使用延迟依赖解析：

```python
from src.services.container.injection_decorators import injectable

@injectable(IServiceA)
def get_service_a():
    """获取服务A"""
    pass

@injectable(IServiceB)
def get_service_b():
    """获取服务B"""
    pass
```

### Q2: 如何处理可选服务？

**A:** 使用fallback工厂：

```python
def create_optional_service():
    try:
        from src.services.container import get_global_container
        container = get_global_container()
        return container.get(IOptionalService)
    except:
        return None

@injectable(IOptionalService, create_optional_service)
def get_optional_service():
    """获取可选服务"""
    pass
```

### Q3: 测试时如何隔离服务？

**A:** 使用测试隔离功能：

```python
def test_with_isolation():
    from src.services.container.injection_base import get_global_injection_registry
    
    registry = get_global_injection_registry()
    
    # 创建测试隔离
    with registry.test_isolation() as test_registry:
        # 设置测试用的服务
        mock_service = Mock()
        test_registry.register(IMyService).set_instance(mock_service)
        
        # 执行测试
        result = function_under_test()
        
        # 验证结果
        assert result is not None
```

### Q4: 如何监控注入层状态？

**A:** 使用状态监控功能：

```python
def monitor_injection_status():
    from src.services.container.injection_base import get_injection_status
    
    status = get_injection_status()
    for service_name, info in status.items():
        print(f"{service_name}: {info}")
```

## 最佳实践

### 1. 服务命名规范

```python
# 好的命名
@injectable(ILogger)
def get_logger():
    pass

@injectable(ILLMManager)
def get_llm_manager():
    pass

# 避免的命名
@injectable(ILogger)
def logger():
    pass  # 太简单，容易冲突
```

### 2. 错误处理

```python
@injectable(IService, fallback_factory=create_fallback)
def get_service():
    """获取服务，带有fallback处理"""
    pass
```

### 3. 文档和类型注解

```python
from typing import Optional

@injectable(ILogger)
def get_logger(module_name: Optional[str] = None) -> ILogger:
    """
    获取日志记录器实例
    
    Args:
        module_name: 模块名称，用于标识日志来源
        
    Returns:
        ILogger: 日志记录器实例
    """
    pass
```

### 4. 测试友好设计

```python
# 在服务绑定中设置注入层
class MyServiceBindings(BaseServiceBindings):
    def _post_register(self, container, config, environment):
        # 为测试环境设置特殊的fallback
        if environment == "test":
            fallback_factory = lambda: Mock(spec=IMyService)
            self.setup_service_injection(container, IMyService, fallback_factory)
        else:
            self.setup_service_injection(container, IMyService)
```

## 总结

通过迁移到新的通用依赖注入便利层框架，我们可以：

1. **提升性能**：减少容器查找开销
2. **简化开发**：提供多种便捷的服务获取方式
3. **增强稳定性**：内置错误处理和降级机制
4. **改善测试**：内置测试隔离和Mock支持
5. **统一管理**：集中管理所有服务的注入逻辑

建议按照本指南逐步迁移，先从高频使用的服务开始，然后逐步推广到整个项目。