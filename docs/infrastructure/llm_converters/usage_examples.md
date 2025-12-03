# 消息转换器使用示例

本文档提供了如何使用重构后的消息转换器系统的示例和最佳实践。

## 概述

重构后的消息转换器系统采用了清晰的分层架构：

```
应用层 / 服务层
    ↓ 使用 (依赖IMessageConverter, IProviderConverter)
统一消息转换接口层 (message_converters.py)
    ↓ 内部委托 (依赖IProviderConverter)
提供商转换工具层 (provider_format_utils.py)
    ↓ 依赖
基础消息类型层
```

## 基本使用

### 1. 消息格式转换

```python
from src.infrastructure.llm.converters.message_converters import get_message_converter
from src.infrastructure.messages import HumanMessage, AIMessage

# 获取全局消息转换器实例
converter = get_message_converter()

# 创建消息
human_msg = HumanMessage(content="你好，世界！")
ai_msg = AIMessage(content="你好！有什么可以帮助你的吗？")

# 转换为LLM消息格式
llm_msg = converter.from_base_message(human_msg)
print(f"LLM消息: {llm_msg.role} - {llm_msg.content}")

# 转换为字典格式
dict_msg = converter.from_base_message_dict(human_msg)
print(f"字典消息: {dict_msg}")

# 批量转换
messages = [human_msg, ai_msg]
base_messages = converter.convert_message_list(messages)
```

### 2. 提供商请求转换

```python
from src.infrastructure.llm.converters.message_converters import get_provider_request_converter
from src.infrastructure.messages import HumanMessage, SystemMessage

# 获取全局提供商请求转换器实例
request_converter = get_provider_request_converter()

# 准备消息和参数
messages = [
    SystemMessage(content="你是一个有用的助手。"),
    HumanMessage(content="请介绍一下Python编程语言。")
]
parameters = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
}

# 转换为OpenAI格式
openai_request = request_converter.convert_to_provider_request(
    "openai", messages, parameters
)
print(f"OpenAI请求: {openai_request}")

# 转换为Gemini格式
gemini_request = request_converter.convert_to_provider_request(
    "gemini", messages, parameters
)
print(f"Gemini请求: {gemini_request}")

# 转换为Anthropic格式
anthropic_request = request_converter.convert_to_provider_request(
    "anthropic", messages, parameters
)
print(f"Anthropic请求: {anthropic_request}")
```

### 3. 提供商响应转换

```python
from src.infrastructure.llm.converters.message_converters import get_provider_response_converter

# 获取全局提供商响应转换器实例
response_converter = get_provider_response_converter()

# OpenAI响应
openai_response = {
    "choices": [{
        "message": {
            "role": "assistant",
            "content": "Python是一种高级编程语言..."
        }
    }]
}

# 转换为基础消息
message = response_converter.convert_from_provider_response("openai", openai_response)
print(f"转换后的消息: {message.content}")

# 流式响应处理
openai_events = [
    {"choices": [{"delta": {"content": "Python"}}]},
    {"choices": [{"delta": {"content": " 是"}}]},
    {"choices": [{"delta": {"content": " 一种"}}]},
    {"choices": [{"delta": {"content": " 编程语言。"}}]}
]

stream_message = response_converter.convert_from_provider_stream_response(
    "openai", openai_events
)
print(f"流式消息: {stream_message.content}")
```

## 高级使用

### 1. 工具调用支持

```python
from src.infrastructure.llm.converters.message_converters import get_provider_request_converter
from src.infrastructure.messages import HumanMessage

# 准备工具定义
tools = [
    {
        "name": "get_weather",
        "description": "获取指定地点的天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，如：北京"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["location"]
        }
    }
]

# 准备消息和参数
messages = [HumanMessage(content="北京今天天气怎么样？")]
parameters = {
    "model": "gpt-3.5-turbo",
    "tools": tools,
    "tool_choice": "auto"
}

# 转换请求（包含工具）
request_converter = get_provider_request_converter()
request = request_converter.convert_to_provider_request("openai", messages, parameters)
print(f"包含工具的请求: {request}")
```

### 2. 多模态内容支持

```python
from src.infrastructure.llm.converters.message_converters import get_provider_request_converter
from src.infrastructure.messages import HumanMessage

# 创建多模态消息
multimodal_content = [
    {"type": "text", "text": "这张图片里有什么？"},
    {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
        }
    }
]

message = HumanMessage(content=multimodal_content)
parameters = {"model": "gpt-4-vision-preview"}

# 转换多模态请求
request_converter = get_provider_request_converter()
request = request_converter.convert_to_provider_request("openai", [message], parameters)
print(f"多模态请求: {request}")
```

### 3. 消息工厂使用

```python
from src.infrastructure.llm.converters.message_converters import get_message_factory

# 获取全局消息工厂实例
factory = get_message_factory()

# 创建各种类型的消息
human_msg = factory.create_human_message(
    "你好！",
    name="用户",
    additional_kwargs={"source": "web"}
)

ai_msg = factory.create_ai_message(
    "有什么可以帮助你的吗？",
    tool_calls=[
        {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "北京"}'
            }
        }
    ]
)

system_msg = factory.create_system_message(
    "你是一个有用的助手。",
    additional_kwargs={"priority": "high"}
)

tool_msg = factory.create_tool_message(
    "今天北京天气晴朗，温度25°C。",
    tool_call_id="call_123"
)

# 从字典创建消息
msg_data = {
    "type": "human",
    "content": "测试消息",
    "name": "测试用户"
}
dict_msg = factory.create_from_dict(msg_data)
```

### 4. 消息序列化

```python
from src.infrastructure.llm.converters.message_converters import get_message_serializer

# 获取全局消息序列化器实例
serializer = get_message_serializer()

# 序列化单个消息
message = HumanMessage(content="测试消息")
serialized_data = serializer.serialize(message)
print(f"序列化数据: {serialized_data}")

# 反序列化
deserialized_msg = serializer.deserialize(serialized_data)
print(f"反序列化消息: {deserialized_msg.content}")

# 序列化消息列表
messages = [
    HumanMessage(content="你好"),
    AIMessage(content="有什么可以帮助你的吗？")
]
serialized_list = serializer.serialize_list(messages)

# 反序列化消息列表
deserialized_list = serializer.deserialize_list(serialized_list)
print(f"反序列化列表长度: {len(deserialized_list)}")
```

### 5. 消息验证

```python
from src.infrastructure.llm.converters.message_converters import get_message_validator

# 获取全局消息验证器实例
validator = get_message_validator()

# 验证消息
message = HumanMessage(content="测试消息")
errors = validator.validate(message)
if errors:
    print(f"验证错误: {errors}")
else:
    print("消息验证通过")

# 检查消息是否有效
is_valid = validator.is_valid(message)
print(f"消息是否有效: {is_valid}")

# 验证内容
content_errors = validator.validate_content("测试内容")
if content_errors:
    print(f"内容验证错误: {content_errors}")
```

## 最佳实践

### 1. 使用全局实例

推荐使用全局实例函数获取转换器实例，这样可以利用缓存机制提高性能：

```python
# ✅ 推荐
from src.infrastructure.llm.converters.message_converters import (
    get_message_converter,
    get_provider_request_converter,
    get_provider_response_converter
)

converter = get_message_converter()
request_converter = get_provider_request_converter()
response_converter = get_provider_response_converter()

# ❌ 不推荐
from src.infrastructure.llm.converters.message_converters import (
    MessageConverter,
    ProviderRequestConverter,
    ProviderResponseConverter
)

converter = MessageConverter()  # 每次都创建新实例
```

### 2. 统一使用message_converters.py作为入口

外部代码应该只使用message_converters.py中的类和函数，不应该直接使用provider_format_utils.py：

```python
# ✅ 推荐
from src.infrastructure.llm.converters.message_converters import get_provider_request_converter

converter = get_provider_request_converter()
request = converter.convert_to_provider_request("openai", messages, parameters)

# ❌ 不推荐
from src.infrastructure.llm.converters.provider_format_utils import get_provider_format_utils_factory

factory = get_provider_format_utils_factory()
utils = factory.get_format_utils("openai")
request = utils.convert_request(messages, parameters)
```

### 3. 错误处理

```python
from src.infrastructure.llm.converters.message_converters import get_provider_request_converter
import logging

logger = logging.getLogger(__name__)

request_converter = get_provider_request_converter()

try:
    request = request_converter.convert_to_provider_request("openai", messages, parameters)
except ValueError as e:
    logger.error(f"参数验证失败: {e}")
    # 处理验证错误
except Exception as e:
    logger.error(f"转换失败: {e}")
    # 处理其他错误
```

### 4. 类型提示

使用类型提示可以提高代码的可读性和可维护性：

```python
from typing import List, Dict, Any
from src.infrastructure.llm.converters.message_converters import get_provider_request_converter
from src.interfaces.messages import IBaseMessage

def process_messages(messages: List[IBaseMessage], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """处理消息并转换为提供商请求"""
    request_converter = get_provider_request_converter()
    return request_converter.convert_to_provider_request("openai", messages, parameters)
```

## 扩展新的提供商

如果需要添加新的LLM提供商，按照以下步骤：

### 1. 实现IProviderConverter接口

```python
from src.interfaces.llm.converters import IProviderConverter
from src.infrastructure.messages import AIMessage

class NewProviderConverter(IProviderConverter):
    def get_provider_name(self) -> str:
        return "new_provider"
    
    def convert_request(self, messages, parameters):
        # 实现请求转换逻辑
        return {"provider": "new_provider", "messages": messages}
    
    def convert_response(self, response):
        # 实现响应转换逻辑
        return AIMessage(content=response.get("content", ""))
```

### 2. 注册新提供商

```python
from src.infrastructure.llm.converters.provider_format_utils import get_provider_format_utils_factory

factory = get_provider_format_utils_factory()
factory.register_provider("new_provider", NewProviderConverter)
```

### 3. 使用新提供商

```python
from src.infrastructure.llm.converters.message_converters import get_provider_request_converter

request_converter = get_provider_request_converter()
request = request_converter.convert_to_provider_request("new_provider", messages, parameters)
```

## 总结

重构后的消息转换器系统提供了：

1. **清晰的职责分工**：message_converters.py作为统一对外门面，provider_format_utils.py作为内部实现
2. **统一的接口**：通过IProviderConverter接口标准化提供商转换器
3. **便捷的使用方式**：提供全局实例函数和兼容性方法
4. **良好的扩展性**：易于添加新的提供商支持
5. **完整的错误处理**：提供验证和错误处理机制

通过遵循本文档的示例和最佳实践，可以有效地使用消息转换器系统进行各种LLM集成任务。