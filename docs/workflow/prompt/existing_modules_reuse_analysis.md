# 现有模块复用分析

## 概述

本文档分析了当前系统中已有的缓存、配置管理和其他相关模块，提出了在提示词工作流重构中复用这些模块的建议，避免重复实现。

## 现有模块分析

### 1. 缓存系统

#### 1.1 核心缓存模块 (`src/core/common/cache.py`)

**功能特性**：
- 基于 `cachetools` 的增强缓存系统
- 支持 TTL、LRU、LFU 等多种淘汰策略
- 线程安全的缓存操作
- 缓存统计和监控
- 支持序列化和压缩
- 专用缓存类：`ConfigCache`、`LLMCache`、`GraphCache`

**可复用组件**：
```python
# 全局缓存管理器
from src.core.common.cache import get_global_cache_manager, CacheManager

# 专用缓存类
from src.core.common.cache import ConfigCache, LLMCache, GraphCache

# 缓存装饰器
from src.core.common.cache import config_cached, llm_cached, graph_cached
```

**复用建议**：
- **直接复用**：`CacheManager` 作为提示词缓存的基础
- **扩展专用缓存**：创建 `PromptCache` 专用类
- **利用统计功能**：复用缓存统计和监控机制

#### 1.2 LLM缓存系统 (`src/core/llm/cache/`)

**功能特性**：
- `CacheConfig` 和 `EnhancedCacheConfig` 配置模型
- 支持多种缓存策略（client_first, server_first, hybrid）
- Gemini 服务器端缓存支持
- 缓存键生成和管理

**可复用组件**：
```python
# 缓存配置
from src.core.llm.cache.cache_config import CacheConfig, EnhancedCacheConfig

# 缓存管理器
from src.core.llm.cache import CacheManager, create_cache_manager
```

**复用建议**：
- **配置模型复用**：扩展 `CacheConfig` 支持提示词特定配置
- **缓存策略复用**：利用现有的缓存策略选择机制

#### 1.3 图缓存系统 (`src/core/workflow/registry/graph_cache.py`)

**功能特性**：
- `IGraphCache` 接口和 `GraphCache` 实现
- 多种淘汰策略（LRU、LFU、TTL）
- 模式匹配的缓存失效
- 缓存优化和统计

**可复用组件**：
```python
# 图缓存接口和实现
from src.core.workflow.registry.graph_cache import IGraphCache, GraphCache, create_graph_cache

# 缓存条目和策略
from src.core.workflow.registry.graph_cache import CacheEntry, CacheEvictionPolicy
```

**复用建议**：
- **接口设计参考**：参考 `IGraphCache` 设计 `IPromptCache`
- **淘汰策略复用**：直接复用 `CacheEvictionPolicy` 枚举
- **模式匹配复用**：复用缓存失效的模式匹配逻辑

### 2. 配置管理系统

#### 2.1 配置加载器 (`src/core/config/config_loader.py`)

**功能特性**：
- 支持 YAML、JSON 格式
- 配置文件类型推断
- 路径解析和格式自动识别
- 配置缓存（通过 `@config_cached` 装饰器）
- 配置合并功能

**可复用组件**：
```python
# 配置加载器
from src.core.config.config_loader import ConfigLoader, load_config_file, merge_configs

# 缓存装饰器
from src.core.common.cache import config_cached
```

**复用建议**：
- **直接复用**：`ConfigLoader` 用于加载提示词配置文件
- **扩展功能**：添加提示词特定的配置类型推断
- **合并逻辑复用**：复用配置合并功能处理继承关系

#### 2.2 配置管理器 (`src/core/config/config_manager.py`)

**功能特性**：
- 统一的配置管理入口
- 配置注册表和类型管理
- 配置验证和模型转换
- 环境变量解析
- 文件监听和自动重载
- 配置变更回调机制

**可复用组件**：
```python
# 配置管理器
from src.core.config.config_manager import ConfigManager, get_default_manager

# 配置注册表
from src.core.config.config_manager import ConfigRegistry

# 便捷函数
from src.core.config.config_manager import load_config, load_config_model
```

**复用建议**：
- **扩展配置类型**：添加 `ConfigType.PROMPT` 类型
- **复用验证机制**：利用现有的配置验证框架
- **复用回调系统**：用于提示词配置变更通知

### 3. LLM客户端增强功能 (`src/core/llm/clients/enhanced_base.py`)

**功能特性**：
- 缓存集成（通过 `_execute_with_cache`）
- 降级机制（通过 `_execute_with_fallback`）
- 重试机制（通过 `_execute_with_retry`）
- 钩子系统
- 错误处理和转换

**可复用组件**：
```python
# 缓存执行模式
from src.core.llm.clients.enhanced_base import EnhancedLLMClient

# 钩子接口
from src.core.llm.interfaces import ILLMCallHook
```

**复用建议**：
- **执行模式复用**：参考缓存、降级、重试的执行模式设计
- **钩子系统复用**：用于提示词注入的生命周期管理

### 4. 工作流执行系统

#### 4.1 执行管理器 (`src/core/workflow/execution/services/execution_manager.py`)

**功能特性**：
- 工作流执行管理
- 结果缓存（通过 `_cache_result`）
- 执行上下文管理
- 错误处理和恢复

**可复用组件**：
```python
# 执行管理器
from src.core.workflow.execution.services.execution_manager import WorkflowExecutionManager

# 缓存机制
# 参考 _cache_result 方法的实现
```

**复用建议**：
- **缓存模式复用**：参考工作流结果的缓存模式
- **上下文管理复用**：用于提示词注入的执行上下文

## 复用方案设计

### 1. 提示词缓存系统设计

#### 1.1 基于现有缓存系统的扩展

```python
# src/services/prompts/cache/prompt_cache.py
from src.core.common.cache import CacheManager, CacheEntry
from src.core.llm.cache.cache_config import CacheConfig
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

class PromptCacheConfig(CacheConfig):
    """提示词缓存配置"""
    
    # 提示词特定配置
    enable_content_validation: bool = True
    max_content_size: int = 1024 * 1024  # 1MB
    compression_threshold: int = 10 * 1024  # 10KB
    
    def __post_init__(self) -> None:
        super().__post_init__()
        # 调整默认值以适应提示词特点
        if self.ttl_seconds == 3600:  # 默认值
            self.ttl_seconds = 7200  # 提示词缓存时间更长

class PromptCache:
    """提示词专用缓存"""
    
    def __init__(self, config: Optional[PromptCacheConfig] = None):
        self.config = config or PromptCacheConfig()
        
        # 复用全局缓存管理器
        self._cache_manager = get_global_cache_manager()
        
        # 创建专用缓存实例
        self._cache = self._cache_manager.get_cache(
            "prompt",
            maxsize=self.config.max_size,
            ttl=self.config.ttl_seconds
        )
    
    async def get(self, key: str) -> Optional[str]:
        """获取提示词内容"""
        # 复用缓存管理器的异步获取
        return await self._cache_manager.get(key)
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """设置提示词内容"""
        # 内容验证
        if self.config.enable_content_validation:
            self._validate_content(value)
        
        # 压缩大内容
        if len(value) > self.config.compression_threshold:
            value = self._compress_content(value)
        
        # 复用缓存管理器的异步设置
        await self._cache_manager.set(key, value, ttl or self.config.ttl_seconds)
    
    def _validate_content(self, content: str) -> None:
        """验证提示词内容"""
        if len(content) > self.config.max_content_size:
            raise ValueError(f"提示词内容过大: {len(content)} > {self.config.max_content_size}")
    
    def _compress_content(self, content: str) -> str:
        """压缩提示词内容"""
        # 复用现有的序列化机制
        import gzip
        import base64
        compressed = gzip.compress(content.encode('utf-8'))
        return base64.b64encode(compressed).decode('ascii')
```

#### 1.2 缓存键生成策略

```python
# src/services/prompts/cache/key_generator.py
from src.core.llm.cache import LLMCacheKeyGenerator
from typing import Sequence, Dict, Any

class PromptCacheKeyGenerator:
    """提示词缓存键生成器"""
    
    def __init__(self):
        # 复用LLM缓存键生成器的逻辑
        self._llm_key_generator = LLMCacheKeyGenerator()
    
    def generate_key(
        self,
        category: str,
        name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成提示词缓存键"""
        base_key = f"prompt:{category}:{name}"
        
        if parameters:
            # 复用参数序列化逻辑
            param_str = self._serialize_parameters(parameters)
            base_key += f":{param_str}"
        
        return base_key
    
    def _serialize_parameters(self, parameters: Dict[str, Any]) -> str:
        """序列化参数"""
        # 复用LLM缓存键生成器的参数序列化
        return self._llm_key_generator._serialize_parameters(parameters)
```

### 2. 配置系统集成方案

#### 2.1 扩展配置类型

```python
# src/core/config/base.py (扩展现有枚举)
from enum import Enum

class ConfigType(Enum):
    """配置类型枚举"""
    LLM = "llm"
    TOOL = "tool"
    TOOL_SET = "tool_set"
    GLOBAL = "global"
    PROMPT = "prompt"  # 新增提示词类型
    WORKFLOW = "workflow"
    STATE_MACHINE = "state_machine"
```

#### 2.2 提示词配置模型

```python
# src/core/config/models/prompt_config.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .base import BaseConfig

@dataclass
class PromptConfig(BaseConfig):
    """提示词配置模型"""
    
    # 基础配置
    category: str = "system"  # system, rules, user_commands
    content: str = ""
    description: str = ""
    
    # 元数据
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    author: str = "system"
    
    # 依赖关系
    dependencies: List[str] = field(default_factory=list)
    
    # 参数定义
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    
    # 缓存配置
    cache_ttl: int = 3600
    cache_enabled: bool = True
    
    # 验证规则
    validation: Dict[str, Any] = field(default_factory=dict)
    
    # 复合提示词配置
    composite: bool = False
    components: List[Dict[str, Any]] = field(default_factory=list)
```

#### 2.3 配置加载器扩展

```python
# src/core/config/config_loader.py (扩展现有模式)
class ConfigLoader:
    def __init__(self, base_path: Optional[Path] = None):
        # ... 现有代码 ...
        
        # 添加提示词配置模式
        self._prompt_patterns = [
            r".*prompt.*\.ya?ml$",
            r".*system.*\.ya?ml$",
            r".*rules.*\.ya?ml$",
            r".*user_commands.*\.ya?ml$"
        ]
        self._compiled_prompt_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self._prompt_patterns]
    
    def infer_config_type(self, config_path: str) -> str:
        """扩展配置类型推断"""
        # ... 现有代码 ...
        
        # 添加提示词类型推断
        path_lower = config_path.lower()
        if any(pattern.search(config_path) for pattern in self._compiled_prompt_patterns):
            return "prompt"
        
        # ... 现有代码 ...
```

### 3. 工作流构建器集成

#### 3.1 基于现有配置管理器的构建器

```python
# src/services/workflow/builders/prompt_aware_builder.py
from src.core.config.config_manager import ConfigManager
from src.core.config.config_loader import ConfigLoader
from src.services.prompts.cache.prompt_cache import PromptCache

class PromptAwareWorkflowBuilder:
    """提示词感知的工作流构建器"""
    
    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        prompt_cache: Optional[PromptCache] = None
    ):
        # 复用现有配置管理器
        self.config_manager = config_manager or ConfigManager()
        
        # 使用提示词专用缓存
        self.prompt_cache = prompt_cache or PromptCache()
        
        # 复用配置加载器
        self.config_loader = self.config_manager.loader
    
    async def build_from_config(self, config_path: str) -> Any:
        """从配置构建工作流"""
        # 复用配置加载逻辑
        config = self.config_manager.load_config(config_path)
        
        # 处理提示词引用
        if 'prompts' in config:
            config['prompts'] = await self._resolve_prompt_references(config['prompts'])
        
        # 构建工作流
        return await self._build_workflow(config)
    
    async def _resolve_prompt_references(self, prompts_config: Dict[str, Any]) -> Dict[str, Any]:
        """解析提示词引用"""
        resolved = {}
        
        for key, value in prompts_config.items():
            if isinstance(value, str) and value.startswith('ref://'):
                # 解析引用
                category, name = self._parse_reference(value)
                
                # 从缓存获取
                cache_key = f"prompt:{category}:{name}"
                cached_content = await self.prompt_cache.get(cache_key)
                
                if cached_content is None:
                    # 从配置加载
                    prompt_config = self._load_prompt_config(category, name)
                    cached_content = prompt_config.content
                    
                    # 缓存内容
                    await self.prompt_cache.set(cache_key, cached_content)
                
                resolved[key] = cached_content
            else:
                resolved[key] = value
        
        return resolved
```

### 4. 错误处理集成

#### 4.1 复用现有错误处理机制

```python
# src/services/prompts/error_handler.py
from src.core.common.exceptions.prompts import PromptError
from src.core.llm.clients.enhanced_base import EnhancedLLMClient

class PromptErrorHandler:
    """提示词错误处理器"""
    
    def __init__(self):
        # 复用LLM客户端的错误处理逻辑
        self._llm_error_handler = EnhancedLLMClient
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Optional[PromptError]:
        """处理提示词错误"""
        # 复用错误分类和转换逻辑
        if isinstance(error, FileNotFoundError):
            return PromptError(f"提示词文件未找到: {context.get('prompt_path')}")
        
        # 复用错误恢复策略
        return self._attempt_error_recovery(error, context)
    
    def _attempt_error_recovery(self, error: Exception, context: Dict[str, Any]) -> Optional[PromptError]:
        """尝试错误恢复"""
        # 复用LLM客户端的错误恢复逻辑
        # ...
        return None
```

## 避免重复实现的具体建议

### 1. 缓存系统

**避免重复**：
- ❌ 重新实现缓存存储和淘汰逻辑
- ❌ 重新实现缓存统计和监控
- ❌ 重新实现序列化和压缩

**复用现有**：
- ✅ 扩展 `CacheManager` 创建 `PromptCache`
- ✅ 复用 `CacheEvictionPolicy` 枚举
- ✅ 复用缓存统计接口
- ✅ 复用序列化机制

### 2. 配置管理

**避免重复**：
- ❌ 重新实现YAML/JSON加载逻辑
- ❌ 重新实现配置验证框架
- ❌ 重新实现环境变量解析

**复用现有**：
- ✅ 扩展 `ConfigType` 枚举添加 `PROMPT`
- ✅ 复用 `ConfigLoader` 加载提示词配置
- ✅ 复用 `ConfigManager` 的验证和回调机制
- ✅ 复用配置合并逻辑处理继承

### 3. 错误处理

**避免重复**：
- ❌ 重新实现错误分类和转换
- ❌ 重新实现错误恢复策略

**复用现有**：
- ✅ 扩展现有错误类型体系
- ✅ 复用错误处理模式
- ✅ 复用钩子机制

### 4. 工作流集成

**避免重复**：
- ❌ 重新实现工作流构建逻辑
- ❌ 重新实现节点和边管理

**复用现有**：
- ✅ 扩展现有工作流构建器
- ✅ 复用配置加载和验证机制
- ✅ 复用执行上下文管理

## 实施优先级

### 高优先级（立即复用）

1. **缓存系统**：直接复用 `CacheManager` 创建 `PromptCache`
2. **配置加载**：复用 `ConfigLoader` 加载提示词配置
3. **错误处理**：扩展现有错误类型体系

### 中优先级（适配复用）

1. **配置管理**：扩展 `ConfigManager` 支持提示词类型
2. **工作流构建**：基于现有构建器创建提示词感知版本
3. **缓存键生成**：复用 `LLMCacheKeyGenerator` 的逻辑

### 低优先级（选择性复用）

1. **序列化机制**：根据需要复用压缩和序列化
2. **监控统计**：复用缓存统计接口
3. **回调系统**：复用配置变更回调机制

## 总结

通过深入分析现有系统，我们发现已经有大量成熟的模块可以直接复用或稍作扩展即可用于提示词工作流系统。主要优势包括：

1. **减少开发工作量**：避免重复实现基础功能
2. **提高系统一致性**：复用经过验证的成熟组件
3. **降低维护成本**：减少重复代码的维护负担
4. **加快开发进度**：专注于业务逻辑而非基础设施

建议在实施过程中优先复用高优先级模块，然后根据实际需要逐步集成中低优先级模块，确保在避免重复实现的同时，最大化利用现有系统的成熟功能。