# HumanRelay LLM 配置模板

## 配置文件结构

### 1. 通用配置模板

```yaml
# configs/llms/provider/human_relay/common.yaml
# HumanRelay通用配置
model_type: human_relay
base_url: null  # 不使用API端点

parameters:
  mode: "single"  # single 或 multi
  frontend_timeout: 300  # 前端等待超时时间（秒）
  max_history_length: 50  # 多轮对话最大历史长度

# HumanRelay特定配置
human_relay_config:
  prompt_template: |
    请将以下提示词输入到Web LLM中，并将回复粘贴回来：
    
    {prompt}
    
    回复：
  incremental_prompt_template: |
    请继续对话，将以下提示词输入到Web LLM中：
    
    {incremental_prompt}
    
    对话历史：
    {conversation_history}
    
    回复：
  frontend_interface:
    interface_type: "tui"  # tui 或 web
    tui_config:
      prompt_style: "highlight"
      input_area_height: 10
    web_config:
      endpoint: "/api/human-relay"
      websocket: true

# 元数据
metadata:
  provider: human_relay
  version: "1.0"
  description: "HumanRelay LLM - 通过前端与Web LLM交互"
  capabilities:
    - human_interaction
    - web_llm_integration
    - configurable_modes
```

### 2. 单轮对话模式配置

```yaml
# configs/llms/provider/human_relay/human-relay-s.yaml
inherits_from: "../common.yaml"
model_name: human-relay-s

parameters:
  mode: "single"

metadata:
  description: "HumanRelay单轮对话模式"
  capabilities:
    - human_interaction
    - web_llm_integration
```

### 3. 多轮对话模式配置

```yaml
# configs/llms/provider/human_relay/human-relay-m.yaml
inherits_from: "../common.yaml"
model_name: human-relay-m

parameters:
  mode: "multi"
  max_history_length: 100  # 扩展历史长度

metadata:
  description: "HumanRelay多轮对话模式"
  capabilities:
    - human_interaction
    - web_llm_integration
    - conversation_history
```

### 4. 自定义提示词模板配置

```yaml
# configs/llms/provider/human_relay/custom-template.yaml
inherits_from: "../common.yaml"
model_name: human-relay-custom

parameters:
  mode: "single"

human_relay_config:
  prompt_template: |
    🎯 **任务说明**
    
    请将以下内容复制到Web LLM中执行：
    
    ```
    {prompt}
    ```
    
    📝 **请将Web LLM的回复粘贴到下方：**
    
  incremental_prompt_template: |
    🔄 **继续对话**
    
    请将以下内容复制到Web LLM中继续对话：
    
    ```
    {incremental_prompt}
    ```
    
    📋 **对话历史：**
    {conversation_history}
    
    📝 **请将Web LLM的回复粘贴到下方：**

metadata:
  description: "HumanRelay自定义模板模式"
  capabilities:
    - human_interaction
    - web_llm_integration
    - custom_templates
```

## 配置参数说明

### 基础参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_type` | string | `human_relay` | 必须为 `human_relay` |
| `model_name` | string | - | 模型名称标识 |
| `mode` | string | `single` | 模式：`single` 或 `multi` |
| `frontend_timeout` | int | 300 | 前端等待超时时间（秒） |
| `max_history_length` | int | 50 | 多轮对话最大历史长度 |

### HumanRelay特定参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt_template` | string | 见上文 | 单轮模式提示词模板 |
| `incremental_prompt_template` | string | 见上文 | 多轮模式提示词模板 |
| `frontend_interface.interface_type` | string | `tui` | 前端类型：`tui` 或 `web` |
| `frontend_interface.tui_config.prompt_style` | string | `highlight` | TUI提示词样式 |
| `frontend_interface.tui_config.input_area_height` | int | 10 | TUI输入区域高度 |

## 模板变量说明

### 单轮模式模板变量

- `{prompt}`: 完整的提示词内容

### 多轮模式模板变量

- `{incremental_prompt}`: 增量提示词（仅最新消息）
- `{conversation_history}`: 格式化的对话历史

## 使用示例

### 1. 基础使用

```python
from src.infrastructure.llm.factory import create_client

# 使用单轮模式
config = {
    "model_type": "human-relay-s",
    "model_name": "human-relay-s",
    "parameters": {
        "mode": "single",
        "frontend_timeout": 300
    }
}

client = create_client(config)
```

### 2. 自定义配置

```python
# 使用自定义模板
config = {
    "model_type": "human_relay",
    "model_name": "human-relay-custom",
    "parameters": {
        "mode": "multi",
        "frontend_timeout": 600,  # 10分钟超时
        "max_history_length": 100
    },
    "human_relay_config": {
        "prompt_template": "自定义提示词模板...",
        "frontend_interface": {
            "interface_type": "tui",
            "tui_config": {
                "prompt_style": "minimal",
                "input_area_height": 15
            }
        }
    }
}

client = create_client(config)
```

### 3. 在Agent配置中使用

```yaml
# configs/agents/human-relay-agent.yaml
inherits_from: "../_group.yaml#default_group"
name: "human-relay-agent"
description: "使用HumanRelay的Agent"

# LLM配置
llm:
  model_type: "human-relay-s"
  model_name: "human-relay-s"
  parameters:
    mode: "single"
    frontend_timeout: 300

# 工具配置
tools:
  - calculator
  - database

# 工作流配置
workflow: "react_workflow"
```

## 最佳实践

### 1. 超时设置

- **开发环境**: 设置较短的超时时间（如60秒）便于测试
- **生产环境**: 根据实际需求设置合理的超时时间（300-600秒）
- **长任务**: 对于复杂任务可设置更长的超时时间

### 2. 历史管理

- **单轮模式**: 不需要管理历史，适合独立任务
- **多轮模式**: 设置合适的 `max_history_length` 避免内存溢出
- **敏感信息**: 注意对话历史中可能包含敏感信息

### 3. 模板设计

- **清晰指示**: 明确告诉用户需要做什么
- **格式友好**: 使用合适的格式（如代码块）提高可读性
- **上下文充分**: 在多轮模式中提供足够的对话历史

### 4. 错误处理

```yaml
# 错误处理配置示例
parameters:
  frontend_timeout: 300
  max_retries: 3
  fallback_enabled: true
  fallback_models:
    - "mock"  # 超时时回退到Mock模型
```

## 环境变量配置

可以通过环境变量配置敏感信息：

```yaml
# 在配置文件中使用环境变量
frontend_interface:
  web_config:
    endpoint: "${HUMAN_RELAY_ENDPOINT:/api/human-relay}"
    auth_token: "${HUMAN_RELAY_TOKEN}"
```

## 性能调优

### 内存优化

```yaml
# 内存优化配置
parameters:
  max_history_length: 50  # 限制历史长度
  cleanup_interval: 3600  # 清理间隔（秒）
```

### 响应时间优化

```yaml
# 响应时间优化
parameters:
  frontend_timeout: 180  # 3分钟超时
  retry_timeout: 30      # 重试超时
```

这些配置模板提供了灵活的HumanRelay LLM配置选项，可以根据具体需求进行调整和扩展。