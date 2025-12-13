`src/infrastructure/config/processor` 目录被广泛使用，是配置系统的核心组件：

## 主要使用场景

### 1. 依赖注入系统
- [`src/services/container/bindings/config_bindings.py`](src/services/container/bindings/config_bindings.py)：注册处理器到依赖容器
- [`src/interfaces/dependency_injection/config.py`](src/interfaces/dependency_injection/config.py)：提供全局处理器实例

### 2. 配置工厂
- [`src/infrastructure/config/factory.py`](src/infrastructure/config/factory.py)：注册所有处理器到配置注册表
- 创建默认处理器链：`inheritance`、`environment`、`reference`、`transformation`、`validation`

### 3. TUI适配器
- [`src/adapters/tui/config.py`](src/adapters/tui/config.py)：直接使用 EnvironmentProcessor 处理环境变量

### 4. 配置模块导出
- [`src/infrastructure/config/__init__.py`](src/infrastructure/config/__init__.py)：导出所有处理器类

### 5. 具体处理器使用

**InheritanceProcessor**：
- 依赖注入中注册为工厂
- 配置工厂中注册为 "inheritance" 处理器
- 被配置处理器链使用

**EnvironmentProcessor**：
- 配置工厂中注册为 "environment" 处理器
- 被 TUI 适配器直接使用

**ReferenceProcessor**：
- 依赖注入中注册为工厂
- 配置工厂中注册为 "reference" 处理器

**TransformationProcessor**：
- 配置工厂中注册为 "transformation" 处理器
- 包含 TypeConverter 类型转换功能

**ValidationProcessorWrapper**：
- 配置工厂中注册为 "validation" 处理器
- 支持模块特定的验证处理器

## 结论

`src/infrastructure/config/processor` 目录是**配置系统的核心组件**，被广泛使用于：
- 配置处理流程
- 依赖注入系统
- 用户界面适配
- 全局服务提供

这些处理器负责配置的继承、环境变量解析、引用处理、类型转换和验证等核心功能，是配置系统正常运行的关键组件。