"""增强版Token计数器使用示例"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.llm.token_counter import (
    EnhancedOpenAITokenCounter,
    EnhancedGeminiTokenCounter,
    EnhancedAnthropicTokenCounter,
    TokenCounterFactory
)
from langchain_core.messages import HumanMessage, AIMessage


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建增强版OpenAI计数器
    counter = EnhancedOpenAITokenCounter("gpt-4")
    
    # 计算文本token
    text = "Hello, how are you today?"
    token_count = counter.count_tokens(text)
    print(f"文本: '{text}'")
    print(f"Token数量: {token_count}")
    
    # 计算消息token
    messages = [
        HumanMessage(content="What is the capital of France?"),
        AIMessage(content="The capital of France is Paris.")
    ]
    message_tokens = counter.count_messages_tokens(messages)
    print(f"消息Token数量: {message_tokens}")
    
    # 获取模型信息
    info = counter.get_model_info()
    print(f"模型信息: {info['model_name']} ({info['provider']})")
    print(f"校准置信度: {info['calibration_confidence']:.2f}")
    print()


def example_api_response_update():
    """API响应更新示例"""
    print("=== API响应更新示例 ===")
    
    counter = EnhancedOpenAITokenCounter("gpt-4")
    
    # 模拟API响应
    api_response = {
        "id": "chatcmpl-123",
        "model": "gpt-4",
        "usage": {
            "prompt_tokens": 25,
            "completion_tokens": 15,
            "total_tokens": 40
        }
    }
    
    # 更新计数器
    context = "What is the capital of France?"
    success = counter.update_from_api_response(api_response, context)
    
    if success:
        print("API响应更新成功")
        
        # 获取最新的使用情况
        usage = counter.get_last_api_usage()
        if usage:
            print(f"API使用情况:")
            print(f"  Prompt tokens: {usage.prompt_tokens}")
            print(f"  Completion tokens: {usage.completion_tokens}")
            print(f"  Total tokens: {usage.total_tokens}")
            print(f"  来源: {usage.source}")
        
        # 再次计算相同文本，应该使用缓存
        cached_count = counter.count_tokens(context)
        print(f"缓存结果: {cached_count}")
        
        # 查看缓存统计
        if hasattr(counter, 'cache') and counter.cache is not None:
            stats = counter.cache.get_stats()
            print(f"缓存命中率: {stats['hit_rate']:.2f}")
    
    print()


def example_calibration():
    """校准示例"""
    print("=== 校准示例 ===")
    
    counter = EnhancedOpenAITokenCounter("gpt-4")
    
    # 模拟多次API调用，收集校准数据
    test_cases = [
        ("Hello", 3),
        ("How are you?", 5),
        ("What is the weather like?", 7),
        ("Can you help me with my homework?", 9),
        ("I need to write a Python script", 8)
    ]
    
    print("添加校准数据点...")
    for text, api_count in test_cases:
        local_count = counter.count_tokens(text)
        # 注意：当前实现中没有校准器，所以这部分会被跳过
        if hasattr(counter, 'calibrator') and counter.calibrator is not None:
            counter.calibrator.add_calibration_point(local_count, api_count)
        print(f"本地: {local_count}, API: {api_count}")
    
    # 查看校准统计
    if hasattr(counter, 'calibrator') and counter.calibrator is not None:
        stats = counter.calibrator.get_stats()
        print(f"\n校准统计:")
        print(f"  数据点数量: {stats['data_points']}")
        print(f"  校准因子: {stats['calibration_factor']:.3f}")
        print(f"  置信度: {stats['confidence']:.2f}")

        # 使用校准后的计数
        test_text = "This is a test sentence for calibration"
        local_count = counter.count_tokens(test_text)
        # 注意：当前实现中没有校准器，所以这部分会被跳过
        calibrated_count = local_count

        print(f"\n测试文本: '{test_text}'")
        print(f"本地计数: {local_count}")
        print(f"校准后计数: {calibrated_count}")
    else:
        print("\n校准器未初始化，无法查看统计或进行校准")
        # 使用本地计数
        test_text = "This is a test sentence for calibration"
        local_count = counter.count_tokens(test_text)
        print(f"\n测试文本: '{test_text}'")
        print(f"本地计数: {local_count}")
    print()


def example_factory_with_config():
    """使用工厂和配置的示例"""
    print("=== 工厂和配置示例 ===")
    
    # 使用配置创建计数器
    config = {
        "model_type": "openai",
        "model_name": "gpt-4",
        "enhanced": True,
        "cache": {
            "ttl_seconds": 1800,  # 30分钟
            "max_size": 500
        },
        "calibration": {
            "min_data_points": 2,
            "max_data_points": 50
        }
    }
    
    counter = TokenCounterFactory.create_with_config(config)

    print(f"创建的计数器类型: {type(counter).__name__}")
    # print(f"模型: {counter.model_name}")
    # 注意：当前接口没有暴露 model_name 属性
    # 对于增强版本的计数器，访问额外属性
    # 缓存和校准器在当前实现中不可直接访问
    # if hasattr(counter, 'cache') and counter.cache is not None:
    #     print(f"缓存TTL: {counter.cache.ttl}秒")
    #     print(f"缓存最大大小: {counter.cache.max_size}")
    # if hasattr(counter, 'calibrator') and counter.calibrator is not None:
    #     print(f"校准最小数据点: {counter.calibrator.min_data_points}")
    print()


def example_different_providers():
    """不同提供商示例"""
    print("=== 不同提供商示例 ===")
    
    providers = [
        ("OpenAI", EnhancedOpenAITokenCounter("gpt-4")),
        ("Gemini", EnhancedGeminiTokenCounter("gemini-pro")),
        ("Anthropic", EnhancedAnthropicTokenCounter("claude-3-sonnet-20240229"))
    ]
    
    test_text = "Hello, world!"
    
    for provider_name, counter in providers:
        count = counter.count_tokens(test_text)
        info = counter.get_model_info()
        print(f"{provider_name}: {count} tokens (模型: {info['model_name']})")
    
    print()


def example_api_response_parsing():
    """API响应解析示例"""
    print("=== API响应解析示例 ===")
    
    # OpenAI响应
    openai_response = {
        "id": "chatcmpl-123",
        "model": "gpt-4",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
    
    # Gemini响应
    gemini_response = {
        "model": "gemini-pro",
        "usageMetadata": {
            "promptTokenCount": 12,
            "candidatesTokenCount": 8,
            "totalTokenCount": 20
        }
    }
    
    # Anthropic响应
    anthropic_response = {
        "model": "claude-3-sonnet-20240229",
        "usage": {
            "input_tokens": 15,
            "output_tokens": 10
        }
    }
    
    # 解析响应
    responses = [
        ("OpenAI", openai_response),
        ("Gemini", gemini_response),
        ("Anthropic", anthropic_response)
    ]
    
    for provider, response in responses:
        # ApiResponseParser 当前在代码库中不存在，暂时注释掉这部分代码
        # usage = ApiResponseParser.parse_response(provider.lower(), response)
        print(f"{provider} API响应解析功能暂不可用")
        print()


if __name__ == "__main__":
    print("增强版Token计数器示例")
    print("=" * 50)
    
    example_basic_usage()
    example_api_response_update()
    example_calibration()
    example_factory_with_config()
    example_different_providers()
    example_api_response_parsing()
    
    print("所有示例运行完成！")