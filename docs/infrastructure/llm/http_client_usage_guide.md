# HTTP客户端使用指南

本文档介绍如何使用新的HTTP客户端基础设施层，包括基本用法、配置管理和最佳实践。

## 1. 快速开始

### 1.1 基本使用

```python
from src.infrastructure.llm.http_client import create_http_client
from src.infrastructure.messages import HumanMessage, AIMessage

# 创建OpenAI客户端
client = create_http_client(
    provider="openai",
    model="gpt-4",
    api_key="your-api-key-here"
)

# 发送消息
messages = [HumanMessage(content="Hello, how are you?")]
response = await client.chat_completions(
    messages=messages,
    model="gpt-4"
)

print(response.content)
```

### 1.2 使用配置文件

```python
from src.infrastructure.llm.http_client import get_http_client_factory

# 使用配置文件创建客户端
factory = get_http_client_factory()
client = factory.create_client(
    provider="openai",
    model="gpt-4"
    # API密钥将从配置文件中读取
)
```

## 2. 支持的提供商

### 2.1 OpenAI

```python
# OpenAI客户端
openai_client = create_http_client(
    provider="openai",
    model="gpt-4",
    api_key="${OPENAI_API_KEY}"  # 支持环境变量
)

# 支持的模型
models = openai_client.get_supported_models()
print(models)  # ['gpt-4', 'gpt-4-turbo', 'gpt-4o', ...]

# 使用Responses API (GPT-5)
response = await openai_client.responses_api(
    input_text="Explain quantum computing",
    model="gpt-5",
    parameters={
        "reasoning_effort": "high",
        "verbosity": "detailed"
    }
)
```

### 2.2 Gemini

```python
# Gemini客户端
gemini_client = create_http_client(
    provider="gemini",
    model="gemini-1.5-pro",
    api_key="${GOOGLE_API_KEY}"
)

# 支持多模态内容
from src.infrastructure.messages import HumanMessage

messages = [
    HumanMessage(content=[
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", "image_url": "https://example.com/image.jpg"}
    ])
]

response = await gemini_client.chat_completions(
    messages=messages,
    model="gemini-1.5-pro"
)
```

### 2.3 Anthropic

```python
# Anthropic客户端
anthropic_client = create_http_client(
    provider="anthropic",
    model="claude-3-sonnet-20240229",
    api_key="${ANTHROPIC_API_KEY}"
)

# 支持长文本
long_text = "..."  # 很长的文本
messages = [HumanMessage(content=long_text)]

response = await anthropic_client.chat_completions(
    messages=messages,
    model="claude-3-sonnet-20240229",
    parameters={
        "max_tokens": 4096
    }
)
```

## 3. 流式响应

### 3.1 基本流式使用

```python
# 流式响应
stream_response = client.chat_completions(
    messages=[HumanMessage(content="Tell me a story")],
    model="gpt-4",
    stream=True
)

async for chunk in stream_response:
    print(chunk, end="", flush=True)
print()  # 换行
```

### 3.2 流式响应处理

```python
async def process_stream_response(client, messages, model):
    """处理流式响应的完整示例"""
    response_chunks = []
    
    try:
        async for chunk in client.chat_completions(
            messages=messages,
            model=model,
            stream=True
        ):
            response_chunks.append(chunk)
            print(chunk, end="", flush=True)
            
    except Exception as e:
        print(f"\n流式响应出错: {e}")
        return None
    
    full_response = "".join(response_chunks)
    return full_response

# 使用示例
full_text = await process_stream_response(
    client,
    [HumanMessage(content="Explain machine learning")],
    "gpt-4"
)
```

## 4. 工具调用

### 4.1 定义工具

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius"
                }
            },
            "required": ["location"]
        }
    }
]
```

### 4.2 使用工具调用

```python
# OpenAI工具调用
response = await openai_client.chat_completions(
    messages=[
        HumanMessage(content="What's the weather in Tokyo?")
    ],
    model="gpt-4",
    parameters={
        "tools": tools,
        "tool_choice": "auto"
    }
)

# 检查是否有工具调用
if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]
        
        # 执行工具调用
        if function_name == "get_weather":
            result = get_weather(**json.loads(arguments))
            
            # 发送工具结果
            from src.infrastructure.messages import ToolMessage
            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
            
            # 继续对话
            followup_response = await openai_client.chat_completions(
                messages=[
                    HumanMessage(content="What's the weather in Tokyo?"),
                    response.message,
                    tool_message
                ],
                model="gpt-4"
            )
```

## 5. 配置管理

### 5.1 配置文件结构

```yaml
# configs/llms/provider/openai/http_client_common.yaml
provider: openai
base_url: "https://api.openai.com/v1"
api_key: "${OPENAI_API_KEY}"

timeout: 30
max_retries: 3
retry_delay: 1.0
backoff_factor: 2.0
pool_connections: 10

features:
  function_calling: true
  streaming: true
  vision: true
  responses_api: true

defaults:
  temperature: 0.7
  max_tokens: 2048
  top_p: 1.0
  frequency_penalty: 0.0
  presence_penalty: 0.0

models:
  - "gpt-4"
  - "gpt-4-turbo"
  - "gpt-4o"
  - "gpt-3.5-turbo"
```

### 5.2 模型特定配置

```yaml
# configs/llms/provider/openai/gpt-5-http.yaml
inherits_from: "provider/openai/http_client_common.yaml"

models:
  - "gpt-5"
  - "gpt-5-turbo"

parameters:
  temperature: 0.7
  max_tokens: 8192
  timeout: 60
  reasoning_effort: "medium"

features:
  responses_api: true

api_endpoints:
  chat_completions: "/chat/completions"
  responses: "/responses"

priority: 100
```

### 5.3 环境变量配置

```bash
# 设置环境变量
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_API_KEY="your-google-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 5.4 配置继承

```yaml
# 子配置可以继承父配置
inherits_from: "provider/openai/http_client_common.yaml"

# 覆盖特定设置
timeout: 60
max_retries: 5

# 添加新的设置
custom_setting: "value"
```

## 6. 错误处理

### 6.1 基本错误处理

```python
try:
    response = await client.chat_completions(
        messages=messages,
        model=model
    )
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"API调用失败: {e}")
```

### 6.2 重试机制

```python
# HTTP客户端内置重试机制
client = create_http_client(
    provider="openai",
    api_key="your-key",
    max_retries=3,        # 最大重试次数
    retry_delay=1.0,      # 重试延迟
    backoff_factor=2.0    # 退避因子
)
```

### 6.3 超时控制

```python
# 设置超时
client = create_http_client(
    provider="openai",
    api_key="your-key",
    timeout=60  # 60秒超时
)

# 单次请求超时
response = await client.chat_completions(
    messages=messages,
    model=model,
    parameters={"timeout": 30}  # 30秒超时
)
```

## 7. 性能优化

### 7.1 连接池配置

```python
# 优化连接池
client = create_http_client(
    provider="openai",
    api_key="your-key",
    pool_connections=20,  # 连接池大小
    timeout=30
)
```

### 7.2 客户端缓存

```python
# 客户端会被自动缓存
client1 = create_http_client("openai", "gpt-4", "key")
client2 = create_http_client("openai", "gpt-4", "key")

assert client1 is client2  # 同一个实例
```

### 7.3 批量请求

```python
import asyncio

async def batch_requests(client, messages_list, model):
    """批量处理请求"""
    tasks = []
    for messages in messages_list:
        task = client.chat_completions(messages, model)
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return responses

# 使用示例
messages_batches = [
    [HumanMessage(content=f"Question {i}")]
    for i in range(10)
]

responses = await batch_requests(client, messages_batches, "gpt-4")
```

## 8. 监控和日志

### 8.1 启用调试日志

```python
import logging
from src.services.logger import get_logger

# 设置日志级别
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# 现在HTTP客户端会输出详细的调试信息
```

### 8.2 自定义日志处理

```python
# HTTP客户端会自动记录请求和响应信息
# 包括：
# - 请求URL和参数
# - 响应状态码和时间
# - 错误信息和重试次数
# - Token使用情况
```

## 9. 最佳实践

### 9.1 安全性

```python
# ✅ 好的做法：使用环境变量
client = create_http_client(
    provider="openai",
    api_key="${OPENAI_API_KEY}"
)

# ❌ 避免的做法：硬编码API密钥
client = create_http_client(
    provider="openai",
    api_key="sk-1234567890abcdef"  # 不要这样做！
)
```

### 9.2 资源管理

```python
# 使用异步上下文管理器
async with create_http_client("openai", "key") as client:
    response = await client.chat_completions(messages, "gpt-4")
    # 客户端会自动关闭

# 或者手动关闭
client = create_http_client("openai", "key")
try:
    response = await client.chat_completions(messages, "gpt-4")
finally:
    await client.close()
```

### 9.3 配置管理

```python
# ✅ 好的做法：使用配置文件
factory = get_http_client_factory(config_dir="custom/config")
client = factory.create_client("openai", "gpt-4")

# ✅ 好的做法：环境特定配置
# configs/llms/provider/openai/production.yaml
# configs/llms/provider/openai/development.yaml
```

### 9.4 错误处理

```python
# ✅ 好的做法：完整的错误处理
async def safe_api_call(client, messages, model):
    try:
        response = await client.chat_completions(messages, model)
        return response
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        raise
    except Exception as e:
        logger.error(f"API调用失败: {e}")
        # 可以在这里实现降级逻辑
        raise
```

## 10. 故障排除

### 10.1 常见问题

**Q: API密钥错误**
```
A: 检查环境变量是否正确设置，或配置文件中的API密钥格式
```

**Q: 连接超时**
```
A: 增加timeout设置，或检查网络连接
```

**Q: 模型不支持**
```
A: 检查模型名称是否正确，使用get_supported_models()查看支持的模型
```

**Q: 配置文件找不到**
```
A: 确认配置文件路径正确，文件格式为YAML
```

### 10.2 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查客户端配置
client = create_http_client("openai", "key")
print(f"支持的模型: {client.get_supported_models()}")
print(f"提供商: {client.get_provider_name()}")

# 测试配置发现
from src.infrastructure.llm.config import ConfigDiscovery
discovery = ConfigDiscovery()
configs = discovery.discover_configs("openai")
print(f"发现的配置: {configs}")
```

这个HTTP客户端系统提供了完整的LLM提供商支持，包括配置管理、错误处理、性能优化等功能，可以满足各种使用场景的需求。