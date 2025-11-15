# 配置工具类拆分实现示例

本文档提供了将配置系统中的功能拆分为独立工具类的具体实现示例。

## 示例1: 环境变量解析工具类 (EnvResolver)

### 1. 创建独立工具类

**文件路径**: `src/infrastructure/tools/env_resolver.py`

```python
"""环境变量解析工具

提供通用的环境变量解析功能，可被多个模块使用。
"""

import os
import re
from typing import Any, Dict, Union, Optional


class EnvResolver:
    """环境变量解析器
    
    提供环境变量的解析、获取、设置和管理功能。
    支持变量前缀和默认值。
    """

    def __init__(self, prefix: str = ""):
        """初始化环境变量解析器

        Args:
            prefix: 环境变量前缀
        """
        self.prefix = prefix
        self.env_var_pattern = re.compile(r"\$\{([^}]+)\}")
        self.env_var_default_pattern = re.compile(r"\$\{([^:]+):([^}]*)\}")

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
                return self._resolve_string(value)
            else:
                return value

        result = _resolve_recursive(config)
        # 确保返回类型是 Dict[str, Any]
        assert isinstance(result, dict)
        return result

    def _resolve_string(self, text: str) -> str:
        """解析字符串中的环境变量

        Args:
            text: 包含环境变量的字符串

        Returns:
            解析后的字符串
        """

        def replace_env_var(match: re.Match) -> str:
            var_expr = match.group(1)

            # 检查是否包含默认值
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                # 添加前缀
                full_var_name = f"{self.prefix}{var_name}" if self.prefix else var_name
                return os.getenv(full_var_name, default_value)
            else:
                # 普通环境变量
                full_var_name = f"{self.prefix}{var_expr}" if self.prefix else var_expr
                value = os.getenv(full_var_name)
                return value if value is not None else ""

        # 使用正则表达式替换所有环境变量
        return self.env_var_pattern.sub(replace_env_var, text)

    def get_env_var(self, name: str, default: Optional[str] = None) -> str:
        """获取环境变量

        Args:
            name: 变量名
            default: 默认值

        Returns:
            环境变量值或默认值
        """
        full_name = f"{self.prefix}{name}" if self.prefix else name
        result = os.getenv(full_name, default)
        return result if result is not None else ""

    def set_env_var(self, name: str, value: str) -> None:
        """设置环境变量

        Args:
            name: 变量名
            value: 变量值
        """
        full_name = f"{self.prefix}{name}" if self.prefix else name
        os.environ[full_name] = value

    def has_env_var(self, name: str) -> bool:
        """检查环境变量是否存在

        Args:
            name: 变量名

        Returns:
            是否存在
        """
        full_name = f"{self.prefix}{name}" if self.prefix else name
        return full_name in os.environ

    def list_env_vars(self, pattern: Optional[str] = None) -> Dict[str, str]:
        """列出环境变量

        Args:
            pattern: 匹配模式（可选）

        Returns:
            环境变量字典
        """
        result = {}
        prefix_pattern = f"^{self.prefix}" if self.prefix else "^"

        for key, value in os.environ.items():
            # 检查是否匹配前缀
            if not re.match(prefix_pattern, key):
                continue

            # 检查是否匹配模式
            if pattern and not re.search(pattern, key):
                continue

            # 移除前缀
            display_key = key[len(self.prefix) :] if self.prefix else key
            result[display_key] = value

        return result

    def clear_env_vars(self, pattern: Optional[str] = None) -> None:
        """清除环境变量

        Args:
            pattern: 匹配模式（可选）
        """
        prefix_pattern = f"^{self.prefix}" if self.prefix else "^"
        keys_to_remove = []

        for key in os.environ:
            # 检查是否匹配前缀
            if not re.match(prefix_pattern, key):
                continue

            # 检查是否匹配模式
            if pattern and not re.search(pattern, key):
                continue

            keys_to_remove.append(key)

        for key in keys_to_remove:
            del os.environ[key]
```

### 2. 更新配置系统以使用独立工具类

**文件路径**: `src/infrastructure/config/config_system.py`

```python
# 在文件顶部添加导入
from ..tools.env_resolver import EnvResolver

# 在ConfigSystem类中更新使用方式
class ConfigSystem(IConfigSystem):
    def __init__(self, ...):
        # ... 其他初始化代码 ...
        
        # 环境变量解析器 - 使用独立的工具类
        self._env_resolver: Optional[EnvResolver] = None
        
        # ... 其他初始化代码 ...

    def get_env_resolver(self) -> EnvResolver:
        """获取环境变量解析器

        Returns:
            环境变量解析器
        """
        if self._env_resolver is None:
            # 加载全局配置以获取环境变量前缀
            global_config = self.load_global_config()
            self._env_resolver = EnvResolver(global_config.env_prefix)

        return self._env_resolver
```

### 3. 创建工具类的工厂

**文件路径**: `src/infrastructure/tools/__init__.py`

```python
"""工具模块

提供各种通用工具类，可被多个模块使用。
"""

from .env_resolver import EnvResolver
from .config_merger import ConfigMerger
from .redactor import Redactor
from .file_watcher import FileWatcher
from .validator import Validator
from .cache import Cache
from .backup_manager import BackupManager
from .inheritance_handler import InheritanceHandler
from .schema_loader import SchemaLoader
from .config_operations import ConfigOperations

__all__ = [
    "EnvResolver",
    "ConfigMerger",
    "Redactor",
    "FileWatcher",
    "Validator",
    "Cache",
    "BackupManager",
    "InheritanceHandler",
    "SchemaLoader",
    "ConfigOperations",
]


class ToolFactory:
    """工具工厂
    
    提供创建各种工具实例的便捷方法。
    """
    
    @staticmethod
    def create_env_resolver(prefix: str = "") -> EnvResolver:
        """创建环境变量解析器
        
        Args:
            prefix: 环境变量前缀
            
        Returns:
            环境变量解析器实例
        """
        return EnvResolver(prefix)
    
    @staticmethod
    def create_config_merger() -> ConfigMerger:
        """创建配置合并器
        
        Returns:
            配置合并器实例
        """
        return ConfigMerger()
    
    @staticmethod
    def create_redactor(patterns: Optional[list] = None, replacement: str = "***") -> Redactor:
        """创建敏感信息脱敏器
        
        Args:
            patterns: 敏感信息模式列表
            replacement: 替换字符串
            
        Returns:
            敏感信息脱敏器实例
        """
        return Redactor(patterns, replacement)
    
    # ... 其他工具的创建方法 ...
```

## 示例2: 配置合并工具类 (ConfigMerger)

### 1. 创建独立工具类

**文件路径**: `src/infrastructure/tools/config_merger.py`

```python
"""配置合并工具

提供通用的字典合并功能，可被多个模块使用。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IConfigMerger(ABC):
    """配置合并器接口"""

    @abstractmethod
    def merge_group_config(
        self, group_config: Dict[str, Any], individual_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并组配置和个体配置

        Args:
            group_config: 组配置
            individual_config: 个体配置

        Returns:
            合并后的配置
        """
        pass

    @abstractmethod
    def deep_merge(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并两个字典

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            合并后的字典
        """
        pass


class ConfigMerger(IConfigMerger):
    """配置合并器实现
    
    提供多种合并策略，包括深度合并、组配置合并等。
    """

    def merge_group_config(
        self, group_config: Dict[str, Any], individual_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并组配置和个体配置

        Args:
            group_config: 组配置
            individual_config: 个体配置

        Returns:
            合并后的配置
        """
        # 先深度合并配置
        result = self.deep_merge(group_config.copy(), individual_config)

        # 对于特定字段，个体配置应该完全覆盖组配置而不是合并
        override_fields = ["tools", "tool_sets"]  # 这些字段个体配置优先
        for field in override_fields:
            if field in individual_config:
                result[field] = individual_config[field]

        # 移除组标识字段，因为它已经完成了合并任务
        if "group" in result:
            del result["group"]

        return result

    def deep_merge(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并两个字典

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            合并后的字典
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    # 递归合并嵌套字典
                    result[key] = self.deep_merge(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # 合并列表，去重
                    result[key] = self._merge_lists(result[key], value)
                else:
                    # 直接覆盖
                    result[key] = value
            else:
                result[key] = value

        return result

    def _merge_lists(self, list1: List[Any], list2: List[Any]) -> List[Any]:
        """合并两个列表，去重

        Args:
            list1: 第一个列表
            list2: 第二个列表

        Returns:
            合并后的列表
        """
        result = list1.copy()

        for item in list2:
            if item not in result:
                result.append(item)

        return result

    def merge_multiple_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个配置

        Args:
            configs: 配置列表

        Returns:
            合并后的配置
        """
        if not configs:
            return {}

        result = configs[0].copy()

        for config in configs[1:]:
            result = self.deep_merge(result, config)

        return result

    def merge_configs_by_priority(
        self, configs: List[Dict[str, Any]], priority_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """按优先级合并配置

        Args:
            configs: 配置列表
            priority_keys: 优先级键列表，第一个配置中的优先级键会保留

        Returns:
            合并后的配置
        """
        if not configs:
            return {}

        # 如果没有指定优先级键，使用所有键
        if not priority_keys:
            return self.merge_multiple_configs(configs)

        result = {}

        # 先处理优先级键（只从第一个配置中获取）
        if configs:
            for key in priority_keys:
                if key in configs[0]:
                    result[key] = configs[0][key]

        # 然后合并所有配置的非优先级键
        for config in configs:
            for key, value in config.items():
                if key not in priority_keys:
                    if key in result:
                        if isinstance(result[key], dict) and isinstance(value, dict):
                            result[key] = self.deep_merge(result[key], value)
                        elif isinstance(result[key], list) and isinstance(value, list):
                            result[key] = self._merge_lists(result[key], value)
                        else:
                            result[key] = value
                    else:
                        result[key] = value

        return result

    def extract_differences(
        self, config1: Dict[str, Any], config2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取两个配置的差异

        Args:
            config1: 第一个配置
            config2: 第二个配置

        Returns:
            差异字典
        """
        differences = {}

        # 检查config2中有但config1中没有的键
        for key, value in config2.items():
            if key not in config1:
                differences[key] = {"added": value}
            elif isinstance(value, dict) and isinstance(config1[key], dict):
                # 递归检查嵌套字典
                nested_diff = self.extract_differences(config1[key], value)
                if nested_diff:
                    differences[key] = nested_diff
            elif value != config1[key]:
                differences[key] = {"old": config1[key], "new": value}

        # 检查config1中有但config2中没有的键
        for key in config1:
            if key not in config2:
                differences[key] = {"removed": config1[key]}

        return differences
```

### 2. 更新配置系统以使用独立工具类

**文件路径**: `src/infrastructure/config/config_system.py`

```python
# 在文件顶部添加导入
from ..tools.config_merger import ConfigMerger

# 在ConfigSystem类中更新使用方式
class ConfigSystem(IConfigSystem):
    def __init__(self, ...):
        # ... 其他初始化代码 ...
        
        # 配置合并器 - 使用独立的工具类
        self._config_merger = ConfigMerger()
        
        # ... 其他初始化代码 ...
```

## 迁移策略

### 1. 渐进式迁移

1. **第一阶段**: 创建独立的工具类，但保留原有实现
2. **第二阶段**: 更新配置系统以使用新的工具类
3. **第三阶段**: 移除原有实现，完成迁移

### 2. 向后兼容性

```python
# 在原有位置创建适配器，确保向后兼容
# 文件: src/infrastructure/config/processor/env_resolver.py

from ...tools.env_resolver import EnvResolver as ToolsEnvResolver

# 为了向后兼容，保留原有导入
class EnvResolver(ToolsEnvResolver):
    """环境变量解析器 - 向后兼容适配器"""
    pass
```

### 3. 测试策略

1. 为每个工具类编写独立的单元测试
2. 确保配置系统的集成测试仍然通过
3. 添加新的集成测试验证工具类的独立性

## 总结

通过将配置系统中的功能拆分为独立的工具类，我们可以：

1. **提高代码复用性**: 工具类可以被多个模块使用
2. **降低耦合度**: 减少模块间的依赖关系
3. **增强可测试性**: 独立的工具类更容易测试
4. **促进模块化**: 整个系统的架构更加清晰

这种拆分方式不仅适用于配置系统，也可以应用到系统的其他部分，从而提高整个项目的代码质量和可维护性。