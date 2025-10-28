# HumanRelay LLM 使用指南

## 概述

HumanRelay LLM 是一个创新的LLM客户端，它通过前端界面与用户交互，让用户手动将提示词输入到Web端的LLM中，然后将回复粘贴回系统。这种设计适用于需要人工介入或无法直接访问API的场景。

## 快速开始

### 1. 基本使用

```python
from src.infrastructure.llm.factory import create_client

# 创建HumanRelay客户端（单轮模式）
config = {
    "model_type": "human-relay-s",
    "model_name": "human-relay-s",
    "parameters": {
        "mode": "single",
        "frontend_timeout": 300
    }
}

client = create_client(config)

# 使用方式与其他LLM客户端相同
messages = [
    {"role": "user", "content": "请帮我分析这段代码..."}
]

response = await client.generate_async(messages)
print(f"Web LLM回复: {response.content}")
```

### 2. 多轮对话模式

```python
# 创建多轮对话模式的客户端
config = {
    "model_type": "human-relay-m", 
    "model_name": "human-relay-m",
    "parameters": {
        "mode": "multi",
        "max_history_length": 50
    }
}

client = create_client(config)

# 多轮对话示例
messages1 = [{"role": "user", "content": "什么是人工智能？"}]
response1 = await client.generate_async(messages1)

messages2 = [{"role": "user", "content": "能详细解释一下机器学习吗？"}]
response2 = await client.generate_async(messages2)  # 会保留对话历史
```

## 配置说明

### 基础配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_type` | string | `human_relay` | 必须为 `human_relay`、`human-relay-s` 或 `human-relay-m` |
| `model_name` | string | - | 模型名称标识 |
| `mode` | string | `single` | 模式：`single`（单轮）或 `multi`（多轮） |
| `frontend_timeout` | int | 300 | 前端等待超时时间（秒） |
| `max_history_length` | int | 50 | 多轮对话最大历史长度 |

### 高级配置

```yaml
# configs/llms/provider/human_relay/advanced.yaml
inherits_from: "../common.yaml"
model_name: human-relay-advanced

parameters:
  mode: "multi"
  frontend_timeout: 600  # 10分钟超时
  max_history_length: 100

human_relay_config:
  prompt_template: |
    🎯 **任务说明**
    
    请将以下内容复制到您喜欢的Web LLM中：
    
    ```
    {prompt}
    ```
    
    📝 **请将Web LLM的完整回复粘贴到下方：**
    
  incremental_prompt_template: |
    🔄 **继续对话**
    
    请继续将以下内容输入到Web LLM中：
    
    ```
    {incremental_prompt}
    ```
    
    📋 **对话历史：**
    {conversation_history}
    
    📝 **请将Web LLM的回复粘贴到下方：**
    
  frontend_interface:
    interface_type: "tui"
    tui_config:
      prompt_style: "minimal"
      input_area_height: 15
      show_timer: true

metadata:
  description: "高级HumanRelay配置"
  capabilities:
    - human_interaction
    - web_llm_integration  
    - conversation_history
    - custom_templates
```

## 使用场景

### 1. 代码审查

```python
# 使用HumanRelay进行代码审查
code_review_prompt = """
请审查以下Python代码，指出潜在问题和改进建议：

```python
def process_data(data):
    result = []
    for item in data:
        if item > 10:
            result.append(item * 2)
    return result
```

请从代码风格、性能、可读性等方面进行分析。
"""

messages = [{"role": "user", "content": code_review_prompt}]
response = await client.generate_async(messages)
```

### 2. 多轮技术讨论

```python
# 多轮技术讨论示例
config = {
    "model_type": "human-relay-m",
    "model_name": "human-relay-m",
    "parameters": {"mode": "multi"}
}
client = create_client(config)

# 第一轮：概念解释
messages1 = [{"role": "user", "content": "请解释什么是微服务架构？"}]
response1 = await client.generate_async(messages1)

# 第二轮：深入探讨
messages2 = [{"role": "user", "content": "微服务架构与单体架构相比有哪些优缺点？"}]
response2 = await client.generate_async(messages2)

# 第三轮：实践建议  
messages3 = [{"role": "user", "content": "在什么场景下适合使用微服务架构？"}]
response3 = await client.generate_async(messages3)
```

### 3. 创意写作

```python
# 创意写作场景
creative_prompt = """
请帮我创作一个关于人工智能的短篇科幻故事，要求：
1. 包含AI与人类的互动
2. 有戏剧性冲突
3. 字数在500字左右
4. 包含技术细节但易于理解
"""

messages = [{"role": "user", "content": creative_prompt}]
response = await client.generate_async(messages)
```

## 在Agent中使用

### 1. Agent配置示例

```yaml
# configs/agents/human-relay-coder.yaml
inherits_from: "../_group.yaml#default_group"
name: "human-relay-coder"
description: "使用HumanRelay的代码助手Agent"

# LLM配置
llm:
  model_type: "human-relay-s"
  model_name: "human-relay-s"
  parameters:
    mode: "single"
    frontend_timeout: 600  # 代码审查可能需要更长时间

# 工具配置
tools:
  - calculator
  - database

# 系统提示词
system_prompt: |
  你是一个专业的代码审查助手。请仔细分析用户提供的代码，
  指出潜在问题并提供改进建议。

# 工作流配置
workflow: "react_workflow"
```

### 2. 在Workflow中使用

```python
# 在自定义Workflow中使用HumanRelay
from src.application.workflow.react_workflow import ReActWorkflow

workflow_config = {
    "llm": {
        "model_type": "human-relay-m",
        "model_name": "human-relay-m", 
        "parameters": {"mode": "multi"}
    },
    "tools": ["calculator", "database"],
    "max_iterations": 5
}

workflow = ReActWorkflow(workflow_config)
```

## 前端交互

### TUI界面

在TUI模式下，HumanRelay会显示一个专门的交互界面：

```
╭─────────────────────────────────────────────────────────────╮
│                    HumanRelay 交互界面                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 请将以下提示词输入到Web LLM中，并将回复粘贴回来：            │
│                                                             │
│ 用户：请帮我分析这段代码...                                 │
│ AI：这是一个代码分析请求...                                 │
│ 用户：具体说明性能优化建议                                  │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│ 回复：                                                     │
│ ___________________________________________________________ │
│                                                             │
│ [确认] [取消] [超时: 04:59]                                │
╰─────────────────────────────────────────────────────────────╯
```

### Web界面（规划中）

Web界面将通过WebSocket与前端通信，提供更丰富的交互体验。

## 最佳实践

### 1. 超时设置建议

```yaml
# 不同场景的超时设置
parameters:
  # 简单问答
  frontend_timeout: 180  # 3分钟
  
  # 代码审查
  frontend_timeout: 600  # 10分钟
  
  # 复杂分析
  frontend_timeout: 1200 # 20分钟
```

### 2. 历史管理策略

```yaml
# 多轮对话历史管理
parameters:
  mode: "multi"
  max_history_length: 50  # 平衡记忆和性能
  
  # 对于长对话场景
  max_history_length: 100
  
  # 对于敏感信息场景  
  max_history_length: 10  # 限制历史记录
```

### 3. 模板定制技巧

```yaml
human_relay_config:
  prompt_template: |
    🔍 **分析任务**
    
    请使用Web LLM分析以下内容：
    
    {prompt}
    
    💡 **分析要求：**
    - 提供详细的分析过程
    - 给出具体的改进建议
    - 使用中文回复
    
    📋 **回复内容：**
    
  incremental_prompt_template: |
    🔄 **继续分析**
    
    请基于之前的分析，继续处理：
    
    {incremental_prompt}
    
    📜 **分析历史：**
    {conversation_history}
    
    📋 **新的分析结果：**
```

## 故障排除

### 1. 常见问题

**问题**: 前端交互超时
```python
# 解决方案：增加超时时间
config = {
    "model_type": "human-relay-s",
    "parameters": {
        "frontend_timeout": 600  # 增加到10分钟
    }
}
```

**问题**: 内存使用过高
```python
# 解决方案：限制历史长度
config = {
    "model_type": "human-relay-m", 
    "parameters": {
        "max_history_length": 20  # 减少历史记录
    }
}
```

**问题**: 提示词格式不清晰
```yaml
# 解决方案：优化模板
human_relay_config:
  prompt_template: |
    ════════════════════════════════════════════
    🎯 任务指令
    ════════════════════════════════════════════
    
    {prompt}
    
    ════════════════════════════════════════════
    📝 请在此处粘贴Web LLM的回复：
    ════════════════════════════════════════════
```

### 2. 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查配置
print(f"模式: {client.mode}")
print(f"历史长度: {len(client.conversation_history)}")
print(f"超时设置: {client.config.parameters.get('frontend_timeout')}")
```

## 性能优化

### 1. 内存优化

```yaml
# 优化内存使用
parameters:
  max_history_length: 30  # 限制历史记录
  cleanup_interval: 1800  # 30分钟清理一次

human_relay_config:
  frontend_interface:
    tui_config:
      input_area_height: 8  # 减少显示区域
```

### 2. 响应时间优化

```python
# 使用单轮模式减少交互时间
config = {
    "model_type": "human-relay-s",
    "parameters": {
        "frontend_timeout": 180  # 3分钟超时
    }
}
```

## 扩展开发

### 1. 自定义前端接口

```python
from src.infrastructure.llm.frontend_interface import FrontendInterface

class CustomFrontend(FrontendInterface):
    """自定义前端接口"""
    
    async def prompt_user(self, prompt: str, mode: str, **kwargs) -> str:
        # 实现自定义前端逻辑
        return await self._custom_prompt_implementation(prompt, mode, **kwargs)
```

### 2. 自定义模板引擎

```python
from src.infrastructure.llm.clients.human_relay import HumanRelayClient

class CustomHumanRelayClient(HumanRelayClient):
    """自定义HumanRelay客户端"""
    
    def _build_full_prompt(self, messages):
        # 实现自定义提示词构建逻辑
        return self._custom_prompt_builder(messages)
```

## 总结

HumanRelay LLM 提供了一个灵活的人工介入解决方案，特别适用于：

- **敏感任务**: 需要人工审核的敏感操作
- **复杂分析**: 需要人类专家参与的复杂分析
- **教育场景**: 教学和演示场景
- **调试辅助**: 帮助调试和验证LLM输出

通过合理的配置和使用，HumanRelay可以成为您LLM工作流中强大的辅助工具。