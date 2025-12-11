# 配置系统架构设计指南

## 概述

本文档详细描述了重构后的配置系统架构，包括各层的职责、接口定义、实现规范和迁移指南，为后续迁移其他模块提供参考。

## 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    Services Layer (服务层)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │WorkflowConfig   │  │LLMConfigService │  │ToolsConfigService│ │
│  │Service          │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │StateConfig      │  │StorageConfig   │  │SessionConfig    │ │
│  │Service          │  │Service         │  │Service          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer (核心层)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ConfigManager    │  │ModuleConfig    │  │ConfigMapper     │ │
│  │(Enhanced)       │  │Registry        │  │Registry         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │WorkflowMapper   │  │LLMMapper        │  │ToolsMapper      │ │
│  │(Core)           │  │(Core)           │  │(Core)           │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer (基础设施层)             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ConfigLoader     │  │ProcessorChain  │  │ConfigValidator  │ │
│  │(Enhanced)       │  │(Enhanced)      │  │(Enhanced)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │CrossModule      │  │ConfigCache     │  │ConfigStorage    │ │
│  │Resolver         │  │(Enhanced)       │  │(Enhanced)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                 Interfaces Layer (接口层)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │IConfigManager   │  │IConfigMapper   │  │IModuleConfig    │ │
│  │IConfigService   │  │IConfigLoader   │  │IService         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Interfaces Layer (接口层)

### 职责
定义所有配置相关的接口和数据结构，不包含任何实现逻辑。

### 核心接口文件

#### `src/interfaces/config/mapper.py`
**必须实现的接口**：
- `IConfigMapper`：配置映射器接口
- `IModuleConfigService`：模块配置服务接口
- `IModuleConfigRegistry`：模块配置注册表接口
- `IConfigMapperRegistry`：配置映射器注册表接口
- `ICrossModuleResolver`：跨模块引用解析器接口
- `IModuleConfigLoader`：模块配置加载器接口
- `IConfigChangeListener`：配置变更监听器接口
- `IConfigWatcher`：配置监听器接口
- `IConfigMonitor`：配置监控器接口
- `IConfigVersionManager`：配置版本管理器接口
- `IConfigStorage`：配置存储接口

**数据结构**：
- `ModuleConfig`：模块配置定义
- `ModuleDependency`：模块依赖定义
- `ConfigChangeEvent`：配置变更事件
- `ConfigVersion`：配置版本信息

**导入规范**：
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
```

#### `src/interfaces/config/manager.py`
**必须实现的接口**：
- `IConfigManager`：基础配置管理器接口
- `IUnifiedConfigManager`：统一配置管理器接口
- `IConfigManagerFactory`：配置管理器工厂接口

**导入规范**：
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..common_domain import ValidationResult
```

## Core Layer (核心层)

### 职责
实现配置系统的核心业务逻辑和映射功能，包含领域实体和业务规则。

### 核心组件文件

#### `src/core/config/config_manager.py`
**必须实现的类**：
- `UnifiedConfigManager`：统一配置管理器
- `ModuleConfigRegistry`：模块配置注册表
- `ConfigMapperRegistry`：配置映射器注册表
- `CrossModuleResolver`：跨模块引用解析器

**导入规范**：
```python
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar, List
import logging

from src.interfaces.config import (
    IConfigLoader, IConfigProcessor, IConfigValidator, IUnifiedConfigManager,
    IConfigInheritanceHandler, IModuleConfigRegistry, IConfigMapperRegistry,
    ICrossModuleResolver, IModuleConfigLoader, ModuleConfig
)
from src.interfaces.common_domain import ValidationResult
from src.interfaces.config import (
    ConfigError, ConfigNotFoundError, ConfigValidationError
)
from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
from src.infrastructure.config.validation import BaseConfigValidator
```

#### `src/core/{module}/mappers/{module}_config_mapper.py`
**必须实现的类**：
- `{Module}ConfigMapper`：模块配置映射器

**导入规范**：
```python
from typing import Dict, Any, Optional
from src.interfaces.config import IConfigMapper, ValidationResult
from src.interfaces.common_domain import ValidationResult as CommonValidationResult
from ..graph_entities import {Module}Entity
```

**必须实现的方法**：
```python
def dict_to_entity(self, config_data: Dict[str, Any]) -> {Module}Entity:
    """将配置字典转换为业务实体"""
    pass

def entity_to_dict(self, entity: {Module}Entity) -> Dict[str, Any]:
    """将业务实体转换为配置字典"""
    pass

def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
    """验证配置数据"""
    pass
```

## Services Layer (服务层)

### 职责
提供面向应用的高级配置服务，协调各组件完成配置管理任务。

### 核心组件文件

#### `src/services/{module}/config_service.py`
**必须实现的类**：
- `{Module}ConfigService`：模块配置服务

**导入规范**：
```python
from typing import Dict, Any, Optional
import logging

from src.interfaces.config import (
    IModuleConfigService, IUnifiedConfigManager, ValidationResult
)
from src.interfaces.dependency_injection import get_logger
from src.core.{module}.graph_entities import {Module}Entity
from src.core.{module}.mappers.config_mapper import get_{module}_config_mapper
```

**必须实现的方法**：
```python
def load_config(self, config_path: str) -> {Module}Entity:
    """加载模块配置"""
    pass

def save_config(self, config: {Module}Entity, config_path: str) -> None:
    """保存模块配置"""
    pass

def validate_config(self, config: {Module}Entity) -> ValidationResult:
    """验证模块配置"""
    pass
```

#### `src/services/config/config_service.py`
**必须实现的类**：
- `ConfigService`：配置服务

**导入规范**：
```python
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from src.interfaces.config import (
    IConfigManager, IModuleConfigService, IConfigMapperRegistry,
    IConfigChangeListener, IConfigMonitor, IConfigVersionManager,
    ConfigChangeEvent, ValidationResult, ModuleConfig, ModuleDependency
)
from src.interfaces.dependency_injection import get_logger
```

## Infrastructure Layer (基础设施层)

### 职责
提供配置系统的基础技术支撑，包括文件操作、缓存、存储等。

### 核心组件文件

#### `src/infrastructure/config/config_loader.py`
**必须实现的类**：
- `ConfigLoader`：配置加载器

**导入规范**：
```python
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable

from src.interfaces.config import (
    ConfigError, ConfigNotFoundError, ConfigFormatError
)
from src.interfaces.config import IConfigLoader
```

#### `src/infrastructure/config/impl/base_impl.py`
**必须实现的类**：
- `ConfigProcessorChain`：配置处理器链
- `BaseConfigValidator`：基础配置验证器
- `ConfigSchema`：配置模式

**导入规范**：
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from src.interfaces.config import IConfigLoader, IConfigProcessor, ValidationResult
from src.interfaces.common_domain import ValidationResult as CommonValidationResult
```

## 模块迁移指南

### 步骤1：创建接口定义
1. 在 `src/interfaces/config/mapper.py` 中添加模块特定的接口（如果需要）
2. 确保所有接口都继承自相应的基类

### 步骤2：实现核心映射器
1. 创建 `src/core/{module}/mappers/{module}_config_mapper.py`
2. 实现 `IConfigMapper` 接口
3. 添加配置验证逻辑
4. 提供便捷函数和向后兼容别名

### 步骤3：实现服务层
1. 创建 `src/services/{module}/config_service.py`
2. 实现 `IModuleConfigService` 接口
3. 添加模块特定的业务逻辑
4. 提供便捷函数

### 步骤4：更新模块导出
1. 更新 `src/core/{module}/__init__.py`
2. 更新 `src/services/{module}/__init__.py`
3. 确保所有新组件都被正确导出

### 步骤5：注册到系统
1. 在 `ConfigService` 中注册模块服务
2. 在 `ConfigMapperRegistry` 中注册映射器
3. 更新依赖注入配置

### 步骤6：删除旧文件
1. 删除旧的配置文件
2. 更新所有引用
3. 运行测试确保兼容性

## 命名规范

### 类命名
- 接口：以 `I` 开头，如 `IConfigMapper`
- 实现类：描述性名称，如 `WorkflowConfigMapper`
- 服务类：以 `Service` 结尾，如 `WorkflowConfigService`

### 文件命名
- 接口文件：`mapper.py`、`manager.py`
- 实现文件：`{module}_config_mapper.py`、`config_service.py`
- 测试文件：`test_{module}_config.py`

### 方法命名
- 接口方法：描述性名称，如 `dict_to_entity`
- 便捷函数：`get_{module}_config_mapper`
- 工厂函数：`create_{module}_config_service`

## 依赖关系

### 层间依赖
- Services → Core → Infrastructure → Interfaces
- 禁止反向依赖
- 同层内可以相互依赖

### 模块间依赖
- 通过 `CrossModuleResolver` 解析跨模块引用
- 使用 `ModuleDependency` 定义依赖关系
- 避免循环依赖

## 测试规范

### 单元测试
- 每个映射器都需要测试
- 每个服务都需要测试
- 测试覆盖率 ≥ 90%

### 集成测试
- 测试模块间协作
- 测试配置加载流程
- 测试错误处理

### 测试文件结构
```
tests/
├── unit/
│   ├── core/
│   │   └── {module}/
│   │       └── test_{module}_config_mapper.py
│   └── services/
│       └── {module}/
│           └── test_{module}_config_service.py
└── integration/
    └── test_config_system.py
```

## 最佳实践

### 1. 接口设计
- 保持接口简洁
- 使用类型注解
- 提供详细的文档字符串

### 2. 错误处理
- 使用特定的异常类型
- 提供有意义的错误消息
- 记录详细的错误日志

### 3. 性能优化
- 使用配置缓存
- 延迟加载配置
- 批量处理配置操作

### 4. 安全考虑
- 验证所有输入
- 处理敏感信息
- 记录配置变更

## 迁移检查清单

- [ ] 创建了所有必需的接口
- [ ] 实现了核心映射器
- [ ] 实现了服务层组件
- [ ] 更新了模块导出
- [ ] 注册到配置系统
- [ ] 删除了旧文件
- [ ] 运行了所有测试
- [ ] 更新了文档
- [ ] 验证了向后兼容性

通过遵循本指南，可以确保所有模块的配置系统都遵循统一的架构和规范，提高系统的可维护性和可扩展性。