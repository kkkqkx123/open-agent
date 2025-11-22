# 提示词配置系统分析

## 概述

本文档分析当前 `configs/prompts` 目录中的提示词配置系统，并提出与提示词模块的集成方案。目标是实现工作流能够直接根据配置文件加载并构建成图，配置文件中的提示词设置采用引用的形式。

## 当前提示词配置系统分析

### 1. 目录结构

```
configs/prompts/
├── system/                    # 系统提示词
│   ├── assistant.md          # 通用助手提示词
│   └── coder/                # 代码生成专家提示词（复合提示词）
│       ├── index.md          # 主提示词
│       ├── 01_code_style.md  # 代码风格规范
│       └── 02_error_handling.md # 错误处理规范
├── rules/                    # 规则提示词
│   ├── format.md             # 格式规则
│   └── safety.md             # 安全规则
└── user_commands/            # 用户指令
    ├── code_review.md        # 代码审查指令
    └── data_analysis.md      # 数据分析指令
```

### 2. 提示词文件格式

#### 2.1 简单提示词格式

```markdown
---
description: 通用助手提示词，定义Agent基础角色
---

你是一个通用助手，负责解答用户问题，语言简洁明了。
```

#### 2.2 复合提示词格式

复合提示词以目录形式组织，包含 `index.md` 文件和其他子文件：

```markdown
# coder/index.md
---
description: 代码生成专家系统提示词
---

你是一个代码生成专家，负责生成高质量、可维护的代码。
```

```markdown
# coder/01_code_style.md
---
description: 代码风格规范
---

请遵循以下代码风格：
- 使用PEP8规范
- 添加适当的注释
- 使用有意义的变量名。避免advanced, smart, enhanced等没有意义的命名
```

### 3. 提示词分类

#### 3.1 系统提示词 (system/)
- **作用**：定义AI助手的基础角色和行为
- **特点**：通常在工作流开始时注入，影响整个对话过程
- **示例**：`assistant.md`, `coder/`

#### 3.2 规则提示词 (rules/)
- **作用**：定义AI助手必须遵循的规则和约束
- **特点**：在系统提示词之后注入，提供行为边界
- **示例**：`safety.md`, `format.md`

#### 3.3 用户指令 (user_commands/)
- **作用**：定义具体的任务指令和期望输出格式
- **特点**：在用户输入时注入，指导AI完成特定任务
- **示例**：`data_analysis.md`, `code_review.md`

### 4. 当前系统的优点

1. **清晰的分类结构**：按功能分类，便于管理和查找
2. **支持复合提示词**：通过目录结构支持复杂提示词组合
3. **元数据支持**：通过YAML前置元数据提供描述信息
4. **易于扩展**：添加新提示词只需创建相应文件

### 5. 当前系统的局限性

1. **缺乏版本管理**：没有版本控制和变更追踪
2. **缺乏依赖关系**：无法定义提示词间的依赖关系
3. **缺乏参数化**：不支持变量替换和动态内容
4. **缺乏验证**：没有格式验证和内容检查
5. **缺乏国际化**：不支持多语言提示词
6. **缺乏性能优化**：没有缓存和预加载机制

## 与提示词模块的集成方案

### 1. 增强的提示词元数据

#### 1.1 扩展元数据格式

```yaml
---
name: "assistant"
description: "通用助手提示词，定义Agent基础角色"
version: "1.0.0"
category: "system"
tags: ["general", "assistant"]
author: "system"
created_at: "2024-01-01"
updated_at: "2024-01-01"
dependencies: []
parameters:
  - name: "language"
    type: "string"
    default: "zh-CN"
    description: "响应语言"
cache_ttl: 3600
validation:
  max_length: 1000
  required_patterns: []
---

你是一个通用助手，负责解答用户问题，语言简洁明了。
```

#### 1.2 复合提示词配置

```yaml
# coder/index.yaml
---
name: "coder"
description: "代码生成专家系统提示词"
version: "1.2.0"
category: "system"
tags: ["coding", "expert"]
composite: true
components:
  - file: "01_code_style.md"
    order: 1
    required: true
  - file: "02_error_handling.md"
    order: 2
    required: true
  - file: "03_testing.md"
    order: 3
    required: false
parameters:
  - name: "language"
    type: "string"
    default: "python"
    description: "编程语言"
  - name: "framework"
    type: "string"
    default: ""
    description: "使用的框架"
---
```

### 2. 提示词注册表

#### 2.1 提示词注册表接口

```python
# src/interfaces/prompts/registry.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import PromptMeta, PromptConfig

class IPromptRegistry(ABC):
    """提示词注册表接口"""
    
    @abstractmethod
    async def register_prompt(self, meta: PromptMeta) -> None:
        """注册提示词"""
        pass
    
    @abstractmethod
    async def get_prompt_meta(self, category: str, name: str) -> Optional[PromptMeta]:
        """获取提示词元信息"""
        pass
    
    @abstractmethod
    async def list_prompts(self, category: str, tags: List[str] = None) -> List[PromptMeta]:
        """列出提示词"""
        pass
    
    @abstractmethod
    async def resolve_dependencies(self, prompt_name: str) -> List[PromptMeta]:
        """解析提示词依赖"""
        pass
    
    @abstractmethod
    async def validate_prompt(self, meta: PromptMeta) -> List[str]:
        """验证提示词"""
        pass
```

#### 2.2 提示词注册表实现

```python
# src/services/prompts/registry.py
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from ...interfaces.prompts.registry import IPromptRegistry
from ...interfaces.prompts.models import PromptMeta
from ...core.common.exceptions.prompts import PromptRegistryError

class PromptRegistry(IPromptRegistry):
    """提示词注册表实现"""
    
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._prompts: Dict[str, PromptMeta] = {}
        self._categories = ["system", "rules", "user_commands"]
    
    async def initialize(self) -> None:
        """初始化注册表，扫描并注册所有提示词"""
        for category in self._categories:
            await self._scan_category(category)
    
    async def _scan_category(self, category: str) -> None:
        """扫描类别目录"""
        category_dir = self.prompts_dir / category
        if not category_dir.exists():
            return
        
        for item in category_dir.iterdir():
            if item.is_file() and item.suffix == '.md':
                await self._register_simple_prompt(category, item)
            elif item.is_dir() and (item / 'index.yaml').exists():
                await self._register_composite_prompt(category, item)
    
    async def _register_simple_prompt(self, category: str, file_path: Path) -> None:
        """注册简单提示词"""
        meta = await self._parse_prompt_meta(category, file_path)
        await self.register_prompt(meta)
    
    async def _register_composite_prompt(self, category: str, dir_path: Path) -> None:
        """注册复合提示词"""
        index_file = dir_path / 'index.yaml'
        meta = await self._parse_composite_prompt_meta(category, dir_path, index_file)
        await self.register_prompt(meta)
    
    async def _parse_prompt_meta(self, category: str, file_path: Path) -> PromptMeta:
        """解析提示词元信息"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析YAML前置元数据
        if content.startswith('---\n'):
            try:
                end_index = content.find('\n---\n', 4)
                if end_index != -1:
                    yaml_content = content[4:end_index]
                    metadata = yaml.safe_load(yaml_content)
                    prompt_content = content[end_index + 5:]
                else:
                    metadata = {}
                    prompt_content = content
            except yaml.YAMLError as e:
                raise PromptRegistryError(f"解析提示词元数据失败: {e}")
        else:
            metadata = {}
            prompt_content = content
        
        # 创建PromptMeta对象
        return PromptMeta(
            name=metadata.get('name', file_path.stem),
            category=category,
            path=file_path,
            description=metadata.get('description', ''),
            version=metadata.get('version', '1.0.0'),
            tags=metadata.get('tags', []),
            author=metadata.get('author', 'system'),
            created_at=metadata.get('created_at'),
            updated_at=metadata.get('updated_at'),
            dependencies=metadata.get('dependencies', []),
            parameters=metadata.get('parameters', []),
            cache_ttl=metadata.get('cache_ttl', 3600),
            validation=metadata.get('validation', {}),
            content=prompt_content
        )
```

### 3. 配置文件引用系统

#### 3.1 引用语法设计

在工作流配置文件中，使用以下语法引用提示词：

```yaml
# workflows/prompt_agent_workflow.yaml
metadata:
  name: "prompt_agent_workflow"
  version: "1.0.0"
  description: "基于提示词的代理工作流"

# 提示词配置
prompts:
  system_prompt: "ref://system/assistant"
  rules:
    - "ref://rules/safety"
    - "ref://rules/format"
  user_command: "ref://user_commands/data_analysis"
  
  # 带参数的引用
  system_prompt_with_params:
    ref: "ref://system/coder"
    parameters:
      language: "python"
      framework: "fastapi"

# 节点配置
nodes:
  inject_prompts:
    function: "prompt_injection_node"
    config:
      prompt_config: "{{ prompts }}"
      cache_enabled: true
```

#### 3.2 引用解析器

```python
# src/services/prompts/reference_resolver.py
import re
from typing import Dict, Any, List, Optional
from ...interfaces.prompts.registry import IPromptRegistry
from ...interfaces.prompts.models import PromptConfig

class PromptReferenceResolver:
    """提示词引用解析器"""
    
    def __init__(self, registry: IPromptRegistry):
        self.registry = registry
        self.ref_pattern = re.compile(r'ref://([^/]+)/([^/]+)')
    
    async def resolve_references(self, config: Dict[str, Any]) -> PromptConfig:
        """解析配置中的提示词引用"""
        resolved_config = {}
        
        # 解析系统提示词
        if 'system_prompt' in config:
            resolved_config['system_prompt'] = await self._resolve_reference(
                config['system_prompt']
            )
        
        # 解析规则提示词
        if 'rules' in config:
            resolved_config['rules'] = await self._resolve_references_list(
                config['rules']
            )
        
        # 解析用户指令
        if 'user_command' in config:
            resolved_config['user_command'] = await self._resolve_reference(
                config['user_command']
            )
        
        # 解析缓存设置
        resolved_config['cache_enabled'] = config.get('cache_enabled', True)
        
        return PromptConfig(**resolved_config)
    
    async def _resolve_reference(self, ref: Any) -> str:
        """解析单个引用"""
        if isinstance(ref, str) and ref.startswith('ref://'):
            match = self.ref_pattern.match(ref)
            if match:
                category, name = match.groups()
                return f"{category}/{name}"
        
        return ref
    
    async def _resolve_references_list(self, refs: List[Any]) -> List[str]:
        """解析引用列表"""
        resolved = []
        for ref in refs:
            resolved_ref = await self._resolve_reference(ref)
            if resolved_ref:
                resolved.append(resolved_ref)
        return resolved
```

### 4. 工作流构建器集成

#### 4.1 增强的工作流构建器

```python
# src/services/workflow/builders/prompt_aware_builder.py
from typing import Dict, Any, Optional
from ...interfaces.prompts.registry import IPromptRegistry
from ...interfaces.prompts.reference_resolver import PromptReferenceResolver
from ...services.prompts.workflow_helpers import create_prompt_agent_workflow

class PromptAwareWorkflowBuilder:
    """提示词感知的工作流构建器"""
    
    def __init__(
        self,
        registry: IPromptRegistry,
        reference_resolver: PromptReferenceResolver
    ):
        self.registry = registry
        self.reference_resolver = reference_resolver
    
    async def build_from_config(self, config: Dict[str, Any]) -> Any:
        """从配置构建工作流"""
        # 解析提示词引用
        if 'prompts' in config:
            prompt_config = await self.reference_resolver.resolve_references(
                config['prompts']
            )
        else:
            prompt_config = None
        
        # 创建提示词注入器
        from ...services.prompts.injector import PromptInjector
        from ...services.prompts.loader import PromptLoader
        from ...services.prompts.cache import MemoryPromptCache
        
        loader = PromptLoader(self.registry)
        cache = MemoryPromptCache()
        injector = PromptInjector(loader, cache)
        
        # 构建工作流
        workflow = create_prompt_agent_workflow(
            prompt_injector=injector,
            llm_client=config.get('llm_client'),
            system_prompt=prompt_config.system_prompt if prompt_config else None,
            rules=prompt_config.rules if prompt_config else None,
            user_command=prompt_config.user_command if prompt_config else None,
            cache_enabled=prompt_config.cache_enabled if prompt_config else True
        )
        
        return workflow
```

## LLM节点提示词配置方式分析

### 1. 当前方式：专门节点注入

#### 1.1 优点

1. **职责分离**：提示词注入与LLM调用分离，符合单一职责原则
2. **灵活性高**：可以独立配置提示词注入逻辑
3. **可复用性**：提示词注入节点可以被多个工作流复用
4. **可测试性**：可以独立测试提示词注入逻辑
5. **可扩展性**：可以添加其他预处理节点

#### 1.2 缺点

1. **复杂度增加**：需要额外的节点和转换
2. **性能开销**：额外的节点执行开销
3. **配置复杂**：需要在多个地方配置相关参数
4. **调试困难**：问题可能分布在多个节点中

### 2. 替代方式：LLM节点直接配置

#### 2.1 优点

1. **简化配置**：所有相关配置集中在一个节点
2. **减少开销**：减少节点数量和转换
3. **直观性**：配置更加直观和易于理解
4. **性能提升**：减少节点间的状态传递

#### 2.2 缺点

1. **职责混合**：提示词处理与LLM调用混合
2. **灵活性降低**：难以独立配置提示词逻辑
3. **可复用性差**：提示词逻辑与特定LLM节点绑定
4. **测试困难**：难以独立测试提示词逻辑

### 3. 推荐方案：混合方式

基于分析，推荐采用混合方式：

#### 3.1 基础场景：直接配置

对于简单的场景，支持在LLM节点中直接配置提示词：

```yaml
nodes:
  llm_node:
    function: "llm_call_node"
    config:
      llm_client: "gpt-4"
      prompts:
        system_prompt: "ref://system/assistant"
        rules: ["ref://rules/safety"]
      temperature: 0.7
```

#### 3.2 复杂场景：专门节点

对于复杂的场景，使用专门的提示词注入节点：

```yaml
nodes:
  inject_prompts:
    function: "prompt_injection_node"
    config:
      prompt_config:
        system_prompt: "ref://system/coder"
        rules: ["ref://rules/safety", "ref://rules/format"]
        user_command: "ref://user_commands/code_review"
      cache_enabled: true
  
  llm_node:
    function: "llm_call_node"
    config:
      llm_client: "gpt-4"
      temperature: 0.7

edges:
  - from: "inject_prompts"
    to: "llm_node"
```

#### 3.3 实现策略

```python
# src/core/workflow/graph/node_functions/enhanced_llm_node.py
from typing import Dict, Any, Optional
from ...interfaces.prompts.reference_resolver import PromptReferenceResolver

async def create_enhanced_llm_node(
    llm_client: Any,
    prompt_config: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """创建增强的LLM节点，支持直接配置提示词"""
    
    async def enhanced_llm_node(state: IWorkflowState) -> IWorkflowState:
        # 如果配置了提示词，先注入提示词
        if prompt_config:
            resolver = PromptReferenceResolver(registry)
            config = await resolver.resolve_references(prompt_config)
            
            # 创建临时注入器
            injector = create_prompt_injector()
            state = await injector.inject_prompts(state, config)
        
        # 执行LLM调用
        return await llm_call_node(state, llm_client, **kwargs)
    
    return enhanced_llm_node
```

## 工作流配置文件加载和构建方案

### 1. 配置文件结构设计

#### 1.1 增强的工作流配置格式

```yaml
# workflows/enhanced_prompt_agent.yaml
---
metadata:
  name: "enhanced_prompt_agent"
  version: "1.0.0"
  description: "增强的提示词代理工作流"
  author: "system"
  tags: ["prompt", "agent"]

# 继承配置
inherits_from: "base_workflow.yaml"

# 提示词配置
prompts:
  # 系统提示词
  system_prompt:
    ref: "ref://system/assistant"
    parameters:
      language: "zh-CN"
      style: "professional"
  
  # 规则提示词
  rules:
    - ref: "ref://rules/safety"
    - ref: "ref://rules/format"
      parameters:
        output_format: "markdown"
  
  # 用户指令
  user_command:
    ref: "ref://user_commands/data_analysis"
    parameters:
      detail_level: "detailed"
  
  # 全局设置
  cache_enabled: true
  cache_ttl: 3600
  validation_enabled: true

# 节点配置
nodes:
  start_node:
    function: "start_node"
    description: "开始节点"
  
  inject_prompts:
    function: "prompt_injection_node"
    config:
      prompt_config: "{{ prompts }}"
      error_handling: "continue"
    description: "注入提示词"
  
  llm_call:
    function: "enhanced_llm_node"
    config:
      llm_client: "gpt-4"
      temperature: 0.7
      max_tokens: 2000
      # 可选：直接配置提示词
      # prompts: "{{ prompts }}"
    description: "调用LLM"
  
  end_node:
    function: "end_node"
    description: "结束节点"

# 边配置
edges:
  - from: "start_node"
    to: "inject_prompts"
    type: "simple"
  
  - from: "inject_prompts"
    to: "llm_call"
    type: "simple"
  
  - from: "llm_call"
    to: "end_node"
    type: "simple"

# 入口点
entry_point: "start_node"

# 验证规则
validation_rules:
  - field: "prompts.system_prompt"
    rule_type: "required"
    message: "系统提示词不能为空"
  
  - field: "nodes.llm_call.config.llm_client"
    rule_type: "required"
    message: "LLM客户端不能为空"
```

### 2. 配置加载器实现

#### 2.1 配置加载器接口

```python
# src/interfaces/workflow/config_loader.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path

class IWorkflowConfigLoader(ABC):
    """工作流配置加载器接口"""
    
    @abstractmethod
    async def load_config(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        pass
    
    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        pass
    
    @abstractmethod
    async def resolve_inheritance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析继承关系"""
        pass
    
    @abstractmethod
    async def resolve_references(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析引用"""
        pass
```

#### 2.2 配置加载器实现

```python
# src/services/workflow/config_loader.py
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from ...interfaces.workflow.config_loader import IWorkflowConfigLoader
from ...interfaces.prompts.reference_resolver import PromptReferenceResolver
from ...core.common.exceptions import ConfigurationError

class WorkflowConfigLoader(IWorkflowConfigLoader):
    """工作流配置加载器实现"""
    
    def __init__(
        self,
        config_dir: Path,
        reference_resolver: Optional[PromptReferenceResolver] = None
    ):
        self.config_dir = config_dir
        self.reference_resolver = reference_resolver
        self._config_cache: Dict[str, Dict[str, Any]] = {}
    
    async def load_config(self, config_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        # 检查缓存
        cache_key = str(config_path)
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # 加载文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"加载配置文件失败: {e}")
        
        # 处理配置
        config = await self.resolve_inheritance(config)
        config = await self.resolve_references(config)
        
        # 验证配置
        errors = await self.validate_config(config)
        if errors:
            raise ConfigurationError(f"配置验证失败: {'; '.join(errors)}")
        
        # 缓存配置
        self._config_cache[cache_key] = config
        
        return config
    
    async def resolve_inheritance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析继承关系"""
        if 'inherits_from' not in config:
            return config
        
        parent_path = self.config_dir / config['inherits_from']
        parent_config = await self.load_config(parent_path)
        
        # 合并配置
        merged_config = self._merge_configs(parent_config, config)
        
        # 移除继承字段
        merged_config.pop('inherits_from', None)
        
        return merged_config
    
    def _merge_configs(
        self,
        parent: Dict[str, Any],
        child: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并配置"""
        merged = parent.copy()
        
        for key, value in child.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    async def resolve_references(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析引用"""
        if self.reference_resolver and 'prompts' in config:
            # 解析提示词引用
            prompt_config = await self.reference_resolver.resolve_references(
                config['prompts']
            )
            config['prompts'] = prompt_config
        
        # 解析模板变量
        config = await self._resolve_template_variables(config)
        
        return config
    
    async def _resolve_template_variables(self, config: Any) -> Any:
        """解析模板变量"""
        if isinstance(config, dict):
            return {
                key: await self._resolve_template_variables(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [
                await self._resolve_template_variables(item)
                for item in config
            ]
        elif isinstance(config, str) and '{{' in config and '}}' in config:
            # 简单的模板变量解析
            # 这里可以实现更复杂的模板引擎
            return config  # 暂时返回原值
        else:
            return config
    
    async def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        errors = []
        
        # 验证必需字段
        required_fields = ['metadata', 'nodes', 'edges']
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证元数据
        if 'metadata' in config:
            metadata = config['metadata']
            if 'name' not in metadata:
                errors.append("metadata.name 不能为空")
        
        # 验证节点
        if 'nodes' in config:
            nodes = config['nodes']
            entry_point = config.get('entry_point')
            if entry_point and entry_point not in nodes:
                errors.append(f"入口节点 '{entry_point}' 不存在")
        
        # 验证边
        if 'edges' in config and 'nodes' in config:
            edges = config['edges']
            nodes = config['nodes']
            for edge in edges:
                from_node = edge.get('from')
                to_node = edge.get('to')
                if from_node and from_node not in nodes:
                    errors.append(f"边中的起始节点 '{from_node}' 不存在")
                if to_node and to_node not in nodes:
                    errors.append(f"边中的目标节点 '{to_node}' 不存在")
        
        return errors
```

### 3. 工作流构建器

#### 3.1 工作流构建器实现

```python
# src/services/workflow/builder.py
from typing import Dict, Any, Optional
from pathlib import Path
from ...interfaces.workflow.config_loader import IWorkflowConfigLoader
from ...interfaces.prompts.registry import IPromptRegistry
from ...interfaces.workflow.graph import IWorkflow

class WorkflowBuilder:
    """工作流构建器"""
    
    def __init__(
        self,
        config_loader: IWorkflowConfigLoader,
        registry: IPromptRegistry
    ):
        self.config_loader = config_loader
        self.registry = registry
    
    async def build_from_file(self, config_path: Path) -> IWorkflow:
        """从文件构建工作流"""
        # 加载配置
        config = await self.config_loader.load_config(config_path)
        
        # 构建工作流
        return await self.build_from_config(config)
    
    async def build_from_config(self, config: Dict[str, Any]) -> IWorkflow:
        """从配置构建工作流"""
        # 创建工作流实例
        workflow = self._create_workflow_instance(config)
        
        # 添加节点
        await self._add_nodes(workflow, config['nodes'])
        
        # 添加边
        await self._add_edges(workflow, config['edges'])
        
        # 设置入口点
        if 'entry_point' in config:
            workflow.set_entry_point(config['entry_point'])
        
        return workflow
    
    def _create_workflow_instance(self, config: Dict[str, Any]) -> IWorkflow:
        """创建工作流实例"""
        metadata = config.get('metadata', {})
        return Workflow(
            workflow_id=metadata.get('name', 'unnamed'),
            name=metadata.get('name', 'Unnamed Workflow'),
            description=metadata.get('description', ''),
            version=metadata.get('version', '1.0.0')
        )
    
    async def _add_nodes(self, workflow: IWorkflow, nodes_config: Dict[str, Any]) -> None:
        """添加节点"""
        for node_id, node_config in nodes_config.items():
            node = await self._create_node(node_id, node_config)
            workflow.add_node(node)
    
    async def _add_edges(self, workflow: IWorkflow, edges_config: List[Dict[str, Any]]) -> None:
        """添加边"""
        for edge_config in edges_config:
            edge = self._create_edge(edge_config)
            workflow.add_edge(edge)
    
    async def _create_node(self, node_id: str, node_config: Dict[str, Any]) -> INode:
        """创建节点"""
        function_name = node_config.get('function')
        config = node_config.get('config', {})
        
        # 根据函数名称创建相应的节点
        if function_name == 'prompt_injection_node':
            return await self._create_prompt_injection_node(config)
        elif function_name == 'enhanced_llm_node':
            return await self._create_enhanced_llm_node(config)
        else:
            return await self._create_generic_node(function_name, config)
    
    async def _create_prompt_injection_node(self, config: Dict[str, Any]) -> INode:
        """创建提示词注入节点"""
        from ...core.workflow.graph.node_functions.prompt_nodes import create_prompt_injection_node
        
        prompt_config = config.get('prompt_config')
        injector = await self._create_prompt_injector()
        
        node_func = create_prompt_injection_node(injector, prompt_config)
        
        return Node(
            id="prompt_injection",
            function=node_func,
            config=config
        )
    
    async def _create_enhanced_llm_node(self, config: Dict[str, Any]) -> INode:
        """创建增强的LLM节点"""
        from ...core.workflow.graph.node_functions.enhanced_llm_node import create_enhanced_llm_node
        
        llm_client = config.get('llm_client')
        prompt_config = config.get('prompts')
        
        node_func = await create_enhanced_llm_node(llm_client, prompt_config)
        
        return Node(
            id="enhanced_llm",
            function=node_func,
            config=config
        )
```

## 总结

本文档分析了当前的提示词配置系统，并提出了与提示词模块的集成方案。主要内容包括：

1. **当前系统分析**：详细分析了现有的提示词文件结构、格式和分类
2. **集成方案设计**：提出了增强的元数据格式、注册表系统和引用解析机制
3. **LLM节点配置分析**：比较了专门节点注入和直接配置两种方式的优缺点
4. **工作流构建方案**：设计了完整的配置文件加载和构建流程

通过这些改进，可以实现：

- **配置驱动**：工作流完全由配置文件驱动，支持引用和继承
- **类型安全**：强类型的配置解析和验证
- **高性能**：缓存机制和异步加载
- **高可扩展性**：插件化的提示词类型系统
- **易用性**：直观的配置格式和引用语法

建议按照本文档的设计逐步实施，并在实施过程中进行充分的测试和验证。