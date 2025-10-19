# LLM模块使用示例

本文档提供了LLM模块的详细使用示例，包括基本用法、高级功能和最佳实践。

## 目录

1. [基本用法](#基本用法)
2. [客户端配置](#客户端配置)
3. [钩子机制](#钩子机制)
4. [降级策略](#降级策略)
5. [流式生成](#流式生成)
6. [函数调用](#函数调用)
7. [错误处理](#错误处理)
8. [性能优化](#性能优化)

## 基本用法

### 创建客户端

```python
from src.llm import LLMFactory, create_client

# 方法1：使用全局工厂
config = {
    "model_type": "openai",
    "model_name": "gpt-3.5-turbo",
    "api_key": "your-api-key",
    "temperature": 0.7,
    "max_tokens": 1000
}

client = create_client(config)

# 方法2：使用工厂实例
from src.llm import LLMFactory, LLMModuleConfig

module_config = LLMModuleConfig(cache_enabled=True)
factory = LLMFactory(module_config)
client = factory.create_client(config)
```

### 基本文本生成

```python
from langchain_core.messages import HumanMessage

# 创建消息
messages = [
    HumanMessage(content="请解释什么是人工智能？")
]

# 生成响应
response = client.generate(messages)
print(response.content)
print(f"使用Token: {response.token_usage.total_tokens}")
print(f"响应时间: {response.response_time:.2f}秒")
```

### 异步生成

```python
import asyncio
from langchain_core.messages import HumanMessage

async def generate_async():
    messages = [HumanMessage(content="请写一首关于春天的诗")]
    response = await client.generate_async(messages)
    print(response.content)

# 运行异步函数
asyncio.run(generate_async())
```

## 客户端配置

### OpenAI配置

```python
openai_config = {
    "model_type": "openai",
    "model_name": "gpt-4",
    "api_key": "${OPENAI_API_KEY}",  # 从环境变量读取
    "base_url": "https://api.openai.com/v1",
    "organization": "your-org-id",  # 可选
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "timeout": 30,
    "max_retries": 3,
    "fallback_enabled": True,
    "fallback_models": ["gpt-3.5-turbo"],
    "max_fallback_attempts": 3
}

client = create_client(openai_config)
```

### Gemini配置

```python
gemini_config = {
    "model_type": "gemini",
    "model_name": "gemini-pro",
    "api_key": "${GEMINI_API_KEY}",
    "base_url": "https://generativelanguage.googleapis.com/v1",
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 1.0,
    "top_k": 40,  # Gemini特有参数
    "timeout": 30,
    "max_retries": 3
}

client = create_client(gemini_config)
```

### Anthropic配置

```python
anthropic_config = {
    "model_type": "anthropic",
    "model_name": "claude-3-sonnet-20240229",
    "api_key": "${ANTHROPIC_API_KEY}",
    "base_url": "https://api.anthropic.com",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30,
    "max_retries": 3
}

client = create_client(anthropic_config)
```

### Mock配置（用于测试）

```python
mock_config = {
    "model_type": "mock",
    "model_name": "mock-model",
    "response_delay": 0.1,  # 响应延迟（秒）
    "error_rate": 0.0,      # 错误率（0-1）
    "error_types": ["timeout", "rate_limit"]  # 可能的错误类型
}

client = create_client(mock_config)
```

## 钩子机制

### 日志钩子

```python
from src.llm import LoggingHook

# 创建日志钩子
logging_hook = LoggingHook(
    log_requests=True,   # 记录请求
    log_responses=True,  # 记录响应
    log_errors=True      # 记录错误
)

# 添加到客户端
client.add_hook(logging_hook)

# 现在所有调用都会被记录
response = client.generate(messages)
```

### 指标钩子

```python
from src.llm import MetricsHook

# 创建指标钩子
metrics_hook = MetricsHook()
client.add_hook(metrics_hook)

# 使用客户端
for i in range(10):
    response = client.generate(messages)

# 获取指标
metrics = metrics_hook.get_metrics()
print(f"总调用次数: {metrics['total_calls']}")
print(f"成功率: {metrics['success_rate']:.2%}")
print(f"平均响应时间: {metrics['average_response_time']:.2f}秒")
print(f"平均Token使用: {metrics['average_tokens_per_call']:.1f}")

# 重置指标
metrics_hook.reset_metrics()
```

### 组合钩子

```python
from src.llm import CompositeHook

# 创建组合钩子
composite_hook = CompositeHook([
    LoggingHook(),
    MetricsHook(),
    # 可以添加更多钩子
])

# 添加到客户端
client.add_hook(composite_hook)
```

## 降级策略

### 基本降级

```python
from src.llm.fallback import FallbackManager, FallbackStrategy, FallbackModel

# 定义降级模型
fallback_models = [
    FallbackModel(name="gpt-3.5-turbo", priority=1),
    FallbackModel(name="gemini-pro", priority=2),
    FallbackModel(name="claude-3-haiku", priority=3)
]

# 创建降级管理器
fallback_manager = FallbackManager(
    fallback_models=fallback_models,
    strategy=FallbackStrategy.SEQUENTIAL,  # 顺序降级
    max_attempts=3,
    timeout=30.0
)

# 使用降级
try:
    response = fallback_manager.execute_fallback(
        primary_client=client,
        messages=messages,
        parameters={"temperature": 0.7}
    )
    
    # 检查是否使用了降级
    if "fallback_model" in response.metadata:
        print(f"使用了降级模型: {response.metadata['fallback_model']}")
        
except Exception as e:
    print(f"所有降级都失败了: {e}")
```

### 条件降级

```python
from src.llm.fallback import ConditionalFallback

# 创建带条件的降级模型
fallback_models = [
    FallbackModel(
        name="gpt-3.5-turbo",
        priority=1,
        conditions=[
            ConditionalFallback.on_timeout,        # 超时时降级
            ConditionalFallback.on_rate_limit       # 频率限制时降级
        ]
    ),
    FallbackModel(
        name="gemini-pro",
        priority=2,
        conditions=[
            ConditionalFallback.on_service_unavailable  # 服务不可用时降级
        ]
    )
]

fallback_manager = FallbackManager(
    fallback_models=fallback_models,
    strategy=FallbackStrategy.PRIORITY
)
```

### 并行降级

```python
# 并行尝试多个模型，使用第一个成功的结果
fallback_manager = FallbackManager(
    fallback_models=fallback_models,
    strategy=FallbackStrategy.PARALLEL,
    timeout=10.0  # 总超时时间
)
```

## 流式生成

### 同步流式生成

```python
from langchain_core.messages import HumanMessage

messages = [HumanMessage(content="请详细解释机器学习的基本概念")]

# 流式生成
print("AI回复: ", end="", flush=True)
for chunk in client.stream_generate(messages):
    print(chunk, end="", flush=True)
print()  # 换行
```

### 异步流式生成

```python
import asyncio
from langchain_core.messages import HumanMessage

async def stream_example():
    messages = [HumanMessage(content="请写一个短故事")]
    
    print("AI回复: ", end="", flush=True)
    async for chunk in client.stream_generate_async(messages):
        print(chunk, end="", flush=True)
    print()  # 换行

# 运行异步流式生成
asyncio.run(stream_example())
```

## 函数调用

### 定义函数

```python
functions = [
    {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["city"]
        }
    }
]

# 配置客户端
config = {
    "model_type": "openai",
    "model_name": "gpt-4",
    "api_key": "your-api-key",
    "functions": functions,
    "function_call": "auto"  # 自动选择函数
}

client = create_client(config)
```

### 使用函数调用

```python
from langchain_core.messages import HumanMessage

messages = [
    HumanMessage(content="北京今天的天气怎么样？")
]

response = client.generate(messages)

# 检查是否有函数调用
if response.function_call:
    function_name = response.function_call["name"]
    arguments = response.function_call["arguments"]
    
    print(f"调用函数: {function_name}")
    print(f"参数: {arguments}")
    
    # 执行函数并继续对话
    # ...
```

## 错误处理

### 基本错误处理

```python
from src.llm.exceptions import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMServiceUnavailableError
)

try:
    response = client.generate(messages)
except LLMTimeoutError as e:
    print(f"请求超时: {e}")
except LLMRateLimitError as e:
    print(f"频率限制: {e}, 重试时间: {e.retry_after}秒")
except LLMAuthenticationError as e:
    print(f"认证失败: {e}")
except LLMServiceUnavailableError as e:
    print(f"服务不可用: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 重试机制

```python
import time
from src.llm.exceptions import LLMCallError

def generate_with_retry(client, messages, max_retries=3, base_delay=1.0):
    """带重试的生成函数"""
    for attempt in range(max_retries + 1):
        try:
            return client.generate(messages)
        except LLMRateLimitError as e:
            if attempt == max_retries:
                raise
            delay = e.retry_after or (base_delay * (2 ** attempt))
            print(f"频率限制，{delay}秒后重试...")
            time.sleep(delay)
        except (LLMTimeoutError, LLMServiceUnavailableError) as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"临时错误，{delay}秒后重试...")
            time.sleep(delay)

# 使用重试函数
response = generate_with_retry(client, messages)
```

## 性能优化

### 客户端缓存

```python
from src.llm import LLMFactory, LLMModuleConfig

# 启用缓存的配置
module_config = LLMModuleConfig(
    cache_enabled=True,
    cache_max_size=100,  # 最大缓存客户端数量
    cache_ttl=3600      # 缓存生存时间（秒）
)

factory = LLMFactory(module_config)

# 第一次创建会创建新客户端
client1 = factory.create_client(config)

# 第二次获取相同模型会返回缓存的客户端
client2 = factory.get_or_create_client("gpt-3.5-turbo", config)

assert client1 is client2  # 是同一个实例
```

### Token计算优化

```python
# 预先计算Token数量，避免超出限制
def check_token_limit(client, messages, max_tokens=4000):
    """检查Token限制"""
    token_count = client.get_messages_token_count(messages)
    
    if token_count > max_tokens:
        print(f"Token数量超限: {token_count} > {max_tokens}")
        # 可以在这里实现消息截断或摘要
        return False
    
    return True

# 使用检查
if check_token_limit(client, messages):
    response = client.generate(messages)
else:
    # 处理超限情况
    pass
```

### 批量处理

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def batch_generate(client, messages_list, max_workers=5):
    """批量生成响应"""
    results = {}
    
    def worker(idx, messages):
        try:
            response = client.generate(messages)
            return idx, response
        except Exception as e:
            return idx, e
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_idx = {
            executor.submit(worker, idx, messages): idx
            for idx, messages in enumerate(messages_list)
        }
        
        # 收集结果
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result_idx, result = future.result()
                results[result_idx] = result
            except Exception as e:
                results[idx] = e
    
    return results

# 使用批量处理
messages_list = [
    [HumanMessage(content=f"问题 {i+1}")]
    for i in range(10)
]

results = batch_generate(client, messages_list)
```

## 最佳实践

1. **使用环境变量存储敏感信息**：如API密钥，不要硬编码在代码中
2. **启用缓存**：对于频繁使用的模型，启用客户端缓存可以提高性能
3. **设置合理的超时**：根据网络环境和模型响应时间设置合适的超时
4. **实现降级策略**：为关键应用配置降级模型，确保服务可用性
5. **监控指标**：使用MetricsHook监控调用性能和成功率
6. **处理错误**：实现适当的错误处理和重试机制
7. **优化Token使用**：预先计算Token数量，避免超出限制
8. **使用流式生成**：对于长文本生成，使用流式API提供更好的用户体验

## 故障排除

### 常见问题

1. **导入错误**：确保已安装所需的依赖包（langchain-openai, langchain-google-genai, langchain-anthropic）
2. **认证失败**：检查API密钥是否正确，是否有足够的权限
3. **模型不可用**：检查模型名称是否正确，是否有访问权限
4. **超时错误**：增加超时时间或检查网络连接
5. **频率限制**：实现重试机制或使用降级模型

### 调试技巧

1. **启用详细日志**：设置日志级别为DEBUG
2. **使用Mock客户端**：在开发和测试中使用Mock客户端
3. **检查响应元数据**：查看响应中的元数据了解调用详情
4. **监控指标**：使用MetricsHook监控性能指标

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 使用Mock客户端进行测试
mock_config = {
    "model_type": "mock",
    "model_name": "debug-model",
    "response_delay": 0.0,
    "error_rate": 0.0
}

debug_client = create_client(mock_config)
```

---

更多详细信息请参考API文档和源代码注释。