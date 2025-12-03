# Anthropic API集成指南

## 概述

本文档描述了Anthropic Claude API在Modular Agent Framework中的完整集成实现，包括格式转换、工具使用、多模态支持和流式响应处理。

## 架构设计

### 模块化设计

我们采用了模块化设计，将Anthropic API的不同功能分离到专门的工具类中：

```
src/infrastructure/llm/converters/
├── anthropic_format_utils.py          # 主要格式转换器
├── anthropic_multimodal_utils.py      # 多模态内容处理
├── anthropic_tools_utils.py           # 工具使用处理
├── anthropic_stream_utils.py          # 流式响应处理
└── anthropic_validation_utils.py      # 验证和错误处理
```

### 核心组件

#### 1. AnthropicFormatUtils
主要的格式转换器，负责：
- 请求格式转换
- 响应格式转换
- 流式响应处理
- 验证集成

#### 2. AnthropicMultimodalUtils
多模态内容处理工具，支持：
- 文本内容处理
- 图像内容处理
- 内容验证
- 格式转换

#### 3. AnthropicToolsUtils
工具使用处理工具，支持：
- 工具定义转换
- 工具选择策略
- 工具调用提取
- 工具验证

#### 4. AnthropicStreamUtils
流式响应处理工具，支持：
- Server-Sent Events解析
- 流式事件处理
- 文本和工具调用提取
- 流式验证

#### 5. AnthropicValidationUtils
验证和错误处理工具，支持：
- 请求参数验证
- 响应格式验证
- 错误处理
- 友好错误消息

## 功能特性

### 1. 完整的API支持

#### 支持的模型
- `claude-sonnet-4-5` (推荐)
- `claude-3-opus`
- `claude-3-sonnet`
- `claude-3-haiku`

#### 支持的参数
```python
parameters = {
    "model": "claude-sonnet-4-5",
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "stop_sequences": ["STOP", "END"],
    "system": "You are a helpful assistant.",
    "metadata": {"user_id": "123"},
    "stream": False,
    "tools": [...],
    "tool_choice": "auto"
}
```

### 2. 工具使用支持

#### 工具定义格式
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
                }
            },
            "required": ["location"]
        }
    }
]
```

#### 工具选择策略
- `"auto"` - 自动选择工具
- `"none"` - 不使用工具
- `{"type": "any"}` - 必须使用工具
- `{"type": "tool", "name": "tool_name"}` - 指定工具

### 3. 多模态支持

#### 支持的图像格式
- JPEG (`image/jpeg`)
- PNG (`image/png`)
- GIF (`image/gif`)
- WebP (`image/webp`)

#### 多模态内容示例
```python
content = [
    {
        "type": "text",
        "text": "What's in this image?"
    },
    {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": "base64_encoded_image_data"
        }
    }
]
```

### 4. 流式响应支持

#### 流式事件类型
- `message_start` - 消息开始
- `content_block_start` - 内容块开始
- `content_block_delta` - 内容块增量
- `content_block_stop` - 内容块结束
- `message_delta` - 消息增量
- `message_stop` - 消息结束

#### 流式处理示例
```python
# 解析流式事件
events = []
for line in stream_response:
    event = stream_utils.parse_stream_event(line)
    if event:
        events.append(event)

# 转换为完整响应
message = format_utils.convert_stream_response(events)
```

## 使用示例

### 1. 基本对话

```python
from src.infrastructure.llm.converters.provider_format_utils import get_provider_format_utils_factory

# 创建格式工具
factory = get_provider_format_utils_factory()
anthropic_utils = factory.get_format_utils("anthropic")

# 准备消息和参数
messages = [
    HumanMessage(content="Hello, Claude!")
]
parameters = {
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "temperature": 0.7
}

# 转换请求
request = anthropic_utils.convert_request(messages, parameters)

# 发送请求到API...
# response = api_client.send_request(request)

# 转换响应
message = anthropic_utils.convert_response(response)
```

### 2. 工具使用

```python
# 定义工具
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
]

# 准备请求
messages = [HumanMessage(content="What's the weather in San Francisco?")]
parameters = {
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "tools": tools,
    "tool_choice": "auto"
}

# 转换并发送请求
request = anthropic_utils.convert_request(messages, parameters)
# response = api_client.send_request(request)

# 处理工具调用
message = anthropic_utils.convert_response(response)
if message.tool_calls:
    for tool_call in message.tool_calls:
        # 执行工具调用
        result = execute_tool(tool_call)
        
        # 创建工具结果消息
        tool_message = ToolMessage(
            content=result,
            tool_call_id=tool_call["id"]
        )
        messages.append(message)
        messages.append(tool_message)
        
        # 继续对话...
```

### 3. 多模态内容

```python
# 创建多模态消息
content = [
    {"type": "text", "text": "What's in this image?"},
    {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64.b64encode(image_data).decode()
        }
    }
]

messages = [HumanMessage(content=content)]
parameters = {
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024
}

# 转换请求
request = anthropic_utils.convert_request(messages, parameters)
```

### 4. 流式响应

```python
# 启用流式响应
parameters = {
    "model": "claude-sonnet-4-5",
    "max_tokens": 1024,
    "stream": True
}

# 发送流式请求
stream_response = api_client.send_stream_request(request)

# 处理流式事件
events = []
for line in stream_response:
    event = anthropic_utils.stream_utils.parse_stream_event(line)
    if event:
        events.append(event)
        
        # 实时处理文本
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                print(delta.get("text", ""), end="")

# 转换完整响应
final_message = anthropic_utils.convert_stream_response(events)
```

## 验证和错误处理

### 1. 请求验证

```python
# 验证请求参数
errors = anthropic_utils.validate_request(messages, parameters)
if errors:
    print("验证错误:", errors)
    # 处理错误...
```

### 2. 错误处理

```python
try:
    request = anthropic_utils.convert_request(messages, parameters)
except AnthropicValidationError as e:
    print("验证错误:", e)
except AnthropicFormatError as e:
    print("格式错误:", e)
```

### 3. API错误处理

```python
# 处理API错误响应
error_response = {
    "error": {
        "type": "authentication_error",
        "message": "Invalid API key"
    }
}

friendly_message = anthropic_utils.handle_api_error(error_response)
print(friendly_message)  # "认证失败，请检查API密钥: Invalid API key"
```

## 性能优化

### 1. 缓存机制

- 工具定义缓存
- 格式转换结果缓存
- 验证结果缓存

### 2. 批量处理

- 批量消息转换
- 批量工具验证
- 批量内容处理

### 3. 内存优化

- 流式处理减少内存占用
- 按需加载大型内容
- 及时释放临时对象

## 测试

### 1. 单元测试

运行所有Anthropic相关测试：
```bash
uv run pytest tests/infrastructure/llm/converters/test_anthropic_format_utils.py -v
```

### 2. 集成测试

测试完整的API集成流程：
```bash
uv run pytest tests/infrastructure/llm/converters/test_anthropic_integration.py -v
```

### 3. 性能测试

测试转换性能和内存使用：
```bash
uv run pytest tests/infrastructure/llm/converters/test_anthropic_performance.py -v
```

## 最佳实践

### 1. 参数设置

- 根据任务类型调整temperature
- 合理设置max_tokens避免浪费
- 使用stop_sequences控制输出长度

### 2. 工具设计

- 提供清晰的工具描述
- 设计简洁的参数结构
- 合理使用required字段

### 3. 多模态处理

- 优化图像大小和格式
- 合理组合文本和图像
- 验证内容格式

### 4. 流式处理

- 实时处理文本增量
- 正确处理工具调用
- 优雅处理流式错误

## 故障排除

### 1. 常见问题

#### 验证错误
- 检查参数格式和值
- 确认模型名称正确
- 验证工具定义

#### 格式错误
- 检查消息结构
- 确认内容格式
- 验证工具调用

#### API错误
- 检查API密钥
- 确认请求格式
- 查看错误消息

### 2. 调试技巧

#### 启用详细日志
```python
import logging
logging.getLogger("src.infrastructure.llm.converters").setLevel(logging.DEBUG)
```

#### 检查转换结果
```python
# 打印转换后的请求
import json
print(json.dumps(request, indent=2))
```

#### 验证响应格式
```python
# 验证响应格式
errors = anthropic_utils.validation_utils.validate_response(response)
if errors:
    print("响应验证错误:", errors)
```

## 版本历史

### v2.0.0 (当前版本)
- 完全重写的模块化架构
- 增强的工具使用支持
- 完整的多模态支持
- 流式响应处理
- 全面的验证和错误处理

### v1.0.0 (旧版本)
- 基本的格式转换
- 简单的工具支持
- 有限的验证功能

## 贡献指南

### 1. 代码贡献

1. Fork项目
2. 创建功能分支
3. 编写测试
4. 提交Pull Request

### 2. 问题报告

1. 检查现有问题
2. 创建详细描述
3. 提供复现步骤
4. 包含环境信息

### 3. 文档改进

1. 修正错误和不准确之处
2. 添加使用示例
3. 改进说明清晰度
4. 更新版本信息

## 参考资料

- [Anthropic Claude API文档](https://docs.anthropic.com/claude/reference/messages)
- [Anthropic API参数参考](anthropic_api_parameters.md)
- [Modular Agent Framework架构指南](../../architecture.md)