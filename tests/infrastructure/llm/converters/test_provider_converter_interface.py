"""提供商转换器接口测试

测试IProviderConverter接口的实现和功能。
"""

import pytest
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch
from src.interfaces.llm.converters import IProviderConverter
from src.infrastructure.llm.converters.provider_format_utils import (
    BaseProviderFormatUtils,
    ProviderFormatUtilsFactory,
    get_provider_format_utils_factory
)
from src.infrastructure.llm.converters.message_converters import (
    RequestConverter,
    ResponseConverter,
    get_provider_request_converter,
    get_provider_response_converter
)
from src.infrastructure.messages import HumanMessage, AIMessage

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage


class TestIProviderConverter:
    """测试IProviderConverter接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的，不能直接实例化"""
        with pytest.raises(TypeError):
            IProviderConverter()  # type: ignore
    
    def test_concrete_implementation(self):
        """测试具体实现类"""
        
        class ConcreteProviderConverter(IProviderConverter):
            def get_provider_name(self) -> str:
                return "test_provider"
            
            def convert_request(self, messages, parameters):
                return {"provider": "test", "messages": messages}
            
            def convert_response(self, response):
                return HumanMessage(content=response.get("content", ""))
        
        converter = ConcreteProviderConverter()
        assert converter.get_provider_name() == "test_provider"
        
        # 测试请求转换
        messages = [HumanMessage(content="Hello")]
        parameters = {"temperature": 0.7}
        request = converter.convert_request(messages, parameters)
        assert request["provider"] == "test"
        assert request["messages"] == messages
        
        # 测试响应转换
        response = {"content": "Hi there!"}
        message = converter.convert_response(response)
        assert isinstance(message, HumanMessage)
        assert message.content == "Hi there!"
        
        # 测试默认的流式响应转换
        events = [{"content": "Hello"}, {"content": " world"}]
        stream_message = converter.convert_stream_response(events)
        assert isinstance(stream_message, HumanMessage)
        
        # 测试默认的请求验证
        errors = converter.validate_request([], {})
        assert len(errors) > 0
        assert "消息列表不能为空" in errors[0]
        
        # 测试默认的错误处理
        error_response = {"error": {"message": "Test error", "code": "test"}}
        error_msg = converter.handle_api_error(error_response)
        assert "Test error" in error_msg
        assert "test" in error_msg


class TestBaseProviderFormatUtils:
    """测试BaseProviderFormatUtils基类"""
    
    def test_inherits_from_interface(self):
        """测试BaseProviderFormatUtils继承自IProviderConverter"""
        assert issubclass(BaseProviderFormatUtils, IProviderConverter)
    
    def test_abstract_methods(self):
        """测试抽象方法不能直接实例化"""
        with pytest.raises(TypeError):
            BaseProviderFormatUtils()  # type: ignore
    
    def test_concrete_implementation(self):
        """测试具体实现类"""
        
        class ConcreteFormatUtils(BaseProviderFormatUtils):
            def get_provider_name(self) -> str:
                return "test"
            
            def convert_request(self, messages, parameters):
                return {"test": "request"}
            
            def convert_response(self, response):
                return HumanMessage(content="test")
        
        utils = ConcreteFormatUtils()
        assert utils.get_provider_name() == "test"
        assert utils.convert_request([], {}) == {"test": "request"}
        assert isinstance(utils.convert_response({}), HumanMessage)


class TestProviderFormatUtilsFactory:
    """测试ProviderFormatUtilsFactory工厂类"""
    
    def test_get_supported_providers(self):
        """测试获取支持的提供商列表"""
        factory = ProviderFormatUtilsFactory()
        providers = factory.get_supported_providers()
        assert "openai" in providers
        assert "gemini" in providers
        assert "anthropic" in providers
    
    def test_get_format_utils(self):
        """测试获取格式转换工具"""
        factory = ProviderFormatUtilsFactory()
        
        # 测试OpenAI
        openai_utils = factory.get_format_utils("openai")
        assert openai_utils.get_provider_name() == "openai"
        
        # 测试Gemini
        gemini_utils = factory.get_format_utils("gemini")
        assert gemini_utils.get_provider_name() == "gemini"
        
        # 测试Anthropic
        anthropic_utils = factory.get_format_utils("anthropic")
        assert anthropic_utils.get_provider_name() == "anthropic"
    
    def test_get_format_utils_caching(self):
        """测试格式转换工具的缓存机制"""
        factory = ProviderFormatUtilsFactory()
        
        # 第一次获取
        openai_utils1 = factory.get_format_utils("openai")
        # 第二次获取
        openai_utils2 = factory.get_format_utils("openai")
        
        # 应该是同一个实例
        assert openai_utils1 is openai_utils2
    
    def test_unsupported_provider(self):
        """测试不支持的提供商"""
        factory = ProviderFormatUtilsFactory()
        with pytest.raises(ValueError, match="不支持的提供商"):
            factory.get_format_utils("unsupported")
    
    def test_register_provider(self):
        """测试注册新的提供商"""
        factory = ProviderFormatUtilsFactory()
        
        class TestProviderConverter(IProviderConverter):
            def get_provider_name(self) -> str:
                return "test_provider"
            
            def convert_request(self, messages, parameters):
                return {}
            
            def convert_response(self, response):
                return HumanMessage(content="test")
        
        # 注册新提供商
        factory.register_provider("test_provider", TestProviderConverter)
        
        # 验证可以获取
        utils = factory.get_format_utils("test_provider")
        assert isinstance(utils, TestProviderConverter)
        assert utils.get_provider_name() == "test_provider"
    
    def test_register_invalid_provider(self):
        """测试注册无效的提供商"""
        factory = ProviderFormatUtilsFactory()
        
        class InvalidConverter:
            pass
        
        with pytest.raises(ValueError, match="工具类必须继承自IProviderConverter"):
            factory.register_provider("invalid", InvalidConverter)


class TestRequestConverter:
    """测试RequestConverter类"""
    
    def test_initialization(self):
        """测试初始化"""
        converter = RequestConverter()
        assert converter.format_utils_factory is not None
        assert isinstance(converter._cache, dict)
    
    def test_convert_to_provider_request(self):
        """测试转换为提供商请求"""
        converter = RequestConverter()
        messages = [HumanMessage(content="Hello")]
        parameters = {"temperature": 0.7}
        
        # 测试OpenAI
        request = converter.convert_to_provider_request("openai", messages, parameters)
        assert "model" in request
        assert "messages" in request
        assert request["temperature"] == 0.7
        
        # 测试Gemini
        request = converter.convert_to_provider_request("gemini", messages, parameters)
        assert "contents" in request
        
        # 测试Anthropic
        request = converter.convert_to_provider_request("anthropic", messages, parameters)
        assert "model" in request
        assert "messages" in request
    
    def test_convert_to_provider_request_validation(self):
        """测试转换请求时的验证"""
        converter = RequestConverter()
        
        # 测试空provider
        with pytest.raises(ValueError, match="provider和messages不能为空"):
            converter.convert_to_provider_request("", [], {})
        
        # 测试空messages
        with pytest.raises(ValueError, match="provider和messages不能为空"):
            converter.convert_to_provider_request("openai", [], {})
    
    def test_compatibility_methods(self):
        """测试兼容性方法"""
        from typing import Sequence
        converter = RequestConverter()
        messages: Sequence["IBaseMessage"] = [HumanMessage(content="Hello")]
        parameters = {"temperature": 0.7}
        
        # 测试OpenAI兼容方法
        request = converter.convert_to_openai_request(messages, parameters)
        assert "model" in request
        assert "messages" in request
        
        # 测试Gemini兼容方法
        request = converter.convert_to_gemini_request(messages, parameters)
        assert "contents" in request
        
        # 测试Anthropic兼容方法
        request = converter.convert_to_anthropic_request(messages, parameters)
        assert "model" in request
        assert "messages" in request


class TestResponseConverter:
    """测试ResponseConverter类"""
    
    def test_initialization(self):
        """测试初始化"""
        converter = ResponseConverter()
        assert converter.format_utils_factory is not None
        assert isinstance(converter._cache, dict)
    
    def test_convert_from_provider_response(self):
        """测试从提供商响应转换"""
        converter = ResponseConverter()
        
        # 测试OpenAI响应
        openai_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello!"
                }
            }]
        }
        message = converter.convert_from_provider_response("openai", openai_response)
        assert isinstance(message, AIMessage)
        assert message.content == "Hello!"
        
        # 测试Gemini响应
        gemini_response = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Hello!"}]
                }
            }]
        }
        message = converter.convert_from_provider_response("gemini", gemini_response)
        assert isinstance(message, AIMessage)
        
        # 测试Anthropic响应
        anthropic_response = {
            "content": [{
                "type": "text",
                "text": "Hello!"
            }]
        }
        message = converter.convert_from_provider_response("anthropic", anthropic_response)
        assert isinstance(message, AIMessage)
        assert message.content == "Hello!"
    
    def test_convert_from_provider_response_validation(self):
        """测试转换响应时的验证"""
        converter = ResponseConverter()
        
        # 测试空provider
        with pytest.raises(ValueError, match="provider和response不能为空"):
            converter.convert_from_provider_response("", {})
        
        # 测试空response
        with pytest.raises(ValueError, match="provider和response不能为空"):
            converter.convert_from_provider_response("openai", {})
    
    def test_convert_from_provider_stream_response(self):
        """测试从提供商流式响应转换"""
        converter = ResponseConverter()
        
        # 测试OpenAI流式响应
        openai_events = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {"content": " world"}}]}
        ]
        message = converter.convert_from_provider_stream_response("openai", openai_events)
        assert isinstance(message, AIMessage)
        
        # 测试Gemini流式响应
        gemini_events = [
            {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]},
            {"candidates": [{"content": {"parts": [{"text": " world"}]}}]}
        ]
        message = converter.convert_from_provider_stream_response("gemini", gemini_events)
        assert isinstance(message, AIMessage)
        
        # 测试Anthropic流式响应
        anthropic_events = [
            {"type": "content_block_delta", "delta": {"text": "Hello"}},
            {"type": "content_block_delta", "delta": {"text": " world"}}
        ]
        message = converter.convert_from_provider_stream_response("anthropic", anthropic_events)
        assert isinstance(message, AIMessage)
    
    def test_convert_from_provider_stream_response_validation(self):
        """测试转换流式响应时的验证"""
        converter = ResponseConverter()
        
        # 测试空provider
        with pytest.raises(ValueError, match="provider和events不能为空"):
            converter.convert_from_provider_stream_response("", [])
        
        # 测试空events
        with pytest.raises(ValueError, match="provider和events不能为空"):
            converter.convert_from_provider_stream_response("openai", [])
    
    def test_error_handling(self):
        """测试错误处理"""
        converter = ResponseConverter()
        
        # 测试无效响应
        invalid_response = {"invalid": "response"}
        message = converter.convert_from_provider_response("openai", invalid_response)
        assert isinstance(message, AIMessage)
        assert message.content == ""  # 回退到空消息
        
        # 测试无效流式响应
        invalid_events = [{"invalid": "event"}]
        message = converter.convert_from_provider_stream_response("openai", invalid_events)
        assert isinstance(message, AIMessage)
        assert message.content == ""  # 回退到空消息


class TestGlobalInstances:
    """测试全局实例函数"""
    
    def test_get_provider_format_utils_factory(self):
        """测试获取全局工厂实例"""
        factory1 = get_provider_format_utils_factory()
        factory2 = get_provider_format_utils_factory()
        assert factory1 is factory2  # 应该是同一个实例
    
    def test_get_provider_request_converter(self):
        """测试获取全局请求转换器实例"""
        converter1 = get_provider_request_converter()
        converter2 = get_provider_request_converter()
        assert converter1 is converter2  # 应该是同一个实例
    
    def test_get_provider_response_converter(self):
        """测试获取全局响应转换器实例"""
        converter1 = get_provider_response_converter()
        converter2 = get_provider_response_converter()
        assert converter1 is converter2  # 应该是同一个实例