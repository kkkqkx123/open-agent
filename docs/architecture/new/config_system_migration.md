# 配置系统迁移设计方案

## 1. 现有配置系统分析

### 1.1 当前配置系统结构

```
src/infrastructure/config/
├── interfaces.py              # 配置系统接口定义
├── base.py                   # 基础配置模型
├── config_loader.py          # 配置加载器
├── config_system.py          # 配置系统主类
├── config_cache.py           # 配置缓存
├── models/                   # 配置模型
│   ├── llm_config.py        # LLM配置模型
│   ├── tool_config.py       # 工具配置模型
│   ├── global_config.py     # 全局配置模型
│   └── ...
├── loader/                   # 加载器实现
│   └── file_config_loader.py
├── processor/                # 配置处理器
│   ├── validator.py
│   └── enhanced_validator.py
├── utils/                    # 配置工具
│   ├── inheritance_handler.py
│   ├── config_operations.py
│   └── redactor.py
└── service/                  # 配置服务
    ├── config_factory.py
    └── checkpoint_service.py
```

### 1.2 现有问题分析

1. **职责分散**：配置相关功能分散在多个子目录中
2. **单一文件职责过重**：如`config_loader.py`包含了加载、继承、验证等多种功能
3. **模块间耦合**：配置模型与加载器、处理器之间存在紧密耦合
4. **扩展性不足**：添加新的配置类型需要修改多个文件

### 1.3 核心功能识别

1. **配置加载**：从文件系统加载配置
2. **配置继承**：处理配置间的继承关系
3. **配置合并**：合并多个配置源
4. **配置验证**：验证配置的正确性
5. **环境变量解析**：解析配置中的环境变量
6. **配置缓存**：缓存已加载的配置
7. **配置监听**：监听配置文件变化

## 2. 新配置系统架构设计

### 2.1 设计原则

1. **单一职责**：每个类只负责一个特定功能
2. **开闭原则**：对扩展开放，对修改封闭
3. **依赖倒置**：依赖抽象而非具体实现
4. **组合优于继承**：使用组合来构建复杂功能

### 2.2 新架构结构

```
src/core/config/
├── __init__.py
├── base/                     # 基础组件
│   ├── __init__.py
│   ├── interfaces.py         # 核心接口定义
│   ├── base_config.py        # 基础配置模型
│   └── exceptions.py         # 配置异常定义
├── loader/                   # 加载器组件
│   ├── __init__.py
│   ├── config_loader.py      # 配置加载器接口
│   ├── file_loader.py        # 文件加载器实现
│   └── cache_loader.py       # 缓存加载器装饰器
├── processor/                # 处理器组件
│   ├── __init__.py
│   ├── inheritance_processor.py  # 继承处理器
│   ├── merger.py             # 配置合并器
│   ├── validator.py          # 配置验证器
│   └── env_resolver.py       # 环境变量解析器
├── models/                   # 配置模型
│   ├── __init__.py
│   ├── llm_config.py         # LLM配置模型
│   ├── tool_config.py        # 工具配置模型
│   ├── tool_set_config.py    # 工具集配置模型
│   └── global_config.py      # 全局配置模型
├── manager/                  # 管理器组件
│   ├── __init__.py
│   ├── config_manager.py     # 配置管理器
│   └── registry.py           # 配置注册表
└── watcher/                  # 监听器组件
    ├── __init__.py
    ├── file_watcher.py       # 文件监听器
    └── change_handler.py     # 变化处理器
```

### 2.3 核心组件设计

#### 2.3.1 基础接口定义

```python
# src/core/config/base/interfaces.py
"""
配置系统核心接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

class IConfigLoader(ABC):
    """配置加载器接口"""
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    def exists(self, config_path: str) -> bool:
        """检查配置是否存在"""
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
    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证配置"""
        pass

class IConfigMerger(ABC):
    """配置合并器接口"""
    
    @abstractmethod
    def merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        pass

class IConfigWatcher(ABC):
    """配置监听器接口"""
    
    @abstractmethod
    def watch(self, config_path: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """监听配置变化"""
        pass
    
    @abstractmethod
    def stop_watching(self, config_path: str) -> None:
        """停止监听"""
        pass
```

#### 2.3.2 基础配置模型

```python
# src/core/config/base/base_config.py
"""
基础配置模型
"""

from abc import ABC
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class BaseConfig(BaseModel, ABC):
    """基础配置模型"""
    
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseConfig":
        """从字典创建配置"""
        return cls(**data)
    
    def merge(self, other: "BaseConfig") -> "BaseConfig":
        """与另一个配置合并"""
        current_dict = self.to_dict()
        other_dict = other.to_dict()
        merged = self._deep_merge(current_dict, other_dict)
        return self.__class__.from_dict(merged)
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
```

#### 2.3.3 配置加载器

```python
# src/core/config/loader/config_loader.py
"""
配置加载器接口和基础实现
"""

from typing import Dict, Any, Optional
from ..base.interfaces import IConfigLoader

class ConfigLoader(IConfigLoader):
    """配置加载器基础实现"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """初始化配置加载器
        
        Args:
            base_path: 配置基础路径
        """
        self.base_path = base_path or Path("configs")
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置数据
        """
        full_path = self._resolve_path(config_path)
        return self._load_from_file(full_path)
    
    def exists(self, config_path: str) -> bool:
        """检查配置是否存在
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            是否存在
        """
        full_path = self._resolve_path(config_path)
        return full_path.exists()
    
    def _resolve_path(self, config_path: str) -> Path:
        """解析配置文件路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            完整路径
        """
        path = Path(config_path)
        if path.is_absolute():
            return path
        
        full_path = self.base_path / path
        if not full_path.suffix:
            full_path = full_path.with_suffix(".yaml")
        
        return full_path
    
    def _load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """从文件加载配置
        
        Args:
            file_path: 文件路径
            
        Returns:
            配置数据
        """
        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            import yaml
            return yaml.safe_load(f) or {}
```

#### 2.3.4 配置处理器

```python
# src/core/config/processor/inheritance_processor.py
"""
配置继承处理器
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from ..base.interfaces import IConfigProcessor, IConfigLoader

class InheritanceProcessor(IConfigProcessor):
    """配置继承处理器"""
    
    def __init__(self, config_loader: IConfigLoader):
        """初始化继承处理器
        
        Args:
            config_loader: 配置加载器
        """
        self.config_loader = config_loader
    
    def process(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置继承
        
        Args:
            config: 原始配置
            
        Returns:
            处理后的配置
        """
        inherits_from = config.get("inherits_from")
        if not inherits_from:
            return config
        
        # 加载父配置
        parent_config = self._load_parent_config(inherits_from)
        
        # 合并配置
        merged = self._merge_configs(parent_config, config)
        
        # 递归处理继承链
        return self.process(merged)
    
    def _load_parent_config(self, inherits_from: Union[str, List[str]]) -> Dict[str, Any]:
        """加载父配置
        
        Args:
            inherits_from: 继承的配置路径或路径列表
            
        Returns:
            父配置
        """
        if isinstance(inherits_from, str):
            inherits_from = [inherits_from]
        
        parent_config = {}
        for parent_path in inherits_from:
            try:
                loaded_config = self.config_loader.load(parent_path)
                parent_config = self._merge_configs(parent_config, loaded_config)
            except FileNotFoundError:
                # 如果父配置不存在，跳过
                continue
        
        return parent_config
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            合并后的配置
        """
        result = base.copy()
        for key, value in override.items():
            if key == "inherits_from":
                continue  # 跳过继承字段
            
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
```

#### 2.3.5 配置合并器

```python
# src/core/config/processor/merger.py
"""
配置合并器
"""

from typing import Dict, Any, List
from ..base.interfaces import IConfigMerger

class ConfigMerger(IConfigMerger):
    """配置合并器实现"""
    
    def merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            合并后的配置
        """
        return self.deep_merge(base, override)
    
    def deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典
        
        Args:
            dict1: 第一个字典
            dict2: 第二个字典
            
        Returns:
            合并后的字典
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key] = self._merge_lists(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _merge_lists(self, list1: List[Any], list2: List[Any]) -> List[Any]:
        """合并列表，去重
        
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
```

#### 2.3.6 环境变量解析器

```python
# src/core/config/processor/env_resolver.py
"""
环境变量解析器
"""

import os
import re
from typing import Dict, Any
from ..base.interfaces import IConfigProcessor

class EnvResolver(IConfigProcessor):
    """环境变量解析器"""
    
    def __init__(self):
        """初始化环境变量解析器"""
        self.env_pattern = re.compile(r"\$\{([^}]+)\}")
    
    def process(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的环境变量
        
        Args:
            config: 原始配置
            
        Returns:
            解析后的配置
        """
        return self._resolve_recursive(config)
    
    def _resolve_recursive(self, obj: Any) -> Any:
        """递归解析环境变量
        
        Args:
            obj: 要解析的对象
            
        Returns:
            解析后的对象
        """
        if isinstance(obj, dict):
            return {k: self._resolve_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._resolve_env_string(obj)
        else:
            return obj
    
    def _resolve_env_string(self, text: str) -> str:
        """解析字符串中的环境变量
        
        Args:
            text: 包含环境变量的字符串
            
        Returns:
            解析后的字符串
        """
        def replace_env_var(match):
            var_expr = match.group(1)
            
            # 检查是否包含默认值
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                var_name = var_expr.strip()
                value = os.getenv(var_name)
                if value is None:
                    raise ValueError(f"环境变量未定义: {var_name}")
                return value
        
        return self.env_pattern.sub(replace_env_var, text)
```

#### 2.3.7 配置验证器

```python
# src/core/config/processor/validator.py
"""
配置验证器
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, ValidationError
from ..base.interfaces import IConfigValidator

class ConfigValidator(IConfigValidator):
    """配置验证器实现"""
    
    def __init__(self):
        """初始化配置验证器"""
        self._schemas: Dict[str, Type[BaseModel]] = {}
    
    def register_schema(self, config_type: str, schema: Type[BaseModel]) -> None:
        """注册配置模式
        
        Args:
            config_type: 配置类型
            schema: 配置模式
        """
        self._schemas[config_type] = schema
    
    def validate(self, config: Dict[str, Any], schema: Optional[Type[BaseModel]] = None) -> tuple[bool, List[str]]:
        """验证配置
        
        Args:
            config: 配置数据
            schema: 配置模式（可选）
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        # 如果提供了模式，使用它验证
        if schema:
            try:
                schema.model_validate(config)
            except ValidationError as e:
                errors.extend([str(err) for err in e.errors()])
        
        # 执行自定义验证
        errors.extend(self._custom_validate(config))
        
        return len(errors) == 0, errors
    
    def _custom_validate(self, config: Dict[str, Any]) -> List[str]:
        """自定义验证
        
        Args:
            config: 配置数据
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 检查必要字段
        required_fields = config.get("_required_fields", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必要字段: {field}")
        
        return errors
```

#### 2.3.8 配置管理器

```python
# src/core/config/manager/config_manager.py
"""
配置管理器
"""

from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from ..base.interfaces import IConfigLoader, IConfigProcessor, IConfigWatcher
from ..loader.config_loader import ConfigLoader
from ..processor.inheritance_processor import InheritanceProcessor
from ..processor.merger import ConfigMerger
from ..processor.env_resolver import EnvResolver
from ..processor.validator import ConfigValidator
from ..watcher.file_watcher import FileWatcher

class ConfigManager:
    """配置管理器 - 整合所有配置功能"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """初始化配置管理器
        
        Args:
            base_path: 配置基础路径
        """
        # 初始化组件
        self.loader = ConfigLoader(base_path)
        self.inheritance_processor = InheritanceProcessor(self.loader)
        self.merger = ConfigMerger()
        self.env_resolver = EnvResolver()
        self.validator = ConfigValidator()
        self.watcher = FileWatcher()
        
        # 处理器管道
        self.processors: List[IConfigProcessor] = [
            self.inheritance_processor,
            self.env_resolver,
        ]
        
        # 配置缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load_config(self, config_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型（可选）
            
        Returns:
            配置数据
        """
        # 检查缓存
        cache_key = f"{config_path}:{config_type or ''}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 加载配置
        config = self.loader.load(config_path)
        
        # 处理配置
        for processor in self.processors:
            config = processor.process(config)
        
        # 验证配置
        if config_type:
            is_valid, errors = self.validator.validate(config)
            if not is_valid:
                raise ValueError(f"配置验证失败: {errors}")
        
        # 缓存配置
        self._cache[cache_key] = config
        
        return config
    
    def watch_config(self, config_path: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """监听配置变化
        
        Args:
            config_path: 配置文件路径
            callback: 变化回调函数
        """
        def on_change():
            try:
                # 清除缓存
                cache_key = f"{config_path}:"
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(cache_key)]
                for key in keys_to_remove:
                    del self._cache[key]
                
                # 重新加载配置
                config = self.load_config(config_path)
                callback(config)
            except Exception as e:
                print(f"配置重载失败: {e}")
        
        self.watcher.watch(config_path, on_change)
    
    def register_processor(self, processor: IConfigProcessor) -> None:
        """注册配置处理器
        
        Args:
            processor: 配置处理器
        """
        self.processors.append(processor)
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._cache.clear()
```

## 3. LLM和Tools配置模块设计

### 3.1 LLM配置模块

```python
# src/core/config/models/llm_config.py
"""
LLM配置模型
"""

from typing import Dict, Any, Optional, List
from pydantic import Field, field_validator
from ..base.base_config import BaseConfig
from .retry_timeout_config import RetryTimeoutConfig, TimeoutConfig
from .connection_pool_config import ConnectionPoolConfig

class LLMConfig(BaseConfig):
    """LLM配置模型"""
    
    # 基础配置
    model_type: str = Field(..., description="模型类型")
    model_name: str = Field(..., description="模型名称")
    provider: Optional[str] = Field(None, description="提供商名称")
    
    # API配置
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    
    # 参数配置
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模型参数")
    
    # 重试和超时配置
    retry_config: RetryTimeoutConfig = Field(default_factory=RetryTimeoutConfig)
    timeout_config: TimeoutConfig = Field(default_factory=TimeoutConfig)
    
    # 连接池配置
    connection_pool_config: ConnectionPoolConfig = Field(default_factory=ConnectionPoolConfig)
    
    # 降级配置
    fallback_enabled: bool = Field(True, description="是否启用降级")
    fallback_models: List[str] = Field(default_factory=list, description="降级模型列表")
    
    # 工具调用配置
    function_calling_supported: bool = Field(True, description="是否支持函数调用")
    function_calling_mode: str = Field("auto", description="函数调用模式")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """验证模型类型"""
        allowed_types = ["openai", "gemini", "anthropic", "claude", "mock"]
        if v.lower() not in allowed_types:
            raise ValueError(f"模型类型必须是以下之一: {allowed_types}")
        return v.lower()
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        return self.function_calling_supported
```

### 3.2 Tools配置模块

```python
# src/core/config/models/tool_config.py
"""
工具配置模型
"""

from typing import Dict, Any, List, Optional
from pydantic import Field, field_validator
from ..base.base_config import BaseConfig

class ToolConfig(BaseConfig):
    """工具配置模型"""
    
    # 基础配置
    name: str = Field(..., description="工具名称")
    description: str = Field("", description="工具描述")
    tool_type: str = Field(..., description="工具类型")
    
    # 参数配置
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="参数模式")
    
    # 执行配置
    timeout: int = Field(30, description="超时时间（秒）")
    max_retries: int = Field(3, description="最大重试次数")
    enabled: bool = Field(True, description="是否启用")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator("tool_type")
    @classmethod
    def validate_tool_type(cls, v: str) -> str:
        """验证工具类型"""
        allowed_types = ["builtin", "native", "mcp"]
        if v not in allowed_types:
            raise ValueError(f"工具类型必须是以下之一: {allowed_types}")
        return v
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled

class ToolSetConfig(BaseConfig):
    """工具集配置模型"""
    
    # 基础配置
    name: str = Field(..., description="工具集名称")
    description: str = Field("", description="工具集描述")
    
    # 工具配置
    tools: List[str] = Field(default_factory=list, description="工具列表")
    enabled: bool = Field(True, description="是否启用")
    
    # 继承配置
    inherits_from: Optional[str] = Field(None, description="继承的工具集")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    def has_tool(self, tool_name: str) -> bool:
        """检查是否包含指定工具"""
        return tool_name in self.tools
```

### 3.3 专用配置管理器

```python
# src/core/config/manager/llm_config_manager.py
"""
LLM配置管理器
"""

from typing import Dict, Any, Optional, List
from .config_manager import ConfigManager
from ..models.llm_config import LLMConfig

class LLMConfigManager:
    """LLM配置管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化LLM配置管理器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
    
    def load_llm_config(self, name: str) -> LLMConfig:
        """加载LLM配置
        
        Args:
            name: 配置名称
            
        Returns:
            LLM配置对象
        """
        config_path = f"llms/{name}"
        config_data = self.config_manager.load_config(config_path, "llm")
        return LLMConfig.from_dict(config_data)
    
    def list_llm_configs(self) -> List[str]:
        """列出所有LLM配置
        
        Returns:
            配置名称列表
        """
        # 实现列出LLM配置的逻辑
        pass
    
    def watch_llm_config(self, name: str, callback: Callable[[LLMConfig], None]) -> None:
        """监听LLM配置变化
        
        Args:
            name: 配置名称
            callback: 变化回调函数
        """
        config_path = f"llms/{name}"
        def on_change(config_data: Dict[str, Any]):
            config = LLMConfig.from_dict(config_data)
            callback(config)
        
        self.config_manager.watch_config(config_path, on_change)

# src/core/config/manager/tool_config_manager.py
"""
工具配置管理器
"""

from typing import Dict, Any, Optional, List, Callable
from .config_manager import ConfigManager
from ..models.tool_config import ToolConfig, ToolSetConfig

class ToolConfigManager:
    """工具配置管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化工具配置管理器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
    
    def load_tool_config(self, name: str) -> ToolConfig:
        """加载工具配置
        
        Args:
            name: 配置名称
            
        Returns:
            工具配置对象
        """
        config_path = f"tools/{name}"
        config_data = self.config_manager.load_config(config_path, "tool")
        return ToolConfig.from_dict(config_data)
    
    def load_tool_set_config(self, name: str) -> ToolSetConfig:
        """加载工具集配置
        
        Args:
            name: 配置名称
            
        Returns:
            工具集配置对象
        """
        config_path = f"tool-sets/{name}"
        config_data = self.config_manager.load_config(config_path, "tool_set")
        return ToolSetConfig.from_dict(config_data)
    
    def list_tool_configs(self) -> List[str]:
        """列出所有工具配置
        
        Returns:
            配置名称列表
        """
        # 实现列出工具配置的逻辑
        pass
    
    def list_tool_set_configs(self) -> List[str]:
        """列出所有工具集配置
        
        Returns:
            配置名称列表
        """
        # 实现列出工具集配置的逻辑
        pass
```

## 4. 迁移策略

### 4.1 迁移步骤

1. **创建新配置系统结构**
   - 创建新的目录结构
   - 实现核心接口和基础类

2. **迁移现有功能**
   - 将现有功能拆分到对应组件
   - 保持API兼容性

3. **更新依赖注入**
   - 注册新的配置管理器
   - 更新相关服务的依赖

4. **测试和验证**
   - 单元测试
   - 集成测试
   - 性能测试

### 4.2 兼容性保证

1. **适配器模式**
   - 为旧接口提供适配器
   - 渐进式迁移

2. **配置兼容**
   - 支持现有配置格式
   - 提供配置迁移工具

### 4.3 性能优化

1. **缓存机制**
   - 配置结果缓存
   - 智能缓存失效

2. **懒加载**
   - 按需加载配置
   - 延迟初始化

## 5. 优势总结

### 5.1 架构优势

1. **职责清晰**：每个组件只负责特定功能
2. **易于扩展**：新功能可以通过添加组件实现
3. **易于测试**：组件独立，便于单元测试
4. **易于维护**：代码结构清晰，便于理解和修改

### 5.2 功能优势

1. **灵活的处理器管道**：可以自由组合处理器
2. **强大的继承机制**：支持多继承和复杂继承关系
3. **完善的验证体系**：支持多种验证方式
4. **实时配置更新**：支持配置文件监听和热更新

### 5.3 开发优势

1. **开发效率高**：组件化开发，并行工作
2. **代码复用性强**：通用组件可复用
3. **调试方便**：问题定位精确
4. **文档完善**：每个组件都有清晰的接口定义

这种新的配置系统架构通过组件化设计，实现了高内聚、低耦合的目标，为系统的配置管理提供了强大而灵活的解决方案。