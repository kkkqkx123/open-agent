# 统一DI框架使用指南

本文档介绍如何使用重构后的统一DI框架，包括基本用法、高级功能和最佳实践。

## 1. 快速开始

### 1.1 基本初始化

```python
from src.services.configuration.unified_di_framework import (
    initialize_framework,
    shutdown_framework,
    get_service
)

# 初始化框架
container = initialize_framework("development")

try:
    # 使用框架...
    pass
finally:
    # 关闭框架
    shutdown_framework()
```

### 1.2 注册和配置模块

```python
from src.services.configuration.unified_di_framework import register_module_configurator
from src.services.state.state_configurator import create_state_configurator

# 注册状态管理配置器
state_configurator = create_state_configurator()
register_module_configurator("state", state_configurator)

# 配置模块
from src.services.configuration.unified_di_framework import get_global_framework
framework = get_global_framework()

state_config = {
    "enabled": True,
    "default_storage": "sqlite",
    "serialization": {
        "format": "json",
        "compression": True
    }
}
framework.configure_module("state", state_config)
```

## 2. 模块配置器开发

### 2.1 创建自定义配置器

```python
from src.services.configuration.base_configurator import BaseModuleConfigurator
from src.interfaces.container import IDependencyContainer
from typing import Dict, Any

class MyModuleConfigurator(BaseModuleConfigurator):
    def __init__(self):
        super().__init__("my_module")
        self.set_priority(10)  # 设置优先级
        self.add_dependency("state")  # 添加依赖
    
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置服务"""
        if not config.get("enabled", True):
            return
        
        # 注册服务
        container.register(
            IMyService,
            MyService,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    def _create_default_config(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "version": "1.0.0",
            "setting1": "default_value"
        }
    
    def get_required_fields(self) -> List[str]:
        return ["enabled"]
    
    def get_field_types(self) -> Dict[str, Type]:
        return {
            "enabled": bool,
            "version": str,
            "setting1": str
        }
    
    def _validate_custom(self, config: Dict[str, Any]) -> ValidationResult:
        """自定义验证"""
        errors = []
        
        if config.get("setting1") == "invalid_value":
            errors.append("setting1不能是invalid_value")
        
        return ValidationResult(len(errors) == 0, errors, [])
```

### 2.2 注册配置器

```python
from src.services.configuration.unified_di_framework import register_module_configurator

configurator = MyModuleConfigurator()
register_module_configurator("my_module", configurator)
```

## 3. 配置模板系统

### 3.1 使用预定义模板

```python
from src.services.configuration.unified_di_framework import configure_from_template

# 使用开发环境模板
configure_from_template("development", variables={
    "DB_HOST": "localhost",
    "DB_NAME": "my_dev_db"
})

# 使用生产环境模板
configure_from_template("production", variables={
    "DB_HOST": "prod-db-server",
    "DB_NAME": "my_prod_db",
    "REDIS_HOST": "redis-server"
})

# 使用测试环境模板
configure_from_template("testing")
```

### 3.2 创建自定义模板

```python
from src.services.configuration.template_system import ConfigurationTemplate, register_template

template_content = {
    "my_module": {
        "enabled": True,
        "version": "${MODULE_VERSION:1.0.0}",
        "database": {
            "host": "${DB_HOST:localhost}",
            "port": "${DB_PORT:5432}",
            "name": "${DB_NAME}"
        }
    }
}

template = ConfigurationTemplate("my_template", template_content)
register_template(template)

# 使用模板
configure_from_template("my_template", variables={
    "MODULE_VERSION": "2.0.0",
    "DB_HOST": "custom-db",
    "DB_NAME": "custom_db"
})
```

## 4. 高级功能

### 4.1 依赖分析

```python
from src.services.configuration.unified_di_framework import get_global_framework

framework = get_global_framework()
container = framework.get_container()

# 分析依赖关系
analysis = container.analyze_dependencies()
print(f"总服务数: {len(analysis.dependency_graph)}")
print(f"循环依赖: {len(analysis.circular_dependencies)}")
print(f"最大依赖深度: {analysis.max_dependency_depth}")

# 获取依赖链
for service_type, deps in analysis.dependency_graph.items():
    print(f"{service_type.__name__} 依赖于: {[d.__name__ for d in deps]}")
```

### 4.2 服务追踪

```python
# 获取服务追踪器
tracker = container.get_service_tracker()

# 获取使用统计
stats = tracker.get_service_usage_statistics()
for service_type, stat in stats.items():
    print(f"{service_type.__name__}:")
    print(f"  创建总数: {stat.total_created}")
    print(f"  当前活跃: {stat.current_active}")
    print(f"  平均生命周期: {stat.average_lifetime}")

# 检测内存泄漏
leaks = tracker.detect_memory_leaks()
for leak in leaks:
    print(f"潜在内存泄漏: {leak.service_type.__name__}")
    print(f"  泄漏实例数: {leak.total_instances}")
    print(f"  持续时间: {leak.leak_duration}")
```

### 4.3 生命周期管理

```python
# 获取生命周期管理器
lifecycle_manager = framework.get_lifecycle_manager()

# 启动所有服务
results = lifecycle_manager.start_all_services()
for service_name, success in results.items():
    print(f"{service_name}: {'启动成功' if success else '启动失败'}")

# 获取服务状态
status = lifecycle_manager.get_all_service_status()
for service_name, service_status in status.items():
    print(f"{service_name}: {service_status.value}")

# 注册事件处理器
def on_service_started(service_name: str):
    print(f"服务已启动: {service_name}")

lifecycle_manager.register_lifecycle_event_handler("started", on_service_started)
```

### 4.4 配置验证

```python
from src.services.configuration.validation_rules import (
    CommonValidationRules,
    EnumRule,
    RangeRule
)

# 创建验证规则
rules = [
    CommonValidationRules.required_string("api_key"),
    CommonValidationRules.positive_integer("timeout"),
    EnumRule("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"]),
    RangeRule("max_connections", min_value=1, max_value=1000)
]

# 添加到配置验证器
validator = framework.get_configuration_manager()._validator
for rule in rules:
    validator.add_validation_rule("my_module", rule)

# 验证配置
config = {
    "api_key": "secret_key",
    "timeout": 30,
    "log_level": "INFO",
    "max_connections": 100
}

validation_result = validator.validate_module_configuration("my_module", config)
if not validation_result.is_success():
    print(f"配置验证失败: {validation_result.errors}")
```

## 5. 插件系统

### 5.1 创建插件

```python
from src.interfaces.container import IContainerPlugin, IDependencyContainer

class MyPlugin(IContainerPlugin):
    def initialize(self, container: IDependencyContainer) -> None:
        """初始化插件"""
        # 可以在这里注册额外的服务或修改现有服务
        print(f"插件 {self.get_plugin_name()} 初始化")
    
    def get_plugin_name(self) -> str:
        return "my_plugin"
    
    def get_plugin_version(self) -> str:
        return "1.0.0"
    
    def cleanup(self) -> None:
        """清理插件资源"""
        print(f"插件 {self.get_plugin_name()} 清理完成")
```

### 5.2 注册插件

```python
from src.services.configuration.unified_di_framework import get_global_framework

framework = get_global_framework()
container = framework.get_container()

# 注册插件
plugin = MyPlugin()
container.register_plugin(plugin)

# 初始化所有插件
container.initialize_plugins()
```

## 6. 性能优化

### 6.1 获取优化建议

```python
framework = get_global_framework()
suggestions = framework.optimize_configuration()

print(f"总影响分数: {suggestions['total_impact_score']}")
print(f"高优先级建议数: {suggestions['high_priority_count']}")

for suggestion in suggestions['suggestions']:
    print(f"- {suggestion['description']} (影响: {suggestion['impact']})")
```

### 6.2 服务预热

```python
# 预热关键服务
critical_services = [IMyService, IStateService, ILLMService]
container.prewarm_services(critical_services)
```

### 6.3 懒加载

```python
# 获取懒加载代理
lazy_service = container.get_lazy(IMyService)

# 实际使用时才会创建实例
service = lazy_service()
```

## 7. 监控和调试

### 7.1 框架状态监控

```python
# 获取框架状态
status = framework.get_framework_status()

print(f"容器指标:")
metrics = status['container_metrics']
print(f"  总服务数: {metrics['total_services']}")
print(f"  缓存命中率: {metrics['cache_hit_rate']:.2%}")
print(f"  平均解析时间: {metrics['average_resolution_time']:.4f}s")

print(f"生命周期统计:")
lifecycle_stats = status['lifecycle_statistics']
print(f"  总服务数: {lifecycle_stats['total_services']}")
print(f"  总错误数: {lifecycle_stats['total_errors']}")
```

### 7.2 事件追踪

```python
# 获取最近事件
lifecycle_manager = framework.get_lifecycle_manager()
recent_events = lifecycle_manager.get_recent_events(50)

for event in recent_events:
    print(f"{event.timestamp}: {event.service_name} - {event.event_type}")
```

## 8. 最佳实践

### 8.1 模块设计原则

1. **单一职责**：每个配置器只负责一个模块的配置
2. **依赖明确**：明确声明模块间的依赖关系
3. **配置验证**：实现完整的配置验证逻辑
4. **默认配置**：提供合理的默认配置

### 8.2 生命周期管理

1. **正确顺序**：按照依赖关系顺序启动和停止服务
2. **错误处理**：实现适当的错误处理和恢复机制
3. **资源清理**：确保所有资源都能正确释放

### 8.3 性能优化

1. **合理使用生命周期**：根据服务特性选择合适的生命周期
2. **服务预热**：对关键服务进行预热
3. **监控指标**：定期检查性能指标和优化建议

### 8.4 测试策略

1. **单元测试**：为每个配置器编写单元测试
2. **集成测试**：测试模块间的协作
3. **性能测试**：验证性能优化效果

## 9. 迁移指南

### 9.1 从旧配置方式迁移

```python
# 旧方式
from src.services.state.di_config import configure_state_services
configure_state_services(container, config)

# 新方式
from src.services.state.state_configurator import create_state_configurator
from src.services.configuration.unified_di_framework import register_module_configurator

configurator = create_state_configurator()
register_module_configurator("state", configurator)

framework = get_global_framework()
framework.configure_module("state", config)
```

### 9.2 渐进式迁移

1. **先迁移接口**：保持现有接口不变，内部使用新框架
2. **逐步替换**：逐个模块迁移到新框架
3. **验证功能**：确保迁移后功能正常
4. **性能对比**：验证性能改进效果

## 10. 故障排除

### 10.1 常见问题

1. **循环依赖**：使用依赖分析器检测并解决
2. **配置验证失败**：检查配置格式和必需字段
3. **服务启动失败**：查看生命周期事件和错误日志
4. **内存泄漏**：使用服务追踪器检测泄漏

### 10.2 调试技巧

1. **启用详细日志**：设置日志级别为DEBUG
2. **使用框架状态**：定期检查框架状态
3. **分析依赖关系**：使用依赖分析器理解服务关系
4. **监控性能指标**：关注关键性能指标

通过遵循本指南，您可以充分利用统一DI框架的功能，构建可维护、高性能的应用程序。