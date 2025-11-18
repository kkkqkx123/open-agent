"""增强版Token计数器使用示例"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.llm.token_calculation_service import TokenCalculationService
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import HumanMessage, AIMessage


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建Token计算服务
    service = TokenCalculationService()
    
    # 计算文本token
    text = "Hello, how are you today?"
    token_count = service.calculate_tokens(text, "openai", "gpt-4")
    print(f"文本: '{text}'")
    print(f"Token数量: {token_count}")
    
    # 计算消息token
    messages = [
        HumanMessage(content="What is the capital of France?"),
        AIMessage(content="The capital of France is Paris.")
    ]
    message_tokens = service.calculate_messages_tokens(messages, "openai", "gpt-4")
    print(f"消息Token数量: {message_tokens}")
    
    # 获取处理器统计信息（新方法）
    stats = service.get_processor_stats("openai", "gpt-4")
    print(f"处理器统计: {stats}")
    print()


def example_api_response_update():
    """API响应更新示例"""
    print("=== API响应更新示例 ===")
    
    service = TokenCalculationService()
    
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
    
    # 解析API响应中的token使用情况
    usage = service.parse_token_usage_from_response(api_response, "openai")
    
    if usage:
        print("API响应解析成功")
        print(f"API使用情况:")
        print(f" Prompt tokens: {usage.prompt_tokens}")
        print(f"  Completion tokens: {usage.completion_tokens}")
        print(f"  Total tokens: {usage.total_tokens}")
        print(f"  来源: {usage.source}")
    else:
        print("API响应解析失败")
    
    print()


def example_calibration():
    """校准示例（新架构中已移除校准功能，使用服务统计）"""
    print("=== 统计信息示例 ===")
    
    service = TokenCalculationService()
    
    # 计算几个文本的token数量
    test_cases = [
        ("Hello", "openai", "gpt-4"),
        ("How are you?", "openai", "gpt-4"),
        ("What is the weather like?", "openai", "gpt-4"),
        ("Can you help me with my homework?", "openai", "gpt-4"),
        ("I need to write a Python script", "openai", "gpt-4")
    ]
    
    print("计算Token数量...")
    for text, model_type, model_name in test_cases:
        token_count = service.calculate_tokens(text, model_type, model_name)
        print(f"文本: '{text}' -> Token数量: {token_count}")
    
    # 查看处理器统计信息
    stats = service.get_processor_stats("openai", "gpt-4")
    print(f"\n处理器统计:")
    print(f"  总请求数: {stats.get('total_requests', 0)}")
    print(f"  成功计算数: {stats.get('successful_calculations', 0)}")
    print(f"  失败计算数: {stats.get('failed_calculations', 0)}")
    print(f"  成功率: {stats.get('success_rate_percent', 0):.2f}%")
    print()


def example_factory_with_config():
    """使用Token计算服务的示例"""
    print("=== Token计算服务示例 ===")
    
    # 创建服务实例
    service = TokenCalculationService(default_provider="openai")

    print(f"Token计算服务初始化完成")
    print(f"默认提供商: {service._default_provider}")
    print()


def example_different_providers():
    """不同提供商示例"""
    print("=== 不同提供商示例 ===")
    
    service = TokenCalculationService()
    
    providers = [
        ("OpenAI", "gpt-4"),
        ("Gemini", "gemini-pro"),
        ("Anthropic", "claude-3-sonnet-20240229")
    ]
    
    test_text = "Hello, world!"
    
    for provider_name, model_name in providers:
        count = service.calculate_tokens(test_text, provider_name.lower(), model_name)
        print(f"{provider_name}: {count} tokens (模型: {model_name})")
    
    print()


def example_api_response_parsing():
    """API响应解析示例"""
    print("=== API响应解析示例 ===")
    
    service = TokenCalculationService()
    
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
        usage = service.parse_token_usage_from_response(response, provider.lower())
        if usage:
            print(f"{provider} API响应解析成功:")
            print(f"  Prompt tokens: {usage.prompt_tokens}")
            print(f"  Completion tokens: {usage.completion_tokens}")
            print(f" Total tokens: {usage.total_tokens}")
        else:
            print(f"{provider} API响应解析失败或无usage信息")
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