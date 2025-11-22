# 提示词模块重构指南

## 概述

本文档描述了提示词模块的重构过程，包括架构设计、实现细节和使用指南。

## 重构目标

1. **模块化设计**：将提示词功能拆分为独立的、可复用的模块
2. **类型安全**：使用强类型接口和协议确保类型安全
3. **异步支持**：所有I/O操作支持异步执行
4. **缓存优化**：实现多级缓存机制提升性能
5. **配置驱动**：通过配置文件管理提示词和工作流
6. **错误处理**：完善的错误处理和恢复机制

## 架构设计

### 核心组件

```
src/
├── interfaces/
│   ├── prompts.py              # 核心接口定义
│   ├── prompts/
│   │   ├── types.py           # 提示词类型接口
│   │   ├── cache.py           # 缓存接口
│   │   └── models.py          # 数据模型
│   └── state/
│       └── workflow.py        # 工作流状态接口
├── core/
│   ├── prompts/
│   │   ├── types/             # 提示词类型实现
│   │   ├── type_registry.py   # 类型注册表
│   │   └── error_handler.py   # 错误处理器
│   └── state/
│       ├── workflow_state.py  # 工作流状态实现
│       └── state_builder.py   # 状态构建器
├── services/
│   ├── prompts/
│   │   ├── injector.py        # 提示词注入器
│   │   ├── registry.py        # 提示词注册表
│   │   ├── reference_resolver.py # 引用解析器
│   │   └── cache/
│   │       └── memory_cache.py # 内存缓存实现
│   └── workflow/
│       └── builders/
│           └── prompt_aware_builder.py # 提示词感知构建器
└── core/workflow/
    ├── services/
    │   └── prompt_service.py  # 工作流提示词服务（通用）
    ├── graph/nodes/
    │   └── llm_node.py       # 增强的LLM节点（集成提示词服务）
    └── templates/
        └── workflow_template_processor.py # 工作流模板处理器
```

### 设计原则

1. **接口分离**：所有接口定义在 `interfaces/` 目录
2. **依赖注入**：使用依赖注入容器管理组件生命周期
3. **单一职责**：每个模块只负责一个特定功能
4. **开闭原则**：通过接口扩展功能，无需修改现有代码

## 核心功能

### 1. 提示词类型系统

#### 类型定义
```python
from src.interfaces.prompts.types import IPromptType, PromptType

class CustomPromptType(IPromptType):
    @property
    def type_name(self) -> str:
        return "custom"
    
    @property
    def injection_order(self) -> int:
        return 50
    
    async def process_prompt(self, content: str, context: Dict[str, Any]) -> str:
        # 处理提示词内容
        return processed_content
    
    def create_message(self, content: str) -> Any:
        # 创建消息对象
        return message
    
    def validate_content(self, content: str) -> List[str]:
        # 验证内容
        return errors
```

#### 注册新类型
```python
from src.core.prompts.type_registry import get_global_registry

registry = get_global_registry()
registry.register_class(CustomPromptType)
```

### 2. 缓存系统

#### 基本使用
```python
from src.services.prompts.cache.memory_cache import MemoryPromptCache
from datetime import timedelta

# 创建缓存
cache = MemoryPromptCache(
    max_size=1000,
    default_ttl=timedelta(hours=1)
)

# 使用缓存
await cache.set("key", "value", timedelta(minutes=30))
value = await cache.get("key")
```

#### 自定义淘汰策略
```python
from src.services.prompts.cache.memory_cache import ICacheEvictionPolicy

class CustomEvictionPolicy(ICacheEvictionPolicy):
    def select_victim(self, entries: List[ICacheEntry]) -> Optional[ICacheEntry]:
        # 自定义淘汰逻辑
        return selected_entry

cache = MemoryPromptCache(eviction_policy=CustomEvictionPolicy())
```

### 3. 提示词注册表

#### 注册提示词
```python
from src.services.prompts.registry import PromptRegistry
from src.interfaces.prompts.models import PromptMeta, PromptType

prompt = PromptMeta(
    id="my_prompt",
    name="My Prompt",
    type=PromptType.SYSTEM,
    content="You are a helpful assistant.",
    tags=["assistant", "helpful"],
    category="general"
)

await registry.register(prompt)
```

#### 搜索提示词
```python
from src.interfaces.prompts.models import PromptSearchCriteria, PromptStatus

criteria = PromptSearchCriteria(
    type=PromptType.SYSTEM,
    status=PromptStatus.ACTIVE,
    tags=["assistant"],
    limit=10
)

result = await registry.search(criteria)
```

### 4. 引用解析

#### 基本引用语法
```
{{ref:prompt_id}}                    # 简单引用
{{ref:prompt_id@version}}            # 带版本的引用
{{ref:prompt_id as alias}}           # 带别名的引用
{{ref:prompt_id@version as alias}}   # 完整引用语法
```

#### 条件引用
```
{{if ref:optional_prompt}}
This content only appears if the prompt exists
{{endif}}
```

#### 工作流模板语法
```
{{for step in steps}}
{{step_number}}. {{step.name}}
{{endfor}}

{{if condition}}
内容当条件为真时显示
{{else}}
内容当条件为假时显示
{{endif}}

{{variable_name}}                   # 变量替换
{{object.property}}                  # 属性访问
```

### 5. 工作流集成

#### 工作流提示词服务（通用）
```python
from src.core.workflow.services.prompt_service import get_workflow_prompt_service

# 获取全局提示词服务
prompt_service = get_workflow_prompt_service()

# 配置提示词系统
prompt_service.configure(prompt_registry, prompt_injector)

# 处理提示词内容
processed_content = await prompt_service.process_prompt_content(
    "Hello {{name}}, your task is: {{task}}",
    {"name": "Alice", "task": "analysis"}
)

# 构建消息列表
messages = await prompt_service.build_messages(
    base_messages=[SystemMessage(content="You are helpful")],
    prompt_ids=["system_prompt", "user_prompt"],
    additional_content="Please help with {{task}}",
    context={"task": "data analysis"}
)
```

#### 工作流模板处理器
```python
from src.core.workflow.templates.workflow_template_processor import WorkflowTemplateProcessor

# 处理包含工作流逻辑的模板
template = """
执行以下步骤：
{{for step in steps}}
{{step_number}}. {{step.name}} - {{step.description}}
{{endfor}}

{{if has_summary}}
总结：{{summary}}
{{endif}}
"""

context = {
    "steps": [
        {"name": "分析", "description": "分析需求"},
        {"name": "设计", "description": "设计方案"}
    ],
    "has_summary": True,
    "summary": "任务完成"
}

processed = WorkflowTemplateProcessor.process_template(template, context)
```

#### 构建提示词感知的工作流
```python
from src.services.workflow.builders.prompt_aware_builder import PromptAwareWorkflowBuilder

builder = PromptAwareWorkflowBuilder(registry, injector)

config = {
    "name": "my_workflow",
    "nodes": [
        {
            "id": "llm_node",
            "type": "llm",
            "config": {
                "max_tokens": 1000,
                "system_prompt_id": "system_prompt_id",
                "user_prompt_id": "user_prompt_id",
                "prompt_variables": {"task": "specific_task"},
                "user_input": "{{for step in steps}}处理{{step.name}}{{endfor}}"
            }
        }
    ],
    "edges": []
}

workflow = await builder.build_from_config(config)
```

## 配置系统

### 提示词配置结构

```yaml
# configs/prompts/system/base_assistant.yaml
id: base_assistant
name: Base Assistant
type: system
content: |
  You are a helpful assistant.
  Please follow these rules:
  {{ref:rules_prompt}}
status: active
priority: normal
cache_enabled: true
cache_ttl: 3600
tags:
  - assistant
  - base
category: assistant
variables:
  - name: tone
    type: string
    default_value: friendly
    description: Assistant's tone
validation:
  max_length: 5000
  required_keywords:
    - assistant
    - helpful
```

### 工作流配置

```yaml
# configs/workflows/prompt_aware_workflow.yaml
name: Prompt Aware Workflow
description: Workflow with integrated prompt system
nodes:
  - id: analyzer
    type: llm
    config:
      max_tokens: 500
      temperature: 0.3
      system_prompt_id: analyzer_system
      user_prompt_id: analyzer_user
      prompt_variables:
        analysis_type: sentiment
  
  - id: responder
    type: llm
    config:
      max_tokens: 1000
      temperature: 0.7
      system_prompt_id: responder_system
      user_prompt_id: responder_user
      prompt_variables:
        response_style: professional

edges:
  - source: analyzer
    target: responder
```

## 错误处理

### 错误类型

```python
from src.core.common.exceptions.prompts import (
    PromptError,
    PromptNotFoundError,
    PromptValidationError,
    PromptReferenceError,
    PromptCacheError,
    PromptInjectionError
)
```

### 错误恢复策略

```python
from src.core.prompts.error_handler import PromptErrorHandler, ErrorRecoveryStrategy

handler = PromptErrorHandler()

# 注册恢复策略
handler.register_strategy(
    PromptNotFoundError,
    ErrorRecoveryStrategy.USE_DEFAULT
)

# 处理错误
result = await handler.handle_error(error, context)
```

## 性能优化

### 缓存策略

1. **多级缓存**：内存缓存 + 可选的Redis缓存
2. **智能淘汰**：LRU/LFU策略自动淘汰
3. **预热机制**：启动时预加载常用提示词
4. **TTL管理**：灵活的生存时间配置

### 异步优化

1. **并发加载**：并行加载多个提示词
2. **批量操作**：支持批量注册和搜索
3. **连接池**：LLM客户端连接池管理
4. **流式处理**：大内容流式处理

## 测试指南

### 单元测试

```bash
# 运行提示词模块测试
pytest tests/unit/prompts/ -v

# 运行缓存系统测试
pytest tests/unit/prompts/test_memory_cache.py -v

# 运行类型系统测试
pytest tests/unit/prompts/test_type_registry.py -v
```

### 集成测试

```bash
# 运行工作流集成测试
pytest tests/integration/test_prompt_workflow_integration.py -v

# 运行端到端测试
pytest tests/integration/test_e2e_prompt_workflow.py -v
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src/interfaces/prompts \
       --cov=src/core/prompts \
       --cov=src/services/prompts \
       tests/
```

## 迁移指南

### 从旧版本迁移

1. **更新导入路径**
   ```python
   # 旧版本
   from src.domain.prompts import PromptManager
   
   # 新版本
   from src.services.prompts.registry import PromptRegistry
   ```

2. **替换API调用**
   ```python
   # 旧版本
   prompt = prompt_manager.get_prompt("id")
   
   # 新版本
   prompt = await registry.get("id")
   ```

3. **配置文件迁移**
   - 使用新的配置结构
   - 添加类型和验证规则
   - 启用缓存配置

### 兼容性说明

- **向后兼容**：保留旧API的包装器
- **渐进迁移**：支持新旧系统并存
- **弃用警告**：明确标记废弃功能

## 最佳实践

### 1. 提示词设计

- **模块化**：将复杂提示词拆分为可复用的小块
- **参数化**：使用变量和引用提高灵活性
- **版本管理**：为重要提示词维护版本历史
- **文档化**：为每个提示词提供清晰的描述

### 2. 工作流模板设计

- **职责分离**：工作流逻辑放在模板处理器中，提示词类型专注于内容处理
- **语法简洁**：使用直观的模板语法，避免复杂的嵌套
- **错误处理**：提供模板验证和错误提示
- **性能考虑**：避免过深的循环嵌套

### 3. 性能优化

- **合理缓存**：为静态提示词启用长TTL缓存
- **批量操作**：使用批量API减少网络开销
- **异步优先**：始终使用异步API
- **监控指标**：跟踪缓存命中率和响应时间

### 4. 错误处理

- **优雅降级**：提供默认提示词作为后备
- **详细日志**：记录错误上下文和恢复过程
- **重试机制**：对临时错误实现自动重试
- **用户友好**：向用户提供有意义的错误信息

## 故障排除

### 常见问题

1. **提示词未找到**
   - 检查注册表是否正确初始化
   - 验证提示词ID拼写
   - 确认提示词状态为active

2. **引用解析失败**
   - 检查引用语法是否正确
   - 验证被引用的提示词是否存在
   - 确认没有循环引用

3. **缓存问题**
   - 检查缓存配置是否正确
   - 验证TTL设置
   - 清理过期缓存

### 调试工具

```python
# 启用调试日志
import logging
logging.getLogger("src.services.prompts").setLevel(logging.DEBUG)

# 获取统计信息
stats = await registry.get_stats()
print(f"缓存命中率: {stats['cache_hit_rate']:.2%}")

# 验证提示词
errors = await registry.validate_all_prompts()
for error in errors:
    print(f"验证错误: {error}")
```

## 架构改进说明

### 职责分离原则

1. **提示词类型**：专注于内容处理和消息创建
2. **工作流模板处理器**：处理工作流特定的逻辑（循环、条件等）
3. **LLM节点**：集成提示词系统和工作流模板处理

### 避免的陷阱

- **功能冗余**：避免在多个地方实现相同的变量替换逻辑
- **模块耦合**：提示词模块不应包含工作流特定的逻辑
- **职责混乱**：每个组件应该有明确的单一职责

## 未来规划

### 短期目标

1. **Redis缓存支持**：实现分布式缓存
2. **模板引擎增强**：扩展工作流模板处理器功能
3. **A/B测试**：提示词效果测试框架
4. **监控面板**：实时性能监控

### 长期目标

1. **机器学习优化**：基于使用数据自动优化提示词
2. **多语言支持**：国际化提示词管理
3. **可视化编辑器**：图形化提示词编辑工具
4. **版本控制**：Git风格的提示词版本管理

## 参考资料

- [API文档](../api/prompts.md)
- [配置参考](../configuration/prompts.md)
- [示例代码](../../examples/prompts/)
- [性能基准](../performance/prompts_benchmarks.md)