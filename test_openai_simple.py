"""简单测试OpenAI统一客户端"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm.clients.openai.config import OpenAIConfig
from llm.clients.openai.unified_client import OpenAIUnifiedClient
from langchain_core.messages import HumanMessage


def test_config_creation():
    """测试配置创建"""
    print("测试配置创建...")
    
    # 创建配置
    config = OpenAIConfig(
        model_type="openai",
        model_name="gpt-3.5-turbo",
        api_key="test-key",
        api_format="chat_completion",
        temperature=0.7,
        max_tokens=100
    )
    
    print(f"配置创建成功: {config.model_name}")
    print(f"API格式: {config.api_format}")
    print(f"支持的API格式: {list(config.api_format_configs.keys())}")
    
    # 测试API格式切换
    config.switch_api_format("responses")
    print(f"切换后的API格式: {config.api_format}")
    
    # 测试降级格式
    fallback_formats = config.get_fallback_formats()
    print(f"降级格式: {fallback_formats}")
    
    print("配置测试完成！")


def test_client_creation():
    """测试客户端创建"""
    print("\n测试客户端创建...")
    
    # 创建配置
    config = OpenAIConfig(
        model_type="openai",
        model_name="gpt-3.5-turbo",
        api_key="test-key",
        api_format="chat_completion"
    )
    
    # 创建客户端
    client = OpenAIUnifiedClient(config)
    
    print(f"客户端创建成功: {type(client).__name__}")
    print(f"当前API格式: {client.get_current_api_format()}")
    print(f"支持的API格式: {client.get_supported_api_formats()}")
    print(f"是否支持函数调用: {client.supports_function_calling()}")
    
    # 测试API格式切换
    print("\n测试API格式切换...")
    client.switch_api_format("responses")
    print(f"切换后的API格式: {client.get_current_api_format()}")
    
    # 切换回Chat Completion
    client.switch_api_format("chat_completion")
    print(f"切换回Chat Completion: {client.get_current_api_format()}")
    
    print("客户端测试完成！")


def test_token_counting():
    """测试Token计数功能"""
    print("\n测试Token计数...")
    
    config = OpenAIConfig(
        model_type="openai",
        model_name="gpt-3.5-turbo",
        api_key="test-key"
    )
    
    client = OpenAIUnifiedClient(config)
    
    # 测试文本Token计数
    text = "Hello, world! This is a test message."
    token_count = client.get_token_count(text)
    print(f"文本Token计数: '{text}' -> {token_count} tokens")
    
    # 测试消息Token计数
    messages = [
        HumanMessage(content="Hello, how are you?"),
        HumanMessage(content="What's the weather like today?")
    ]
    messages_token_count = client.get_messages_token_count(messages)
    print(f"消息Token计数: {len(messages)} messages -> {messages_token_count} tokens")
    
    print("Token计数测试完成！")


if __name__ == "__main__":
    # 运行基本测试
    test_config_creation()
    
    # 测试客户端创建
    test_client_creation()
    
    # 测试Token计数
    test_token_counting()
    
    print("\n所有测试完成！")