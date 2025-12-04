# 依赖注入容器通用规范改进总结

## 概述

基于对日志依赖注入容器的分析，我们实现了三个通用规范，并将其应用到整个依赖注入容器系统中：

1. **延迟依赖解析**
2. **异常处理规范**
3. **测试支持机制**

## 改进内容

### 1. 新增接口和类

#### 异常处理 (`src/interfaces/container/exceptions.py`)
- `ContainerException` - 容器基础异常类
- `RegistrationError` - 注册错误
- `ServiceNotFoundError` - 服务未找到错误
- `ServiceCreationError` - 服务创建错误
- `CircularDependencyError` - 循环依赖错误
- `ValidationError` - 验证错误
- `IExceptionHandler` - 异常处理器接口
- `DefaultExceptionHandler` - 默认异常处理器

#### 测试支持 (`src/interfaces/container/testing.py`)
- `ITestContainerManager` - 测试容器管理器接口
- `IMockServiceRegistry` - Mock服务注册器接口
- `ITestIsolationStrategy` - 测试隔离策略接口
- `DefaultTestIsolationStrategy` - 默认测试隔离策略
- `TestContainerManager` - 测试容器管理器实现
- `MockServiceRegistry` - Mock服务注册器实现

#### 服务绑定基类 (`src/services/container/base_service_bindings.py`)
- `BaseServiceBindings` - 服务绑定基类
- `EnvironmentSpecificBindings` - 环境特定绑定基类

#### 优化的日志绑定 (`src/services/container/logger_bindings_v2.py`)
- `LoggerServiceBindings` - 使用通用规范的日志绑定
- `EnvironmentSpecificLoggerBindings` - 环境特定的日志绑定

### 2. 容器核心功能增强

#### 延迟依赖解析
```python
def register_factory_with_delayed_resolution(
    self,
    interface: Type,
    factory_factory: Callable[[], Callable[..., Any]],
    environment: str = "default",
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """注册延迟解析的工厂工厂"""
```

#### 批量依赖解析
```python
def resolve_dependencies(self, service_types: List[Type]) -> Dict[Type, Any]:
    """批量解析依赖，支持循环依赖检测"""
```

#### 异常处理支持
```python
def set_exception_handler(self, handler: IExceptionHandler) -> None:
    """设置异常处理器"""

def _handle_exception(self, exception: Exception, context: str) -> None:
    """统一异常处理"""
```

#### 测试隔离支持
```python
def create_test_isolation(self, isolation_id: Optional[str] = None) -> 'DependencyContainer':
    """创建测试隔离容器"""

def reset_test_state(self, isolation_id: Optional[str] = None) -> None:
    """重置测试状态"""
```

## 使用示例

### 1. 基本使用（使用新的日志绑定）

```python
from src.services.container import get_global_container
from src.services.container.logger_bindings_v2 import setup_global_logger_services

# 获取容器
container = get_global_container()

# 日志配置
config = {
    "log_level": "INFO",
    "log_outputs": [
        {
            "type": "console",
            "level": "INFO",
            "formatter": "color"
        }
    ]
}

# 设置全局日志服务
setup_global_logger_services(container, config, environment="production")
```

### 2. 使用延迟依赖解析

```python
from src.services.container import get_global_container
from src.interfaces.logger import ILogger, ILogRedactor

container = get_global_container()

# 注册延迟解析的工厂
def logger_factory_factory():
    def logger_factory():
        # 在这里解析依赖，避免循环依赖
        redactor = container.get(ILogRedactor)
        # 创建logger实例
        return create_logger_with_redactor(redactor)
    return logger_factory

container.register_factory_with_delayed_resolution(
    ILogger,
    logger_factory_factory
)
```

### 3. 异常处理

```python
from src.interfaces.container.exceptions import DefaultExceptionHandler

# 创建自定义异常处理器
class CustomExceptionHandler(DefaultExceptionHandler):
    def handle_registration_error(self, error, service_type):
        # 发送告警
        send_alert(f"服务注册失败: {service_type}")
        # 记录到监控系统
        monitor_error(error)
        return False  # 继续抛出异常

# 设置异常处理器
container.set_exception_handler(CustomExceptionHandler())
```

### 4. 测试隔离

```python
from src.services.container.logger_bindings_v2 import isolated_test_logger

# 使用隔离的测试环境
with isolated_test_logger(container, test_config) as test_env:
    # 在隔离环境中测试
    logger = container.get(ILogger)
    logger.info("测试日志消息")
    # 测试结束后自动清理
```

### 5. 环境特定配置

```python
from src.services.container.logger_bindings_v2 import setup_environment_logger_services

# 为不同环境设置日志服务
setup_environment_logger_services(container, base_config, "development")
setup_environment_logger_services(container, base_config, "production")
setup_environment_logger_services(container, base_config, "test")
```

### 6. 创建自定义服务绑定

```python
from src.services.container.base_service_bindings import BaseServiceBindings
from src.interfaces.container.exceptions import ValidationError

class DatabaseServiceBindings(BaseServiceBindings):
    def _validate_config(self, config):
        errors = []
        if "connection_string" not in config:
            errors.append("缺少connection_string配置")
        if errors:
            raise ValidationError("数据库配置验证失败", errors)
    
    def _do_register_services(self, container, config, environment):
        # 注册数据库服务
        self.register_delayed_factory(
            container,
            IDatabaseService,
            lambda: lambda: DatabaseService(config["connection_string"]),
            environment
        )
    
    def _post_register(self, container, config, environment):
        # 注册后处理，比如健康检查
        if environment == "production":
            self._register_health_check(container, config)

# 使用自定义绑定
bindings = DatabaseServiceBindings()
bindings.register_services(container, db_config, "production")
```

## 向后兼容性

所有新功能都保持了向后兼容性：

1. **现有API保持不变**：原有的 `register`、`register_factory`、`get` 等方法继续工作
2. **降级处理**：新功能在不支持时会降级到原有行为
3. **可选参数**：新功能通过可选参数或新方法提供

## 性能影响

1. **延迟依赖解析**：实际上提高了性能，因为只在需要时才解析依赖
2. **异常处理**：最小化性能影响，只在异常发生时才有开销
3. **测试支持**：只在测试环境中使用，不影响生产环境性能

## 最佳实践

### 1. 服务绑定开发

```python
# 继承BaseServiceBindings
class MyServiceBindings(BaseServiceBindings):
    def _validate_config(self, config):
        # 验证配置
        pass
    
    def _do_register_services(self, container, config, environment):
        # 使用延迟依赖解析避免循环依赖
        self.register_delayed_factory(container, IMyService, factory_factory)
    
    def _post_register(self, container, config, environment):
        # 注册后处理
        pass
```

### 2. 异常处理

```python
# 设置自定义异常处理器
container.set_exception_handler(MyExceptionHandler())

# 在服务绑定中使用
self.register_with_error_handling(
    container, 
    register_func, 
    "服务描述", 
    environment
)
```

### 3. 测试隔离

```python
# 使用测试隔离上下文
with bindings.test_isolation(container, test_config) as test_container:
    # 测试逻辑
    pass
# 自动清理
```

## 迁移指南

### 从原有日志绑定迁移

1. **简单替换**：
```python
# 原有方式
from src.services.container.logger_bindings import setup_global_logger_services

# 新方式
from src.services.container.logger_bindings_v2 import setup_global_logger_services
```

2. **使用新的绑定类**：
```python
# 原有方式
register_logger_services(container, config, environment)

# 新方式
bindings = LoggerServiceBindings()
bindings.register_services(container, config, environment)
```

### 为现有服务绑定添加通用规范

1. **继承基类**：
```python
# 原有方式
def register_my_services(container, config, environment):
    # 注册逻辑
    pass

# 新方式
class MyServiceBindings(BaseServiceBindings):
    def _do_register_services(self, container, config, environment):
        # 注册逻辑
        pass
```

2. **添加异常处理**：
```python
# 在注册方法中使用异常处理
self.register_with_error_handling(container, register_func, "描述", environment)
```

## 总结

通过实施这三个通用规范，我们显著提升了依赖注入容器的：

1. **可靠性**：通过统一的异常处理和循环依赖检测
2. **可测试性**：通过测试隔离和Mock支持
3. **可维护性**：通过基类和最佳实践模式
4. **性能**：通过延迟依赖解析优化

这些改进不仅解决了日志绑定中发现的问题，还为整个系统提供了统一的、可扩展的依赖注入解决方案。