# 配置管理系统 (Configuration Management System)

## 概述

本目录包含核心配置管理系统的实现，提供统一的配置加载、处理、验证和管理功能。系统采用分层架构设计，确保配置管理的一致性和可扩展性。

## 架构设计

### 核心组件

#### 1. ConfigManager (`config_manager.py`)
**职责**：配置的实际处理逻辑

- 实现了 `IUnifiedConfigManager` 接口
- 提供配置加载、处理、验证的核心功能
- 支持模块特定的验证器注册
- 管理配置处理器链的执行流程

**主要功能**：
- `load_config()`: 加载并处理配置文件
- `validate_config()`: 验证配置数据
- `register_module_validator()`: 注册模块特定验证器
- `reload_config()`: 重新加载配置

**使用场景**：
- 需要直接处理配置文件的模块
- 需要自定义验证逻辑的场景
- 基础配置管理需求

#### 2. ConfigManagerFactory (`config_manager_factory.py`)
**职责**：配置管理器的创建和管理

- 实现了 `IConfigManagerFactory` 接口
- 负责创建和管理模块特定的配置管理器实例
- 支持装饰器模式扩展功能
- 提供配置管理器的缓存和生命周期管理

**主要功能**：
- `get_manager()`: 获取模块特定的配置管理器
- `register_manager_decorator()`: 注册管理器装饰器
- `clear_manager_cache()`: 清除管理器缓存
- `get_factory_status()`: 获取工厂状态信息

**使用场景**：
- 需要为不同模块提供定制化配置管理器的场景
- 需要扩展配置管理器功能的场景
- 需要管理多个配置管理器实例的场景

### 组件关系

```
ConfigManagerFactory
    ├── 创建和管理 → ConfigManager 实例
    ├── 支持装饰器 → 增强的 ConfigManager
    └── 缓存管理 → 已创建的实例

ConfigManager
    ├── 使用 → ConfigLoader (加载配置)
    ├── 使用 → ConfigProcessorChain (处理配置)
    └── 使用 → ConfigValidator (验证配置)
```

## 设计原则

### 1. 单一职责原则
- `ConfigManager` 专注于配置处理逻辑
- `ConfigManagerFactory` 专注于实例管理

### 2. 开闭原则
- 通过装饰器注册机制扩展功能
- 无需修改现有代码支持新模块类型

### 3. 依赖倒置原则
- 依赖接口而非具体实现
- 通过 `IUnifiedConfigManager` 接口解耦

## 使用指南

### 基础使用

```python
# 直接使用 ConfigManager
from src.core.config.config_manager import ConfigManager
from src.infrastructure.config import ConfigLoader

config_loader = ConfigLoader()
config_manager = ConfigManager(config_loader)
config = config_manager.load_config("app_config.yaml")
```

### 工厂模式使用

```python
# 使用 ConfigManagerFactory
from src.core.config.config_manager_factory import ConfigManagerFactory

factory = ConfigManagerFactory(base_manager)
manager = factory.get_manager("llm_module")
config = manager.load_config("llm_config.yaml", module_type="llm")
```

### 装饰器扩展

```python
# 注册装饰器扩展功能
class EnhancedConfigManager:
    def __init__(self, base_manager):
        self.base_manager = base_manager
    
    def load_config(self, *args, **kwargs):
        # 添加增强逻辑
        config = self.base_manager.load_config(*args, **kwargs)
        # 额外处理
        return enhanced_config

factory.register_manager_decorator("advanced_module", EnhancedConfigManager)
```

## 依赖注入集成

配置管理系统已集成到依赖注入容器中：

```python
# 在服务绑定中注册
from src.services.container.bindings.config_bindings import ConfigServiceBindings

bindings = ConfigServiceBindings()
bindings.register_services(container, config, environment)
```

## 扩展指南

### 添加新的配置处理器

1. 实现 `IConfigProcessor` 接口
2. 在 `ConfigProcessorChain` 中注册处理器

### 添加新的验证器

1. 实现 `IConfigValidator` 接口
2. 通过 `register_module_validator()` 注册

### 添加新的管理器装饰器

1. 创建装饰器类包装基础管理器
2. 通过 `register_manager_decorator()` 注册

## 注意事项

1. **向后兼容性**：系统提供了全局实例和便捷函数以保持向后兼容
2. **生命周期管理**：ConfigManagerFactory 负责管理配置管理器的生命周期
3. **缓存策略**：工厂实现了配置管理器的缓存机制，避免重复创建
4. **线程安全**：配置管理器实例通常是单例，需要注意线程安全问题

## 相关文件

- `src/interfaces/config/interfaces.py`: 接口定义
- `src/services/container/bindings/config_bindings.py`: 依赖注入配置
- `src/services/config/injection.py`: 便利注入层
- `src/infrastructure/config/`: 基础设施层实现

## 最佳实践

1. 优先使用依赖注入获取配置管理器实例
2. 为不同模块类型注册特定的验证器
3. 使用工厂模式管理多个配置管理器实例
4. 通过装饰器模式扩展功能而非修改核心代码
5. 保持配置处理器的无状态设计