# OpenAI统一客户端使用示例

本文档展示了如何使用新的OpenAI统一客户端，支持Chat Completion API和Responses API两种格式。

## 基本使用

### 1. 使用工厂模式创建客户端

```python
from src.llm.factory import create_client

# 创建Chat Completion客户端
config = {
    "model_type": "openai",
    "model_name": "gpt-4",
    "api_key": "your-api-key",
    "api_format": "chat_completion"  # 默认格式
}

client = create_client(config)

# 使用客户端
from langchain_core.messages import HumanMessage
messages = [HumanMessage(content="Hello, how are you?")]
response = client.generate(messages)
print(response.content)
```

### 2. 使用Responses API

```python
from src.llm.factory import create_client

# 创建Responses API客户端
config = {
    "model_type": "openai",
    "model_name": "gpt-4",
    "api_key": "your-api-key",
    "api_format": "responses"  # 使用Responses API
}

client = create_client(config)

# 使用客户端
messages = [HumanMessage(content="Hello, how are you?")]
response = client.generate(messages)
print(response.content)
```

## 高级功能

### 1. 动态切换API格式

```python
from src.llm.clients.openai.unified_client import OpenAIUnifiedClient
from src.llm.clients.openai.config import OpenAIConfig

# 创建配置
config = OpenAIConfig(
    model_type="openai",
    model_name="gpt-4",
    api_key="your-api-key",
    api_format="chat_completion"
)

# 创建客户端
client = OpenAIUnifiedClient(config)

# 使用Chat Completion API
response1 = client.generate(messages)

# 切换到Responses API
client.switch_api_format("responses")
response2 = client.generate(messages)

# 切换回Chat Completion
client.switch_api_format("chat_completion")
```

### 2. 带降级的生成

```python
from src.llm.clients.openai.config import OpenAIConfig

# 创建支持降级的配置
config = OpenAIConfig(
    model_type="openai",
    model_name="gpt-4",
    api_key="your-api-key",
    api_format="responses",  # 主要使用Responses API
    fallback_enabled=True,
    fallback_formats=["chat_completion"]  # 降级到Chat Completion
)

client = OpenAIUnifiedClient(config)

# 使用带降级的生成
try:
    response = client.generate_with_fallback(messages)
    print(f"生成成功: {response.content}")
except Exception as e:
    print(f"所有API格式都失败: {e}")
```

### 3. 流式生成

```python
# 同步流式生成
for chunk in client.stream_generate(messages):
    print(chunk, end='', flush=True)

# 异步流式生成
async for chunk in client.stream_generate_async(messages):
    print(chunk, end='', flush=True)
```

## 配置详解

### 基本配置

```yaml
# configs/llms/openai-gpt4.yaml
model_type: openai
model_name: gpt-4
api_format: chat_completion  # chat_completion | responses
base_url: "https://api.openai.com/v1"
api_key: "${OPENAI_API_KEY}"

parameters:
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  max_retries: 3
```

### API格式特定配置

```yaml
api_formats:
  chat_completion:
    endpoint: "/chat/completions"
    supports_multiple_choices: true
    legacy_structured_output: true
  responses:
    endpoint: "/responses"
    supports_reasoning: true
    native_storage: true
    structured_output_format: "text.format"
```

### 降级配置

```yaml
# 启用降级功能
fallback_enabled: true
fallback_formats:
  - chat_completion  # 如果当前格式失败，尝试这些格式
  - responses
```

## 错误处理

```python
from src.llm.exceptions import LLMCallError, LLMRateLimitError

try:
    response = client.generate(messages)
except LLMRateLimitError as e:
    print(f"频率限制: {e}")
    # 等待重试
except LLMCallError as e:
    print(f"API调用错误: {e}")
    # 处理其他错误
```

## 性能优化

### 1. Token计数缓存

```python
# 客户端会自动缓存Token计数结果
token_count = client.get_token_count("Hello, world!")
# 第二次调用会使用缓存
token_count = client.get_token_count("Hello, world!")
```

### 2. 连接池

Responses API原生客户端使用httpx的连接池，支持高并发场景。

## 监控和调试

### 1. 获取当前API格式

```python
current_format = client.get_current_api_format()
print(f"当前使用: {current_format}")
```

### 2. 获取支持的API格式

```python
supported_formats = client.get_supported_api_formats()
print(f"支持的格式: {supported_formats}")
```

### 3. 获取模型信息

```python
model_info = client.get_model_info()
print(f"模型信息: {model_info}")
```

## 向后兼容性

新的统一客户端完全向后兼容。现有的代码无需修改即可继续使用：

```python
# 旧代码（仍然有效）
config = {
    "model_type": "openai",
    "model_name": "gpt-4",
    "api_key": "your-api-key"
}

client = create_client(config)
# 默认使用chat_completion格式
```

## 最佳实践

### 1. 渐进式迁移

1. **第一阶段**：部署新架构，默认使用Chat Completion
2. **第二阶段**：在测试环境验证Responses API
3. **第三阶段**：逐步切换到Responses API
4. **第四阶段**：全面启用新特性

### 2. 配置管理

- 为不同的API格式创建单独的配置文件
- 使用环境变量管理API密钥
- 在生产环境中启用降级功能

### 3. 错误处理

- 始终准备好降级方案
- 监控API格式使用情况和成功率
- 为API格式切换失败设置告警

## 注意事项

1. **Responses API可用性**：确保你的API密钥有Responses API访问权限
2. **性能差异**：不同API格式可能有不同的性能特征
3. **功能差异**：某些功能可能只在特定API格式中可用
4. **成本考虑**：不同API格式可能有不同的定价模式

## 故障排除

### 常见问题

1. **Responses API不可用**：检查API密钥权限和网络连接
2. **Token计算不准确**：确保使用相同的编码器
3. **性能下降**：启用连接池和缓存机制

### 调试技巧

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志记录
client = create_client(config)
# 查看详细的API调用日志
```

这个统一客户端设计为提供无缝的API格式切换体验，同时保持向后兼容性。