# 配置系统工具类迁移指南

本指南提供了将配置系统中的功能拆分为独立工具类的详细步骤和最佳实践。

## 迁移概述

迁移过程分为以下几个阶段：
1. 准备阶段：创建工具目录和基础结构
2. 拆分阶段：逐个拆分工具类
3. 集成阶段：更新配置系统以使用新工具类
4. 清理阶段：移除原有实现

## 准备阶段

### 1. 创建工具目录结构

```bash
mkdir -p src/infrastructure/tools
touch src/infrastructure/tools/__init__.py
```

### 2. 确定迁移优先级

根据以下因素确定迁移优先级：
1. **依赖关系**：优先迁移被其他模块依赖较少的工具类
2. **独立性**：优先迁移独立性强的工具类
3. **使用频率**：优先迁移使用频率高的工具类
4. **复杂度**：优先迁移复杂度低的工具类

建议的迁移顺序：
1. EnvResolver（环境变量解析器）
2. ConfigCache（配置缓存）
3. ConfigMerger（配置合并器）
4. Redactor（敏感信息脱敏器）
5. SchemaLoader（模式加载器）
6. FileWatcher（文件监听器）
7. Validator（配置验证器）
8. BackupManager（备份管理器）
9. InheritanceHandler（继承处理器）
10. ConfigOperations（配置操作工具）

## 拆分阶段

### 1. 环境变量解析器 (EnvResolver)

#### 步骤1：创建独立工具类

```bash
# 创建文件
touch src/infrastructure/tools/env_resolver.py
```

#### 步骤2：复制并修改代码

将 `src/infrastructure/config/processor/env_resolver.py` 的内容复制到新文件，并进行以下修改：

1. 更新文档字符串，强调通用性
2. 移除配置系统特定的引用
3. 确保完全独立

#### 步骤3：创建适配器（保持向后兼容）

在 `src/infrastructure/config/processor/env_resolver.py` 中创建适配器：

```python
"""环境变量解析器 - 向后兼容适配器"""

# 导入新的工具类
from ...tools.env_resolver import EnvResolver as ToolsEnvResolver

# 为了向后兼容，保留原有类名
class EnvResolver(ToolsEnvResolver):
    """环境变量解析器 - 向后兼容适配器
    
    注意：此类已迁移到 src/infrastructure/tools/env_resolver.py
    建议直接使用新的工具类。
    """
    pass
```

### 2. 配置缓存 (ConfigCache)

#### 步骤1：创建独立工具类

```bash
# 创建文件
touch src/infrastructure/tools/cache.py
```

#### 步骤2：复制并修改代码

将 `src/infrastructure/config/config_cache.py` 的内容复制到新文件，并进行以下修改：

1. 重命名为更通用的 `Cache` 类
2. 更新文档字符串
3. 移除配置系统特定的引用

```python
"""通用缓存工具

提供线程安全的缓存功能，可被多个模块使用。
"""

import threading
from typing import Dict, Any, Optional


class Cache:
    """通用缓存管理器"""
    
    def __init__(self, name: str = "default"):
        """初始化缓存
        
        Args:
            name: 缓存名称，用于标识不同的缓存实例
        """
        self.name = name
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    # ... 其余方法保持不变 ...
```

#### 步骤3：更新配置系统

在 `src/infrastructure/config/config_cache.py` 中创建适配器：

```python
"""配置缓存 - 向后兼容适配器"""

from ...tools.cache import Cache

class ConfigCache(Cache):
    """配置缓存管理器 - 向后兼容适配器
    
    注意：此类已迁移到 src/infrastructure/tools/cache.py
    建议直接使用新的 Cache 工具类。
    """
    
    def __init__(self):
        """初始化配置缓存"""
        super().__init__("config")
```

### 3. 配置合并器 (ConfigMerger)

#### 步骤1：创建独立工具类

```bash
# 创建文件
touch src/infrastructure/tools/config_merger.py
```

#### 步骤2：复制并修改代码

将 `src/infrastructure/config/processor/merger.py` 的内容复制到新文件，并进行以下修改：

1. 更新文档字符串，强调通用性
2. 移除配置系统特定的引用
3. 保持接口不变

#### 步骤3：更新配置系统

在 `src/infrastructure/config/processor/merger.py` 中创建适配器：

```python
"""配置合并器 - 向后兼容适配器"""

from ...tools.config_merger import ConfigMerger as ToolsConfigMerger
from ...tools.config_merger import IConfigMerger as ToolsIConfigMerger

# 保持接口兼容
IConfigMerger = ToolsIConfigMerger

class ConfigMerger(ToolsConfigMerger):
    """配置合并器 - 向后兼容适配器
    
    注意：此类已迁移到 src/infrastructure/tools/config_merger.py
    建议直接使用新的工具类。
    """
    pass
```

## 集成阶段

### 1. 更新配置系统

逐步更新配置系统中的各个组件，使其使用新的工具类：

#### ConfigSystem 类更新

```python
# 在 src/infrastructure/config/config_system.py 中

# 更新导入
from ..tools.env_resolver import EnvResolver
from ..tools.config_merger import ConfigMerger
from ..tools.cache import Cache

class ConfigSystem(IConfigSystem):
    def __init__(self, ...):
        # ... 其他初始化代码 ...
        
        # 使用新的工具类
        self._cache = Cache("config")
        self._config_merger = ConfigMerger()
        
        # ... 其他初始化代码 ...
    
    def get_env_resolver(self) -> EnvResolver:
        """获取环境变量解析器"""
        if self._env_resolver is None:
            global_config = self.load_global_config()
            self._env_resolver = EnvResolver(global_config.env_prefix)
        return self._env_resolver
```

#### ConfigServiceFactory 类更新

```python
# 在 src/infrastructure/config/config_service_factory.py 中

# 更新导入
from ..tools.env_resolver import EnvResolver
from ..tools.config_merger import ConfigMerger
from ..tools.validator import Validator

class ConfigServiceFactory:
    @staticmethod
    def create_config_system(...) -> IConfigSystem:
        # 使用新的工具类创建配置系统
        config_merger = ConfigMerger()
        config_validator = Validator()
        
        # ... 其余代码 ...
```

### 2. 更新其他模块

检查项目中其他使用这些工具类的模块，并更新导入路径：

```python
# 旧导入
from src.infrastructure.config.processor.env_resolver import EnvResolver

# 新导入
from src.infrastructure.tools.env_resolver import EnvResolver
```

## 清理阶段

### 1. 移除适配器

在确认所有模块都已使用新的工具类后，可以移除适配器：

```bash
# 移除适配器文件
rm src/infrastructure/config/processor/env_resolver.py
rm src/infrastructure/config/config_cache.py
rm src/infrastructure/config/processor/merger.py
```

### 2. 更新文档

更新所有相关文档，包括：
1. API 文档
2. 开发者指南
3. 架构文档
4. 示例代码

### 3. 更新测试

1. 为新的工具类创建独立的单元测试
2. 更新配置系统的集成测试
3. 移除对原有实现的测试

## 测试策略

### 1. 单元测试

为每个工具类创建独立的单元测试：

```python
# 示例：src/infrastructure/tools/test_env_resolver.py

import pytest
import os
from .env_resolver import EnvResolver


class TestEnvResolver:
    def test_resolve_simple_env_var(self):
        """测试解析简单环境变量"""
        os.environ["TEST_VAR"] = "test_value"
        resolver = EnvResolver()
        
        config = {"key": "${TEST_VAR}"}
        result = resolver.resolve(config)
        
        assert result["key"] == "test_value"
    
    def test_resolve_with_default(self):
        """测试带默认值的环境变量"""
        resolver = EnvResolver()
        
        config = {"key": "${NON_EXISTENT_VAR:default_value}"}
        result = resolver.resolve(config)
        
        assert result["key"] == "default_value"
    
    # ... 更多测试用例 ...
```

### 2. 集成测试

确保配置系统与新工具类的集成正常工作：

```python
# 示例：src/infrastructure/config/test_config_system_integration.py

import pytest
from .config_system import ConfigSystem
from ..tools.env_resolver import EnvResolver


class TestConfigSystemIntegration:
    def test_config_system_with_new_env_resolver(self):
        """测试配置系统使用新的环境变量解析器"""
        config_system = ConfigSystem(...)
        
        # 测试环境变量解析
        resolver = config_system.get_env_resolver()
        assert isinstance(resolver, EnvResolver)
        
        # ... 更多集成测试 ...
```

### 3. 回归测试

运行完整的测试套件，确保迁移没有破坏现有功能：

```bash
# 运行所有测试
pytest src/infrastructure/config/
pytest src/infrastructure/tools/
```

## 最佳实践

### 1. 渐进式迁移

- 一次只迁移一个工具类
- 确保每个步骤都有完整的测试覆盖
- 在完成一个工具类的迁移后再进行下一个

### 2. 向后兼容

- 使用适配器模式保持向后兼容
- 在迁移期间保留原有接口
- 提供清晰的迁移文档和警告

### 3. 文档更新

- 及时更新所有相关文档
- 提供迁移前后的对比
- 包含使用示例和最佳实践

### 4. 代码审查

- 每个迁移步骤都应该经过代码审查
- 确保新工具类的质量和一致性
- 验证是否遵循项目的编码规范

## 常见问题和解决方案

### 1. 循环依赖

**问题**：在拆分过程中可能出现循环依赖。

**解决方案**：
- 仔细分析依赖关系
- 使用依赖注入
- 重新设计接口

### 2. 测试失败

**问题**：迁移后测试失败。

**解决方案**：
- 检查导入路径是否正确
- 确保适配器正确实现
- 更新测试用例以匹配新的实现

### 3. 性能问题

**问题**：新工具类可能引入性能问题。

**解决方案**：
- 进行性能基准测试
- 优化关键路径
- 考虑缓存策略

## 总结

通过遵循本指南，可以安全、高效地将配置系统中的功能拆分为独立的工具类。这种拆分不仅提高了代码的复用性和可维护性，还为整个系统的模块化奠定了基础。

记住，迁移是一个渐进的过程，需要耐心和细致的规划。确保每个步骤都有充分的测试和文档支持，以保证迁移的成功。