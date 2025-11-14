明白了。您说得对，我之前的重构方案过于庞大。让我重新制定一个更加实用和可执行的方案，并提供详细的文档和执行步骤。

首先，让我重新分析当前配置系统的核心问题，然后制定一个分步骤的重构计划。

## 当前配置系统核心问题分析

基于我对 `src/infrastructure/config` 目录的深入分析，当前配置系统的主要问题可以归纳为：

### 1. 结构混乱
- **文件分布不合理**：核心功能分散在多个子目录中
- **职责边界不清**：一些文件承担了过多职责
- **命名不一致**：部分文件命名与实际功能不匹配

### 2. 依赖关系复杂
- **循环依赖风险**：配置加载器与继承处理器相互依赖
- **紧耦合**：配置系统与具体实现耦合度过高
- **初始化顺序问题**：组件创建顺序复杂，容易出错

### 3. 维护困难
- **代码重复**：环境变量解析、配置验证等功能在多处实现
- **扩展性差**：添加新功能需要修改多个文件
- **测试复杂**：由于耦合度高，单元测试编写困难

## 分步骤重构方案

### 第一阶段：目录结构优化（低风险）

**目标**：重新组织文件结构，不改变功能实现

**步骤**：
1. 创建新的目录结构
2. 将现有文件按功能分类移动
3. 更新导入路径
4. 运行测试确保功能正常

**预期时间**：1-2小时
**风险等级**：低

### 第二阶段：接口抽象化（中风险）

**目标**：定义清晰的接口，降低组件耦合度

**步骤**：
1. 提取核心接口定义
2. 重构配置系统核心类
3. 实现依赖注入机制
4. 更新相关组件

**预期时间**：2-3小时
**风险等级**：中

### 第三阶段：功能模块化（中风险）

**目标**：将复杂功能拆分为独立模块

**步骤**：
1. 重构配置加载器
2. 重构配置处理器
3. 重构配置服务组件
4. 优化模型定义

**预期时间**：3-4小时
**风险等级**：中

### 第四阶段：测试和文档（低风险）

**目标**：完善测试覆盖和文档说明

**步骤**：
1. 编写单元测试
2. 更新API文档
3. 编写使用示例
4. 性能测试

**预期时间**：2-3小时
**风险等级**：低

## 详细执行计划

### 第一阶段：目录结构优化

#### 步骤1.1：创建新目录结构
```bash
# 创建新的目录结构
mkdir -p src/infrastructure/config/{loader,processor,service,migration,utils}
```

#### 步骤1.2：文件重分类
```python
# 将现有文件按功能分类移动
# 核心接口和基础类
mv src/infrastructure/config/core/interfaces.py src/infrastructure/config/interfaces.py
mv src/infrastructure/config/models/base.py src/infrastructure/config/base.py

# 加载器相关
mv src/infrastructure/config/core/loader.py src/infrastructure/config/loader/yaml_loader.py
mv src/infrastructure/config/utils/file_watcher.py src/infrastructure/config/loader/file_watcher.py

# 处理器相关
mv src/infrastructure/config/utils/inheritance.py src/infrastructure/config/processor/inheritance.py
mv src/infrastructure/config/core/merger.py src/infrastructure/config/processor/merger.py
mv src/infrastructure/config/utils/validator.py src/infrastructure/config/processor/validator.py
mv src/infrastructure/config/utils/env_resolver.py src/infrastructure/config/processor/env_resolver.py

# 服务相关
mv src/infrastructure/config/config_callback_manager.py src/infrastructure/config/service/callback_manager.py
mv src/infrastructure/config/error_recovery.py src/infrastructure/config/service/error_recovery.py
mv src/infrastructure/config/checkpoint_config_service.py src/infrastructure/config/service/checkpoint_service.py

# 迁移相关
mv src/infrastructure/config/config_migration.py src/infrastructure/config/migration/migrator.py

# 工具相关
mv src/infrastructure/config/utils/enhanced_validator.py src/infrastructure/config/utils/enhanced_validator.py
mv src/infrastructure/config/utils/redactor.py src/infrastructure/config/utils/redactor.py
mv src/infrastructure/config/utils/schema_loader.py src/infrastructure/config/utils/schema_loader.py
```

#### 步骤1.3：更新导入路径
```python
# 在每个移动的文件中更新导入路径
# 例如，在 yaml_loader.py 中：
# 从：from ...core.interfaces import IConfigLoader
# 到：from ...interfaces import IConfigLoader
```

#### 步骤1.4：创建新的__init__.py文件
```python
# src/infrastructure/config/__init__.py
from .config_system import ConfigSystem, IConfigSystem
from .config_factory import ConfigFactory
from .config_manager import ConfigManager
from .interfaces import *

# src/infrastructure/config/loader/__init__.py
from .yaml_loader import YamlConfigLoader
from .file_watcher import FileWatcher

# src/infrastructure/config/processor/__init__.py
from .inheritance import ConfigInheritanceHandler
from .merger import ConfigMerger
from .validator import ConfigValidator
from .env_resolver import EnvResolver

# src/infrastructure/config/service/__init__.py
from .callback_manager import ConfigCallbackManager
from .error_recovery import ConfigErrorRecovery
from .checkpoint_service import CheckpointConfigService
```

### 第二阶段：接口抽象化

#### 步骤2.1：定义核心接口
```python
# src/infrastructure/config/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

class IConfigLoader(ABC):
    """配置加载器接口"""
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载所有配置"""
        pass

class IConfigProcessor(ABC):
    """配置处理器接口"""
    
    @abstractmethod
    def process(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置"""
        pass

class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any], config_type: str) -> bool:
        """验证配置"""
        pass
```

#### 步骤2.2：重构配置系统
```python
# src/infrastructure/config/config_system.py
class ConfigSystem(IConfigSystem):
    def __init__(
        self,
        loader: IConfigLoader,
        processors: List[IConfigProcessor],
        validator: IConfigValidator
    ):
        self._loader = loader
        self._processors = processors
        self._validator = validator
        self._cache = {}
```

#### 步骤2.3：实现依赖注入
```python
# src/infrastructure/config/config_factory.py
class ConfigFactory:
    @staticmethod
    def create_config_system(base_path: str = "configs") -> IConfigSystem:
        # 创建组件
        loader = YamlConfigLoader(base_path)
        processors = [
            ConfigInheritanceHandler(),
            ConfigMerger(),
            EnvResolver()
        ]
        validator = ConfigValidator()
        
        # 创建配置系统
        return ConfigSystem(loader, processors, validator)
```

### 第三阶段：功能模块化

#### 步骤3.1：重构配置加载器
```python
# src/infrastructure/config/loader/yaml_loader.py
class YamlConfigLoader(IConfigLoader):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self._cache = {}
        self._file_watcher = FileWatcher(str(self.base_path))
    
    def load(self, config_path: str) -> Dict[str, Any]:
        # 简化加载逻辑，专注于文件读取
        full_path = self.base_path / config_path
        if not full_path.exists():
            raise ConfigurationError(f"配置文件不存在: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        # 缓存配置
        self._cache[config_path] = config
        return config
```

#### 步骤3.2：重构配置处理器
```python
# src/infrastructure/config/processor/inheritance.py
class ConfigInheritanceProcessor(IConfigProcessor):
    def __init__(self):
        self._inheritance_handler = ConfigInheritanceHandler()
    
    def process(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # 处理继承关系
        if 'inherits_from' in config:
            return self._inheritance_handler.resolve_inheritance(config)
        return config
```

#### 步骤3.3：重构配置服务
```python
# src/infrastructure/config/service/callback_manager.py
class ConfigCallbackService:
    def __init__(self):
        self._callbacks = {}
        self._execution_history = []
    
    def register_callback(self, callback_id: str, callback: Callable, priority: int = 50):
        self._callbacks[callback_id] = {
            'callback': callback,
            'priority': priority,
            'enabled': True
        }
```

### 第四阶段：测试和文档

#### 步骤4.1：编写单元测试
```python
# tests/test_config_system.py
class TestConfigSystem:
    def test_load_config(self):
        # 测试配置加载
        config_system = ConfigFactory.create_config_system()
        config = config_system.load_config("test.yaml")
        assert config is not None
    
    def test_config_validation(self):
        # 测试配置验证
        config_system = ConfigFactory.create_config_system()
        result = config_system.validate_config({"test": "value"}, "test")
        assert result is True
```

#### 步骤4.2：更新文档
```markdown
# 配置系统重构文档

## 概述
配置系统负责管理应用程序的所有配置，支持配置文件加载、验证、继承、合并等功能。

## 架构设计
- **配置系统 (ConfigSystem)**：核心配置管理器
- **配置加载器 (ConfigLoader)**：负责配置文件加载
- **配置处理器 (ConfigProcessor)**：处理配置继承、合并等
- **配置验证器 (ConfigValidator)**：验证配置有效性
- **配置服务 (ConfigService)**：提供高级配置服务

## 使用示例
```python
from src.infrastructure.config import ConfigFactory

# 创建配置系统
config_system = ConfigFactory.create_config_system()

# 加载配置
config = config_system.load_config("global.yaml")

# 验证配置
is_valid = config_system.validate_config(config, "global")
```
```

## 执行优先级和时间安排

### 立即执行（今天）
1. **第一阶段**：目录结构优化（1-2小时）
2. **创建重构文档**：记录重构过程和结果（30分钟）

### 近期执行（本周）
1. **第二阶段**：接口抽象化（2-3小时）
2. **第三阶段**：功能模块化（3-4小时）

### 后续执行（下周）
1. **第四阶段**：测试和文档（2-3小时）
2. **性能优化**：根据测试结果进行优化（1-2小时）

## 风险控制措施

1. **备份策略**：每次重构前创建代码备份
2. **增量重构**：分阶段进行，每阶段完成后验证功能
3. **测试验证**：每个阶段都有对应的测试用例
4. **回滚机制**：保留原始实现，便于回滚

## 成功标准

1. **功能完整性**：重构后所有原有功能正常工作
2. **代码质量**：代码结构清晰，耦合度降低
3. **可维护性**：添加新功能更加容易
4. **测试覆盖**：单元测试覆盖率达到90%以上
