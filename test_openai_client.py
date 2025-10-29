#!/usr/bin/env python3
"""测试新的 OpenAI 客户端实现"""

import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试导入"""
    print("测试导入...")
    
    try:
        from src.infrastructure.llm.clients.openai import (
            OpenAIConfig,
            OpenAIUnifiedClient,
            LangChainChatClient,
            LightweightResponsesClient,
            ResponseConverter,
            MessageConverter
        )
        print("✓ 所有导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_config():
    """测试配置"""
    print("测试配置...")
    
    try:
        from src.infrastructure.llm.clients.openai import OpenAIConfig
        
        # 测试 Chat Completions 配置
        config = OpenAIConfig(
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            api_format="chat_completion"
        )
        
        assert config.is_chat_completion() == True
        assert config.is_responses_api() == False
        assert config.validate_config() == True
        
        # 测试 Responses API 配置
        config_responses = OpenAIConfig(
            model_name="gpt-4",
            api_key="test-key",
            api_format="responses"
        )
        
        assert config_responses.is_chat_completion() == False
        assert config_responses.is_responses_api() == True
        assert config_responses.validate_config() == True
        
        print("✓ 配置测试通过")
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def test_client_creation():
    """测试客户端创建"""
    print("测试客户端创建...")
    
    try:
        from src.infrastructure.llm.clients.openai import OpenAIConfig, OpenAIUnifiedClient
        
        # 测试 Chat Completions 客户端
        config = OpenAIConfig(
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            api_format="chat_completion"
        )
        
        client = OpenAIUnifiedClient(config)
        assert client.get_current_api_format() == "chat_completion"
        assert client.supports_function_calling() == True
        
        # 测试 API 格式切换
        client.switch_api_format("responses")
        assert client.get_current_api_format() == "responses"
        
        # 测试客户端信息
        info = client.get_client_info()
        assert "api_format" in info
        assert "model_name" in info
        assert "client_type" in info
        
        print("✓ 客户端创建测试通过")
        return True
    except Exception as e:
        print(f"✗ 客户端创建测试失败: {e}")
        return False

def test_utils():
    """测试工具函数"""
    print("测试工具函数...")
    
    try:
        from src.infrastructure.llm.clients.openai import ResponseConverter, MessageConverter
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # 测试消息转换
        messages = [
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="Hello")
        ]
        
        input_text = MessageConverter.messages_to_input(messages)
        assert "System: You are a helpful assistant" in input_text
        assert "User: Hello" in input_text
        
        print("✓ 工具函数测试通过")
        return True
    except Exception as e:
        print(f"✗ 工具函数测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试新的 OpenAI 客户端实现...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_client_creation,
        test_utils
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！新的 OpenAI 客户端实现工作正常。")
        return True
    else:
        print("✗ 部分测试失败，需要检查实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)