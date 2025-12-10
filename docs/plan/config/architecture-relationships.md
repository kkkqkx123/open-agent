# Infrastructure层配置架构关系设计

## 概述

本文档定义了`src/infrastructure/config`目录中各个层次间的关系组织，明确依赖方向和接口使用原则。

## 架构原则

### 1. 依赖倒置原则
- 高层模块不依赖低层模块，都依赖抽象
- 抽象不依赖细节，细节依赖抽象

### 2. 单向依赖原则
```
processor ← impl ← provider ← factory/registry
```

### 3. 接口隔离原则
- 每个层次只依赖需要的接口
- 不依赖不需要的接口

## 层次职责

### 1. Interfaces层 (`src/infrastructure/config/interfaces.py`)
**职责**: 定义Infrastructure层内部各组件间的接口

**主要接口**:
- `IConfigSchema`: 配置模式接口
- `ISchemaRegistry`: 模式注册表接口
- `IConfigProcessorChain`: 处理器链接口
- `ITypeConverter`: 类型转换器接口

**依赖**: 无（最底层）

### 2. Processor层 (`src/infrastructure/config/processor/`)
**职责**: 提供配置处理的基础功能

**主要组件**:
- `BaseConfigProcessor`: 处理器基类
- `ValidationProcessor`: 验证处理器
- `TransformationProcessor`: 转换处理器
- `EnvironmentProcessor`: 环境变量处理器
- `InheritanceProcessor`: 继承处理器
- `ReferenceProcessor`: 引用处理器

**依赖关系**:
- ✅ 依赖 `interfaces.py` 中的接口
- ✅ 依赖 `src.interfaces.config` 中的外部接口
- ❌ 不依赖 `impl/` 或 `provider/`

### 3. Implementation层 (`src/infrastructure/config/impl/`)
**职责**: 提供配置实现的基础框架

**主要组件**:
- `BaseConfigImpl`: 配置实现基类
- `ConfigProcessorChain`: 处理器链实现
- `ConfigSchema`: 配置模式实现

**依赖关系**:
- ✅ 依赖 `interfaces.py` 中的接口
- ✅ 依赖 `processor/` 中的处理器
- ❌ 不依赖 `provider/`

### 4. Provider层 (`src/infrastructure/config/provider/`)
**职责**: 提供配置的高级接口和缓存功能

**主要组件**:
- `BaseConfigProvider`: 提供者基类
- `CommonConfigProvider`: 通用配置提供者

**依赖关系**:
- ✅ 依赖 `interfaces.py` 中的接口
- ✅ 依赖 `impl/` 中的实现
- ❌ 不被其他层依赖

### 5. 管理层 (`src/infrastructure/config/`)
**职责**: 提供配置系统的管理和创建功能

**主要组件**:
- `ConfigRegistry`: 配置注册中心
- `ConfigFactory`: 配置工厂
- `ConfigLoader`: 配置加载器

**依赖关系**:
- ✅ 依赖 `interfaces.py` 中的接口
- ✅ 依赖 `processor/`、`impl/`、`provider/`
- ❌ 不被其他层依赖

## 依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    Management Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  ConfigRegistry │  │  ConfigFactory  │  │  ConfigLoader   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Provider Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │BaseConfigProvider│  │CommonConfigProv │                     │
│  └─────────────────┘  └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Implementation Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  BaseConfigImpl │  │ConfigProcessorCh │  │  ConfigSchema   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Processor Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ValidationProcessor│  │TransformationPr │  │EnvironmentProc  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Interfaces Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  IConfigSchema  │  │ ISchemaRegistry │  │IConfigProcessor  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 接口使用指南

### 1. Processor层使用接口

```python
# 正确：依赖接口
from ..interfaces import ISchemaRegistry, ValidationResult

class ValidationProcessor(BaseConfigProcessor):
    def __init__(self, schema_registry: ISchemaRegistry):
        self.schema_registry = schema_registry

# 错误：依赖具体实现
from ..impl.base_impl import ConfigSchema  # ❌ 违反依赖方向
```

### 2. Implementation层使用接口

```python
# 正确：依赖接口
from ..interfaces import IConfigSchema, IConfigProcessorChain

class BaseConfigImpl(IConfigImpl):
    def __init__(self, processor_chain: IConfigProcessorChain, schema: IConfigSchema):
        self.processor_chain = processor_chain
        self.schema = schema
```

### 3. Provider层使用接口

```python
# 正确：依赖接口
from ..impl.base_impl import IConfigImpl

class BaseConfigProvider(IConfigProvider):
    def __init__(self, config_impl: IConfigImpl):
        self.config_impl = config_impl
```

## 实例化原则

### 1. 依赖注入
所有具体实例的创建应该在Factory或Registry中进行，通过依赖注入传递给需要的组件。

```python
# 在Factory中创建实例
class ConfigFactory:
    def create_validation_processor(self):
        schema_registry = SchemaRegistry()  # 具体实现
        return ValidationProcessor(schema_registry)  # 注入接口
```

### 2. 接口编程
外部代码应该依赖接口而不是具体实现。

```python
# 正确：依赖接口
def process_config(processor: IConfigProcessor, config: Dict[str, Any]):
    return processor.process(config, "path")

# 错误：依赖具体实现
def process_config(processor: ValidationProcessor, config: Dict[str, Any]):  # ❌
    return processor.process(config, "path")
```

## 扩展指南

### 1. 添加新的Processor
1. 继承 `BaseConfigProcessor`
2. 只依赖 `interfaces.py` 中的接口
3. 不依赖 `impl/` 或 `provider/`

### 2. 添加新的Impl
1. 继承 `BaseConfigImpl`
2. 依赖 `processor/` 中的处理器
3. 实现 `interfaces.py` 中的接口

### 3. 添加新的Provider
1. 继承 `BaseConfigProvider`
2. 依赖 `impl/` 中的实现
3. 提供高级配置功能

## 违规检查清单

### ❌ 禁止的依赖关系
- Processor层依赖Impl层
- Processor层依赖Provider层
- Impl层依赖Provider层
- 任何层依赖Management层

### ✅ 允许的依赖关系
- 任何层依赖Interfaces层
- Impl层依赖Processor层
- Provider层依赖Impl层
- Management层依赖所有层

### ✅ 允许的外部依赖
- `src.interfaces.config` 中的接口
- `src.interfaces.common_domain` 中的类型
- 标准库和第三方库

## 总结

通过明确的依赖关系和接口定义，我们实现了：

1. **清晰的分层架构**: 每层职责明确，依赖方向清晰
2. **松耦合设计**: 通过接口隔离，降低组件间耦合
3. **易于扩展**: 新组件可以轻松添加到相应层次
4. **易于测试**: 每层可以独立测试，通过Mock接口进行单元测试

这种设计确保了配置系统的可维护性和可扩展性，同时遵循了项目的分层架构原则。