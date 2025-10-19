"""错误处理功能演示"""

import sys
import os
sys.path.insert(0, 'src/llm')

def test_error_handler():
    print("=== 错误处理功能演示 ===\n")
    
    try:
        from error_handler import ErrorHandlerFactory, ErrorContext, BaseErrorHandler, OpenAIErrorHandler, GeminiErrorHandler, AnthropicErrorHandler
        from exceptions import (
            LLMCallError,
            LLMTimeoutError,
            LLMRateLimitError,
            LLMAuthenticationError,
            LLMModelNotFoundError,
            LLMTokenLimitError,
            LLMContentFilterError,
            LLMServiceUnavailableError,
            LLMInvalidRequestError
        )
        
        # 测试1: 测试不同模型的错误处理器
        print("1. 测试不同模型的错误处理器:")
        
        for model_type in ["openai", "gemini", "anthropic", "mock"]:
            handler = ErrorHandlerFactory.create_handler(model_type)
            print(f"   {model_type}处理器类型: {type(handler).__name__}")
        print()
        
        # 测试2: 测试基础错误处理
        print("2. 测试基础错误处理:")
        
        base_handler = BaseErrorHandler()
        
        # 测试各种错误类型
        test_errors = [
            TimeoutError("请求超时"),
            ConnectionError("连接失败"),
            Exception("rate limit exceeded"),
            Exception("authentication failed"),
            Exception("model not found"),
            Exception("token limit exceeded"),
            Exception("content filter triggered"),
            Exception("service unavailable"),
            Exception("invalid request"),
            Exception("unknown error")
        ]
        
        for error in test_errors:
            handled_error = base_handler.handle_error(error)
            print(f"   {type(error).__name__} -> {type(handled_error).__name__}: {str(handled_error)[:50]}...")
        print()
        
        # 测试3: 测试错误重试性判断
        print("3. 测试错误重试性判断:")
        
        retryable_errors = [
            LLMTimeoutError("超时错误"),
            LLMRateLimitError("频率限制"),
            LLMServiceUnavailableError("服务不可用"),
            LLMAuthenticationError("认证错误"),
            LLMModelNotFoundError("模型未找到"),
            LLMTokenLimitError("Token限制"),
            LLMContentFilterError("内容过滤"),
            LLMInvalidRequestError("无效请求")
        ]
        
        for error in retryable_errors:
            is_retryable = base_handler.is_retryable(error)
            print(f"   {type(error).__name__}: 可重试={is_retryable}")
        print()
        
        # 测试4: 测试错误上下文
        print("4. 测试错误上下文:")
        
        context = ErrorContext(
            model_name="gpt-4",
            model_type="openai",
            request_id="req-123"
        )
        
        print(f"   错误上下文: {context.to_dict()}")
        print()
        
        # 测试5: 测试特定错误处理器
        print("5. 测试特定错误处理器:")
        
        # OpenAI错误处理器
        openai_handler = OpenAIErrorHandler()
        
        # 模拟OpenAI错误
        class MockOpenAIError(Exception):
            def __init__(self, message, status_code=None):
                super().__init__(message)
                self.response = type('Response', (), {'status_code': status_code})
        
        openai_errors = [
            MockOpenAIError("API密钥无效", 401),
            MockOpenAIError("频率限制", 429),
            MockOpenAIError("模型未找到", 404),
            MockOpenAIError("请求无效", 400),
            MockOpenAIError("服务不可用", 503)
        ]
        
        for error in openai_errors:
            handled_error = openai_handler.handle_error(error)
            print(f"   OpenAI {error.response.status_code} -> {type(handled_error).__name__}")
        print()
        
        # 测试6: 测试支持的模型类型
        print("6. 测试支持的模型类型:")
        
        supported_types = ErrorHandlerFactory.get_supported_types()
        print(f"   支持的模型类型: {supported_types}")
        print()
        
        # 测试7: 测试错误恢复
        print("7. 测试错误恢复:")
        
        # 创建一个会失败的客户端
        from clients.mock_client import MockLLMClient
        from config import MockConfig
        
        failing_config = MockConfig(
            model_type="mock",
            model_name="failing-model",
            response_delay=0.1,
            error_rate=1.0,  # 100%错误率
            error_types=["timeout", "rate_limit"]
        )
        
        failing_client = MockLLMClient(failing_config)
        
        from langchain_core.messages import HumanMessage
        
        try:
            response = failing_client.generate([HumanMessage(content="测试")])
            print(f"   意外成功: {response.content}")
        except Exception as e:
            handled_error = base_handler.handle_error(e)
            print(f"   预期失败: {type(handled_error).__name__}: {str(handled_error)}")
            print(f"   可重试: {base_handler.is_retryable(handled_error)}")
        
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
    test_error_handler()