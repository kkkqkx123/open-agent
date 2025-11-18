# Token计算服务使用指南

## 概述

根据架构分析文档，我们将Token计算功能从Core层迁移到了Services层，以符合扁平化架构的单向依赖原则。新的`TokenCalculationService`提供统一的Token计算接口。

## 架构变更

### 旧架构
- Token计算方法直接集成在Core层的LLM客户端中
- 依赖不存在的`src/core/llm/token_counter.py`模块
- 违反了扁平化架构的单向依赖原则

### 新架构
- Token计算功能统一在Services层的`TokenCalculationService`中
- Core层的LLM客户端不再包含Token计算方法
- 通过依赖注入获取Token计算服务

## 使用方法

### 1. 基本使用

```python
from src.services.llm.token_calculation_service import TokenCalculationService

# 创建服务实例
token_service = TokenCalculationService()

# 计算文本Token数量
text_token_count = token_service.calculate_tokens(
    text="Hello, world!", 
    model_type="openai", 
    model_name="gpt-4"
)

# 计算消息列表Token数量
from langchain_core.messages import HumanMessage, AIMessage
messages = [
    HumanMessage(content="What is the capital of France?"),
    AIMessage(content="The capital of France is Paris.")
]
message_token_count = token_service.calculate_messages_tokens(
    messages=messages, 
    model_type="openai", 
    model_name="gpt-4"
)
```

### 2. 依赖注入使用

```python
from src.infrastructure.container import DependencyContainer

# 在依赖注入容器中获取服务
container = DependencyContainer()
token_service = container.get(TokenCalculationService)

# 使用服务
token_count = token_service.calculate_tokens("Hello", "openai", "gpt-4")
```

### 3. 从API响应解析Token使用情况

```python
# OpenAI API响应示例
openai_response = {
    "id": "chatcmpl-123",
    "model": "gpt-4",
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
}

# 解析API响应中的Token使用情况
usage = token_service.parse_token_usage_from_response(
    openai_response, 
    "openai"
)

if usage:
    print(f"Prompt tokens: {usage.prompt_tokens}")
    print(f"Completion tokens: {usage.completion_tokens}")
    print(f"Total tokens: {usage.total_tokens}")
```

## 支持的模型提供商

- OpenAI (gpt-3.5-turbo, gpt-4, etc.)
- Gemini (gemini-pro, gemini-1.5-pro, etc.)
- Anthropic (claude-3-sonnet, claude-3-opus, etc.)
- 其他模型类型通过混合处理器支持

## 配置

`TokenCalculationService`支持以下配置：

- `default_provider`: 默认模型提供商
- 处理器自动根据模型类型选择合适的计算策略

## 与历史记录集成

Token计算服务与历史记录系统集成：

```python
from src.infrastructure.history.token_tracker import TokenUsageTracker

# TokenUsageTracker现在使用TokenCalculationService
tracker = TokenUsageTracker(
    token_counter=token_service,  # 使用新的TokenCalculationService
    history_manager=history_manager,
    model_type="openai",
    model_name="gpt-4"
)
```

## 迁移指南

### 从旧的LLM客户端方法迁移到新服务

**旧代码:**
```python
client = SomeLLMClient(config)
token_count = client.get_token_count("Hello, world!")
message_count = client.get_messages_token_count(messages)
```

**新代码:**
```python
token_service = TokenCalculationService()
token_count = token_service.calculate_tokens("Hello, world!", "openai", "gpt-4")
message_count = token_service.calculate_messages_tokens(messages, "openai", "gpt-4")
```

## 注意事项

1. Core层的LLM客户端不再提供Token计算方法，需要通过依赖注入获取`TokenCalculationService`
2. `_validate_token_limit`方法在Core层客户端中已暂时禁用，需要重构以使用新的Token计算服务
3. 依赖注入配置已更新，自动注册`TokenCalculationService`
4. 示例文件`examples/enhanced_token_counter_example.py`已更新为使用新服务

## 架构优势

1. **符合架构原则**: 遵循扁平化架构的单向依赖原则
2. **功能集中**: Token计算功能统一在Services层
3. **易于维护**: 避免功能重复，统一实现
4. **扩展性好**: 新的Token计算功能只需在Services层实现
5. **测试容易**: 职责分离使单元测试更简单