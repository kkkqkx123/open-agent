"""Token计算功能演示"""

import sys
import os
sys.path.insert(0, 'src/llm')

def test_token_counter():
    print("=== Token计算功能演示 ===\n")
    
    try:
        from token_counter import TokenCounterFactory, OpenAITokenCounter, GeminiTokenCounter, AnthropicTokenCounter, MockTokenCounter
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        # 测试1: 测试不同模型的Token计算器
        print("1. 测试不同模型的Token计算器:")
        
        # OpenAI计算器
        openai_counter = TokenCounterFactory.create_counter("openai", "gpt-4")
        print(f"   OpenAI计算器信息: {openai_counter.get_model_info()}")
        
        # Gemini计算器
        gemini_counter = TokenCounterFactory.create_counter("gemini", "gemini-pro")
        print(f"   Gemini计算器信息: {gemini_counter.get_model_info()}")
        
        # Anthropic计算器
        anthropic_counter = TokenCounterFactory.create_counter("anthropic", "claude-3-sonnet-20240229")
        print(f"   Anthropic计算器信息: {anthropic_counter.get_model_info()}")
        
        # Mock计算器
        mock_counter = TokenCounterFactory.create_counter("mock", "mock-model")
        print(f"   Mock计算器信息: {mock_counter.get_model_info()}")
        print()
        
        # 测试2: 测试文本Token计算
        print("2. 测试文本Token计算:")
        
        test_text = "你好，这是一个测试文本，用于计算Token数量。"
        
        for model_type in ["openai", "gemini", "anthropic", "mock"]:
            counter = TokenCounterFactory.create_counter(model_type, "test-model")
            token_count = counter.count_tokens(test_text)
            print(f"   {model_type}: {token_count} tokens")
        print()
        
        # 测试3: 测试消息Token计算
        print("3. 测试消息Token计算:")
        
        messages = [
            SystemMessage(content="你是一个有用的助手。"),
            HumanMessage(content="请介绍一下你自己。"),
            AIMessage(content="我是一个AI助手，可以帮助你回答问题。")
        ]
        
        for model_type in ["openai", "gemini", "anthropic", "mock"]:
            counter = TokenCounterFactory.create_counter(model_type, "test-model")
            token_count = counter.count_messages_tokens(messages)
            print(f"   {model_type}: {token_count} tokens")
        print()
        
        # 测试4: 测试支持的模型类型
        print("4. 测试支持的模型类型:")
        supported_types = TokenCounterFactory.get_supported_types()
        print(f"   支持的模型类型: {supported_types}")
        print()
        
        # 测试5: 测试OpenAI计算器的tiktoken支持
        print("5. 测试OpenAI计算器的tiktoken支持:")
        
        try:
            import tiktoken
            print("   tiktoken库已安装")
            
            # 测试不同模型的编码器
            models_to_test = ["gpt-3.5-turbo", "gpt-4", "text-davinci-003"]
            
            for model in models_to_test:
                try:
                    counter = OpenAITokenCounter(model)
                    info = counter.get_model_info()
                    print(f"   {model}: {info}")
                except Exception as e:
                    print(f"   {model}: 创建失败 - {e}")
                    
        except ImportError:
            print("   tiktoken库未安装，使用估算方法")
        print()
        
        # 测试6: 测试长文本Token计算
        print("6. 测试长文本Token计算:")
        
        long_text = "这是一个很长的文本，用于测试Token计算的准确性。" * 20
        
        openai_counter = TokenCounterFactory.create_counter("openai", "gpt-4")
        token_count = openai_counter.count_tokens(long_text)
        print(f"   文本长度: {len(long_text)} 字符")
        print(f"   Token数量: {token_count} tokens")
        print(f"   平均Token/字符: {token_count / len(long_text):.2f}")
        print()
        
        print("=== 演示完成 ===")
        
    except ImportError as e:
        print(f"导入错误: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_token_counter()