#!/usr/bin/env python3
"""
LLM模块使用示例

这个示例展示了如何使用LLM模块进行基本的文本生成、流式生成和错误处理。
"""

import asyncio
import os
from langchain_core.messages import HumanMessage, SystemMessage

# 导入LLM模块
from src.llm import (
    LLMFactory,
    LLMModuleConfig,
    LoggingHook,
    MetricsHook,
    CompositeHook,
    create_client
)
from src.llm.exceptions import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError
)


def basic_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建Mock客户端配置（用于演示）
    config = {
        "model_type": "mock",
        "model_name": "example-model",
        "response_delay": 0.5,  # 模拟响应延迟
        "error_rate": 0.0       # 不产生错误
    }
    
    # 创建客户端
    client = create_client(config)
    
    # 创建消息
    messages = [
        HumanMessage(content="请解释什么是人工智能？")
    ]
    
    # 生成响应
    print("发送请求...")
    response = client.generate(messages)
    
    # 显示结果
    print(f"AI回复: {response.content}")
    print(f"模型: {response.model}")
    print(f"Token使用: {response.token_usage.total_tokens}")
    print(f"响应时间: {response.response_time:.2f}秒")
    print()


def streaming_example():
    """流式生成示例"""
    print("=== 流式生成示例 ===")
    
    # 创建Mock客户端配置
    config = {
        "model_type": "mock",
        "model_name": "streaming-model",
        "response_delay": 0.1,
        "error_rate": 0.0
    }
    
    client = create_client(config)
    
    # 创建消息
    messages = [
        HumanMessage(content="请写一个关于春天的短诗")
    ]
    
    # 流式生成
    print("AI回复（流式）: ", end="", flush=True)
    for chunk in client.stream_generate(messages):
        print(chunk, end="", flush=True)
    print("\n")


async def async_example():
    """异步生成示例"""
    print("=== 异步生成示例 ===")
    
    # 创建Mock客户端配置
    config = {
        "model_type": "mock",
        "model_name": "async-model",
        "response_delay": 0.3,
        "error_rate": 0.0
    }
    
    client = create_client(config)
    
    # 创建消息
    messages = [
        HumanMessage(content="请介绍一下机器学习的基本概念")
    ]
    
    # 异步生成
    print("发送异步请求...")
    response = await client.generate_async(messages)
    
    # 显示结果
    print(f"AI回复: {response.content}")
    print()


async def async_streaming_example():
    """异步流式生成示例"""
    print("=== 异步流式生成示例 ===")
    
    # 创建Mock客户端配置
    config = {
        "model_type": "mock",
        "model_name": "async-streaming-model",
        "response_delay": 0.1,
        "error_rate": 0.0
    }
    
    client = create_client(config)
    
    # 创建消息
    messages = [
        HumanMessage(content="请解释量子计算的基本原理")
    ]
    
    # 异步流式生成
    print("AI回复（异步流式）: ", end="", flush=True)
    async for chunk in client.stream_generate_async(messages):
        print(chunk, end="", flush=True)
    print("\n")


def hooks_example():
    """钩子机制示例"""
    print("=== 钩子机制示例 ===")
    
    # 创建Mock客户端配置
    config = {
        "model_type": "mock",
        "model_name": "hooks-model",
        "response_delay": 0.2,
        "error_rate": 0.0
    }
    
    client = create_client(config)
    
    # 创建钩子
    logging_hook = LoggingHook(log_requests=True, log_responses=True)
    metrics_hook = MetricsHook()
    
    # 创建组合钩子
    composite_hook = CompositeHook([logging_hook, metrics_hook])
    
    # 添加钩子
    client.add_hook(composite_hook)
    
    # 发送多个请求
    for i in range(3):
        messages = [HumanMessage(content=f"请回答问题 {i+1}")]
        response = client.generate(messages)
        print(f"请求 {i+1} 完成")
    
    # 获取指标
    metrics = metrics_hook.get_metrics()
    print(f"\n指标统计:")
    print(f"总调用次数: {metrics['total_calls']}")
    print(f"成功次数: {metrics['successful_calls']}")
    print(f"成功率: {metrics['success_rate']:.2%}")
    print(f"平均响应时间: {metrics['average_response_time']:.2f}秒")
    print(f"平均Token使用: {metrics['average_tokens_per_call']:.1f}")
    print()


def error_handling_example():
    """错误处理示例"""
    print("=== 错误处理示例 ===")
    
    # 创建会失败的Mock客户端
    config = {
        "model_type": "mock",
        "model_name": "error-model",
        "response_delay": 0.1,
        "error_rate": 1.0,  # 100%错误率
        "error_types": ["timeout", "rate_limit"]
    }
    
    client = create_client(config)
    
    # 尝试生成响应
    messages = [HumanMessage(content="这个问题会失败")]
    
    try:
        response = client.generate(messages)
        print("意外成功")
    except LLMTimeoutError as e:
        print(f"捕获超时错误: {e}")
    except LLMRateLimitError as e:
        print(f"捕获频率限制错误: {e}")
    except Exception as e:
        print(f"捕获其他错误: {type(e).__name__}: {e}")
    
    print()


def token_calculation_example():
    """Token计算示例"""
    print("=== Token计算示例 ===")
    
    # 创建Mock客户端
    config = {
        "model_type": "mock",
        "model_name": "token-model"
    }
    
    client = create_client(config)
    
    # 计算文本Token数量
    text = "这是一个用于计算Token数量的示例文本。"
    token_count = client.get_token_count(text)
    print(f"文本: '{text}'")
    print(f"Token数量: {token_count}")
    
    # 计算消息Token数量
    messages = [
        SystemMessage(content="你是一个有用的AI助手。"),
        HumanMessage(content="请介绍一下Python编程语言。"),
        HumanMessage(content="Python有哪些主要特性？")
    ]
    
    message_tokens = client.get_messages_token_count(messages)
    print(f"\n消息列表Token数量: {message_tokens}")
    print()


def factory_example():
    """工厂模式示例"""
    print("=== 工厂模式示例 ===")
    
    # 创建模块配置
    module_config = LLMModuleConfig(
        cache_enabled=True,
        cache_max_size=5
    )
    
    # 创建工厂
    factory = LLMFactory(module_config)
    
    # 创建多个客户端
    configs = [
        {"model_type": "mock", "model_name": "model-1"},
        {"model_type": "mock", "model_name": "model-2"},
        {"model_type": "mock", "model_name": "model-3"}
    ]
    
    clients = []
    for config in configs:
        client = factory.create_client(config)
        clients.append(client)
        print(f"创建客户端: {config['model_name']}")
    
    # 检查缓存
    cache_info = factory.get_cache_info()
    print(f"\n缓存信息:")
    print(f"缓存大小: {cache_info['cache_size']}")
    print(f"最大缓存大小: {cache_info['max_cache_size']}")
    print(f"缓存的模型: {cache_info['cached_models']}")
    
    # 获取缓存的客户端
    cached_client = factory.get_cached_client("model-1")
    print(f"\n获取缓存的客户端 model-1: {cached_client is not None}")
    print()


def model_info_example():
    """模型信息示例"""
    print("=== 模型信息示例 ===")
    
    # 创建Mock客户端
    config = {
        "model_type": "mock",
        "model_name": "info-model"
    }
    
    client = create_client(config)
    
    # 获取模型信息
    model_info = client.get_model_info()
    
    print("模型信息:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")
    
    # 检查函数调用支持
    supports_function_calling = client.supports_function_calling()
    print(f"\n支持函数调用: {supports_function_calling}")
    print()


async def main():
    """主函数"""
    print("LLM模块使用示例")
    print("=" * 50)
    
    # 运行各种示例
    basic_example()
    streaming_example()
    await async_example()
    await async_streaming_example()
    hooks_example()
    error_handling_example()
    token_calculation_example()
    factory_example()
    model_info_example()
    
    print("所有示例运行完成！")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())