"""测试OpenAI统一客户端"""

import asyncio
from src.llm.clients.openai.config import OpenAIConfig
from src.llm.clients.openai.unified_client import OpenAIUnifiedClient
from langchain_core.messages import HumanMessage


def test_openai_unified_client():
    """测试OpenAI统一客户端的基本功能"""
    print("测试OpenAI统一客户端...")
    
    # 创建配置
    config = OpenAIConfig(
        model_type="openai",
        model_name="gpt-3.5-turbo",
        api_key="test-key",  # 测试用的假密钥
        api_format="chat_completion",
        temperature=0.7,
        max_tokens=100
    )
    
    # 创建客户端
    client = OpenAIUnifiedClient(config)
    
    # 测试基本属性
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
    
    print("OpenAI统一客户端测试完成！")


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


async def test_async_operations():
    """测试异步操作"""
    print("\n测试异步操作...")
    
    config = OpenAIConfig(
        model_type="openai",
        model_name="gpt-3.5-turbo",
        api_key="test-key"
    )
    
    client = OpenAIUnifiedClient(config)
    
    # 测试异步生成（需要实际的API密钥才能运行）
    # messages = [HumanMessage(content="Hello, world!")]
    # try:
    #     response = await client.generate_async(messages)
    #     print(f"异步响应: {response.content}")
    # except Exception as e:
    #     print(f"异步生成失败（预期）: {e}")
    
    print("异步操作测试框架准备完成！")


if __name__ == "__main__":
    # 运行基本测试
    test_openai_unified_client()
    
    # 测试Token计数
    test_token_counting()
    
    # 测试异步操作
    asyncio.run(test_async_operations())
    
    print("\n所有测试完成！")