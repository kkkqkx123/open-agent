# 提示词管理模块使用指南

## 概述

提示词管理模块提供了提示词的资产化管理功能，支持简单和复合提示词，提供统一的注册、加载、合并机制。该模块是Modular Agent框架的核心组件之一，负责管理和注入各种类型的提示词。

## 核心组件

### 1. 提示词注册表 (PromptRegistry)

提示词注册表负责管理所有提示词的元信息，包括名称、类别、路径、描述等。

```python
from src.infrastructure.config_loader import YamlConfigLoader
from src.prompts.registry import PromptRegistry

# 初始化配置加载器
config_loader = YamlConfigLoader("configs")

# 创建提示词注册表
registry = PromptRegistry(config_loader)

# 验证注册表完整性
registry.validate_registry()

# 列出指定类别的所有提示词
system_prompts = registry.list_prompts("system")

# 获取特定提示词的元信息
assistant_meta = registry.get_prompt_meta("system", "assistant")
```

### 2. 提示词加载器 (PromptLoader)

提示词加载器负责从文件系统加载提示词内容，支持简单提示词和复合提示词。

```python
from src.prompts.loader import PromptLoader

# 创建提示词加载器
loader = PromptLoader(registry)

# 加载简单提示词
assistant_prompt = loader.load_prompt("system", "assistant")

# 加载复合提示词
coder_prompt = loader.load_prompt("system", "coder")

# 清空缓存
loader.clear_cache()
```

### 3. 提示词注入器 (PromptInjector)

提示词注入器负责将提示词注入到Agent状态中，按照系统→规则→用户指令的顺序注入。

```python
from src.prompts.injector import PromptInjector
from src.prompts.models import PromptConfig
from src.prompts.agent_state import AgentState

# 创建提示词注入器
injector = PromptInjector(loader)

# 配置提示词
config = PromptConfig(
    system_prompt="assistant",
    rules=["safety", "format"],
    user_command="data_analysis"
)

# 注入提示词到Agent状态
state = AgentState()
state = injector.inject_prompts(state, config)
```

## 提示词类型

### 1. 系统提示词 (System Prompts)

系统提示词定义Agent的基础角色和行为，位于`prompts/system/`目录下。

#### 简单系统提示词

```markdown
---
description: 通用助手提示词，定义Agent基础角色
---
你是一个通用助手，负责解答用户问题，语言简洁明了。
```

#### 复合系统提示词

复合提示词由一个主文件和多个子章节文件组成：

```
prompts/system/coder/
├── index.md              # 主文件
├── 01_code_style.md      # 子章节1
└── 02_error_handling.md  # 子章节2
```

主文件 (`index.md`):
```markdown
---
description: 代码生成专家系统提示词
---
你是一个代码生成专家，负责生成高质量、可维护的代码。
```

子章节文件 (`01_code_style.md`):
```markdown
---
description: 代码风格规范
---
请遵循以下代码风格：
- 使用PEP8规范
- 添加适当的注释
- 使用有意义的变量名
```

### 2. 规则提示词 (Rule Prompts)

规则提示词定义Agent必须遵循的规则和约束，位于`prompts/rules/`目录下。

```markdown
---
description: 安全规则提示词
---
请遵循以下安全规则：
- 不生成有害、违法或不道德的内容
- 不提供危险活动的指导
- 尊重用户隐私，不要求提供敏感个人信息
```

### 3. 用户指令 (User Commands)

用户指令定义特定任务的执行指令，位于`prompts/user_commands/`目录下。

```markdown
---
description: 数据分析用户指令
---
请分析提供的数据，并给出以下内容：
1. 数据概览和基本统计信息
2. 数据质量评估
3. 关键发现和洞察
4. 建议的后续分析方向
```

## 配置管理

### 提示词注册表配置

提示词注册表配置文件位于`configs/prompts.yaml`：

```yaml
# 提示词注册表配置
system:
  - name: assistant
    path: prompts/system/assistant.md
    description: 通用助手系统提示词
  - name: coder
    path: prompts/system/coder/
    description: 代码生成专家系统提示词
    is_composite: true

rules:
  - name: safety
    path: prompts/rules/safety.md
    description: 安全规则提示词
  - name: format
    path: prompts/rules/format.md
    description: 输出格式规则提示词

user_commands:
  - name: data_analysis
    path: prompts/user_commands/data_analysis.md
    description: 数据分析用户指令
  - name: code_review
    path: prompts/user_commands/code_review.md
    description: 代码审查用户指令
```

### Agent配置

Agent配置可以指定要使用的提示词：

```yaml
# configs/agents/data_analyst.yaml
name: data_analyst
description: 数据分析专家Agent
system_prompt: coder
rules:
  - safety
  - format
user_command: data_analysis
llm_config: openai-gpt4
tool_sets:
  - data_analysis_set
```

## LangGraph集成

提示词管理模块提供了与LangGraph的集成支持：

```python
from src.prompts.langgraph_integration import create_agent_workflow

# 创建LangGraph工作流
workflow = create_agent_workflow(prompt_injector, llm_client)

# 运行工作流
result = workflow.invoke({"messages": []})
```

如果LangGraph不可用，也可以使用简单工作流：

```python
from src.prompts.langgraph_integration import create_simple_workflow

# 创建简单工作流
workflow = create_simple_workflow(prompt_injector)

# 运行工作流
result_state = workflow["run"]()
```

## 缓存机制

提示词加载器内置了缓存机制，避免重复文件读取：

```python
# 第一次加载会从文件系统读取
content1 = loader.load_prompt("system", "assistant")

# 第二次加载会从缓存获取
content2 = loader.load_prompt("system", "assistant")

# 清空缓存
loader.clear_cache()
```

## 错误处理

提示词管理模块提供了完善的错误处理机制：

```python
try:
    # 加载不存在的提示词
    content = loader.load_prompt("system", "nonexistent")
except ValueError as e:
    print(f"错误: {e}")

try:
    # 注入不存在的提示词
    config = PromptConfig(system_prompt="nonexistent")
    state = injector.inject_prompts(AgentState(), config)
except ValueError as e:
    print(f"错误: {e}")
```

## 最佳实践

1. **提示词组织**：按照功能分类组织提示词，使用清晰的命名约定
2. **元信息**：为每个提示词提供清晰的描述，便于管理和维护
3. **复合提示词**：对于复杂的提示词，使用复合结构提高可维护性
4. **缓存管理**：在开发环境中定期清空缓存以确保使用最新内容
5. **错误处理**：始终使用try-except处理可能的错误情况

## 演示

运行演示程序查看提示词管理模块的完整功能：

```bash
python demo_prompt_management.py
```

## 测试

运行测试套件验证模块功能：

```bash
# 运行所有提示词测试
pytest tests/prompts/

# 运行特定测试
pytest tests/prompts/test_registry.py
pytest tests/prompts/test_loader.py
pytest tests/prompts/test_injector.py
pytest tests/prompts/test_integration.py
```

---

*文档版本：V1.0*  
*创建日期：2025-10-20*