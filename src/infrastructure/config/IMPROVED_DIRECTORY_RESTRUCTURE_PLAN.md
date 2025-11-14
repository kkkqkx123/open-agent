# 配置系统目录重组计划（改进版）

## 目标目录结构

```
src/infrastructure/config/
├── contracts/                      # 契约层：接口和类型定义
│   ├── interfaces.py              # 从 config_interfaces.py 重命名
│   └── types.py                   # 新增：配置相关类型定义
├── loaders/                        # 加载层：配置获取和解析
│   ├── yaml_loader.py             # 从 config_loader.py 重命名
│   ├── inheritance_handler.py     # 从 config_inheritance.py 重命名
│   └── env_resolver.py            # 新增：环境变量解析器
├── processors/                     # 处理层：配置转换和验证
│   ├── config_merger.py           # 从 config_merger.py 重命名
│   ├── base_validator.py          # 从 config_validator.py 重命名
│   └── enhanced_validator.py      # 从 enhanced_validator.py 重命名
├── system/                         # 系统层：核心协调和管理
│   ├── config_system.py           # 从 config_system.py 重命名
│   ├── config_manager.py          # 从 config_manager.py 重命名
│   └── service_factory.py         # 从 config_service_factory.py 重命名
├── monitoring/                     # 监控层：变更监控和错误处理
│   ├── callback_manager.py        # 从 config_callback_manager.py 重命名
│   └── error_recovery.py          # 保持不变
├── tools/                          # 工具层：辅助工具和应用
│   ├── migration_tool.py          # 从 config_migration.py 重命名
│   └── validator_tool.py          # 从 config_validator_tool.py 重命名
├── tests/                          # 测试层
│   └── test_config_refactoring.py # 从 test_config_refactoring.py 重命名
└── models/                         # 模型层：配置数据模型（已存在）
    ├── global_config.py
    ├── llm_config.py
    ├── agent_config.py
    ├── tool_config.py
    ├── token_counter_config.py
    └── ...
```

## 目录职责说明

### 1. contracts/ - 契约层
**职责**: 定义配置系统的接口、类型和契约
**特点**: 
- 纯抽象定义，不包含具体实现
- 被所有其他层依赖
- 变更频率最低

### 2. loaders/ - 加载层
**职责**: 负责配置的获取、加载和初步解析
**特点**:
- 处理文件I/O操作
- 解析配置格式（YAML、JSON等）
- 处理环境变量和继承关系

### 3. processors/ - 处理层
**职责**: 负责配置的转换、合并和验证
**特点**:
- 纯数据处理，不涉及I/O
- 可组合使用
- 易于单元测试

### 4. system/ - 系统层
**职责**: 提供配置系统的核心协调和管理功能
**特点**:
- 协调各层组件
- 提供统一的外部接口
- 管理配置生命周期

### 5. monitoring/ - 监控层
**职责**: 监控配置变更和处理错误恢复
**特点**:
- 横切关注点
- 可选功能
- 独立运行

### 6. tools/ - 工具层
**职责**: 提供配置相关的工具和应用
**特点**:
- 独立可执行
- 特定用途
- 用户交互

## 文件移动清单

### 需要移动的文件
1. `config_interfaces.py` → `contracts/interfaces.py`
2. `config_merger.py` → `processors/config_merger.py`
3. `config_loader.py` → `loaders/yaml_loader.py`
4. `config_inheritance.py` → `loaders/inheritance_handler.py`
5. `config_validator.py` → `processors/base_validator.py`
6. `enhanced_validator.py` → `processors/enhanced_validator.py`
7. `config_callback_manager.py` → `monitoring/callback_manager.py`
8. `error_recovery.py` → `monitoring/error_recovery.py`
9. `config_system.py` → `system/config_system.py`
10. `config_migration.py` → `tools/migration_tool.py`
11. `config_validator_tool.py` → `tools/validator_tool.py`
12. `config_manager.py` → `system/config_manager.py`
13. `config_service_factory.py` → `system/service_factory.py`
14. `test_config_refactoring.py` → `tests/test_config_refactoring.py`

### 需要创建的新文件
1. `contracts/types.py` - 配置相关类型定义
2. `loaders/env_resolver.py` - 环境变量解析器（从config_loader.py中提取）

### 需要特殊处理的文件
- `checkpoint_config_service.py` → 移动到 `src/infrastructure/checkpoint/` 目录

## 导入更新映射表

### 内部导入更新
| 原导入路径 | 新导入路径 |
|-----------|-----------|
| `from .config_interfaces import` | `from .contracts.interfaces import` |
| `from .config_merger import` | `from .processors.config_merger import` |
| `from .config_loader import` | `from .loaders.yaml_loader import` |
| `from .config_inheritance import` | `from .loaders.inheritance_handler import` |
| `from .config_validator import` | `from .processors.base_validator import` |
| `from .enhanced_validator import` | `from .processors.enhanced_validator import` |
| `from .config_callback_manager import` | `from .monitoring.callback_manager import` |
| `from .error_recovery import` | `from .monitoring.error_recovery import` |
| `from .config_system import` | `from .system.config_system import` |
| `from .config_manager import` | `from .system.config_manager import` |
| `from .config_service_factory import` | `from .system.service_factory import` |
| `from .config_migration import` | `from .tools.migration_tool import` |
| `from .config_validator_tool import` | `from .tools.validator_tool import` |

### 外部导入更新
需要搜索整个项目，找到所有引用配置系统的文件：
```bash
# 搜索模式
from .config_*
from ..config.config_*
from src.infrastructure.config.config_*
```

## 执行步骤

### 第一步：创建目录结构
```bash
mkdir -p src/infrastructure/config/contracts
mkdir -p src/infrastructure/config/loaders  
mkdir -p src/infrastructure/config/processors
mkdir -p src/infrastructure/config/system
mkdir -p src/infrastructure/config/monitoring
mkdir -p src/infrastructure/config/tools
mkdir -p src/infrastructure/config/tests
mkdir -p src/infrastructure/checkpoint  # 用于 checkpoint_config_service.py
```

### 第二步：按层次移动文件

#### 2.1 移动契约层
```bash
mv src/infrastructure/config/config_interfaces.py src/infrastructure/config/contracts/interfaces.py
# 创建 types.py 文件
```

#### 2.2 移动加载层
```bash
mv src/infrastructure/config/config_loader.py src/infrastructure/config/loaders/yaml_loader.py
mv src/infrastructure/config/config_inheritance.py src/infrastructure/config/loaders/inheritance_handler.py
# 从 yaml_loader.py 中提取环境变量解析逻辑到 env_resolver.py
```

#### 2.3 移动处理层
```bash
mv src/infrastructure/config/config_merger.py src/infrastructure/config/processors/config_merger.py
mv src/infrastructure/config/config_validator.py src/infrastructure/config/processors/base_validator.py
mv src/infrastructure/config/enhanced_validator.py src/infrastructure/config/processors/enhanced_validator.py
```

#### 2.4 移动系统层
```bash
mv src/infrastructure/config/config_system.py src/infrastructure/config/system/config_system.py
mv src/infrastructure/config/config_manager.py src/infrastructure/config/system/config_manager.py
mv src/infrastructure/config/config_service_factory.py src/infrastructure/config/system/service_factory.py
```

#### 2.5 移动监控层
```bash
mv src/infrastructure/config/config_callback_manager.py src/infrastructure/config/monitoring/callback_manager.py
mv src/infrastructure/config/error_recovery.py src/infrastructure/config/monitoring/error_recovery.py
```

#### 2.6 移动工具层
```bash
mv src/infrastructure/config/config_migration.py src/infrastructure/config/tools/migration_tool.py
mv src/infrastructure/config/config_validator_tool.py src/infrastructure/config/tools/validator_tool.py
```

#### 2.7 移动测试文件
```bash
mv src/infrastructure/config/test_config_refactoring.py src/infrastructure/config/tests/test_config_refactoring.py
```

#### 2.8 移动领域特定服务
```bash
mv src/infrastructure/config/checkpoint_config_service.py src/infrastructure/checkpoint/checkpoint_config_service.py
```

### 第三步：更新导入
1. 更新移动文件内部的相对导入
2. 更新外部文件的导入路径
3. 运行测试确保没有破坏性更改

### 第四步：验证
1. 运行单元测试
2. 运行集成测试
3. 检查应用程序启动是否正常

## 新增文件内容

### contracts/types.py
```python
"""配置系统类型定义

定义配置系统中使用的通用类型。
"""

from typing import Dict, Any, Optional, Union, List
from enum import Enum

# 配置值类型
ConfigValue = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

# 配置路径类型
ConfigPath = str

# 配置环境类型
class ConfigEnvironment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

# 配置格式类型
class ConfigFormat(Enum):
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"
    INI = "ini"
```

### loaders/env_resolver.py
```python
"""环境变量解析器

从 config_loader.py 中提取的环境变量解析逻辑。
"""

import os
import re
from typing import Any, Dict

from ..exceptions import ConfigurationError


class EnvResolver:
    """环境变量解析器"""
    
    def __init__(self, prefix: str = ""):
        """初始化环境变量解析器
        
        Args:
            prefix: 环境变量前缀
        """
        self.prefix = prefix
        self._env_var_pattern = re.compile(r"\$\{([^}]+)\}")
    
    def resolve(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的环境变量
        
        Args:
            config: 配置字典
            
        Returns:
            解析后的配置字典
        """
        def _resolve_recursive(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: _resolve_recursive(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_resolve_recursive(item) for item in value]
            elif isinstance(value, str):
                return self._resolve_env_var_string(value)
            else:
                return value
        
        result = _resolve_recursive(config)
        return result
    
    def _resolve_env_var_string(self, text: str) -> str:
        """解析字符串中的环境变量"""
        def replace_env_var(match: Any) -> str:
            var_expr = match.group(1)
            
            # 检查是否包含默认值
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                # 普通环境变量
                var_name = var_expr.strip()
                value = os.getenv(var_name)
                if value is None:
                    raise ConfigurationError(f"环境变量未定义: {var_name}")
                return value
        
        return self._env_var_pattern.sub(replace_env_var, text)
```

## 注意事项

1. **备份**: 在开始移动文件之前，建议创建当前代码的备份
2. **IDE支持**: 使用支持重命名的IDE可以自动更新大部分导入
3. **测试**: 每移动一个文件后，立即运行相关测试确保功能正常
4. **分批执行**: 建议按层次分批移动文件，便于问题定位
5. **文档更新**: 移动完成后更新相关文档

## 预期收益

1. **更清晰的职责分离**: 每个目录都有明确的职责
2. **更好的可维护性**: 相关功能聚集在一起
3. **更容易扩展**: 新功能可以很容易地找到合适的目录
4. **更好的开发体验**: 开发者可以快速定位相关代码
5. **更强的类型安全**: 通过专门的类型定义文件提高类型安全性