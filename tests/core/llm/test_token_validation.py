"""测试Token验证功能"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.core.llm.clients.base import BaseLLMClient
from src.core.llm.config import LLMClientConfig
from src.interfaces.messages import IBaseMessage
from src.interfaces.llm.exceptions import LLMTokenLimitError


class MockLLMClient(BaseLLMClient):
    """用于测试的Mock LLM客户端"""
    
    async def _do_generate_async(self, messages, parameters, **kwargs):
        from src.infrastructure.llm.models import TokenUsage
        return self._create_response(
            content="Test response",
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
        )
    
    async def _do_stream_generate_async(self, messages, parameters, **kwargs):
        yield "Test"
        yield " "
        yield "response"
    
    def supports_function_calling(self):
        return True


class MockMessage(IBaseMessage):
    """用于测试的Mock消息"""
    
    def __init__(self, content: str):
        self._content = content
        self._id = f"msg_{id(self)}"
        self._timestamp = datetime.now()
    
    @property
    def content(self):
        return self._content
    
    @property
    def type(self):
        return "human"
    
    @property
    def additional_kwargs(self):
        return {}
    
    @property
    def response_metadata(self):
        return {}
    
    @property
    def name(self):
        return None
    
    @property
    def id(self):
        return self._id
    
    @property
    def timestamp(self):
        return self._timestamp
    
    def to_dict(self):
        return {
            "content": self._content,
            "type": self.type,
            "id": self._id,
            "timestamp": self._timestamp.isoformat()
        }
    
    def get_text_content(self):
        return self._content
    
    @classmethod
    def from_dict(cls, data):
        return cls(data.get("content", ""))
    
    def has_tool_calls(self):
        return False
    
    def get_tool_calls(self):
        return []
    
    def get_valid_tool_calls(self):
        return []
    
    def get_invalid_tool_calls(self):
        return []
    
    def add_tool_call(self, tool_call):
        pass


@pytest.fixture
def client_config():
    """创建客户端配置"""
    return LLMClientConfig(
        model_type="openai",
        model_name="gpt-3.5-turbo",
        max_tokens=100  # 设置token限制
    )


@pytest.fixture
def client(client_config):
    """创建客户端实例"""
    return MockLLMClient(client_config)


@pytest.fixture
def messages():
    """创建测试消息列表"""
    return [
        MockMessage("Hello"),
        MockMessage("How are you?"),
        MockMessage("This is a test message.")
    ]


def test_validate_token_limit_with_no_limit(client, messages):
    """测试没有设置token限制时的行为"""
    # 修改配置，移除token限制
    client.config.max_tokens = None
    
    # 应该不会抛出异常
    client._validate_token_limit(messages)


def test_validate_token_limit_within_limit(client, messages):
    """测试token数量在限制内的情况"""
    with patch('src.services.history.injection.get_token_calculation_service') as mock_get_service:
        # Mock TokenCalculationService
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 50  # 小于限制100
        mock_get_service.return_value = mock_service
        
        # 应该不会抛出异常
        client._validate_token_limit(messages)
        
        # 验证服务被正确调用
        mock_service.calculate_messages_tokens.assert_called_once_with(
            messages, "openai", "gpt-3.5-turbo"
        )


def test_validate_token_limit_exceeds_limit(client, messages):
    """测试token数量超过限制的情况"""
    with patch('src.services.history.injection.get_token_calculation_service') as mock_get_service:
        # Mock TokenCalculationService
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 150  # 超过限制100
        mock_get_service.return_value = mock_service
        
        # 应该抛出LLMTokenLimitError
        with pytest.raises(LLMTokenLimitError) as exc_info:
            client._validate_token_limit(messages)
        
        # 验证异常信息
        error = exc_info.value
        assert error.token_count == 150
        assert error.limit == 100
        assert error.model_name == "gpt-3.5-turbo"
        assert "Token数量超过限制: 150 > 100" in error.message


def test_validate_token_limit_service_error(client, messages):
    """测试TokenCalculationService出错时的行为"""
    with patch('src.services.history.injection.get_token_calculation_service') as mock_get_service:
        # Mock服务抛出异常
        mock_get_service.side_effect = Exception("Service unavailable")
        
        # 应该不会抛出异常，而是打印警告
        with patch('builtins.print') as mock_print:
            client._validate_token_limit(messages)
            mock_print.assert_called_once()
            assert "Warning: Token验证失败" in mock_print.call_args[0][0]


def test_validate_token_limit_calculation_error(client, messages):
    """测试token计算出错时的行为"""
    with patch('src.services.history.injection.get_token_calculation_service') as mock_get_service:
        # Mock TokenCalculationService
        mock_service = Mock()
        mock_service.calculate_messages_tokens.side_effect = Exception("Calculation failed")
        mock_get_service.return_value = mock_service
        
        # 应该不会抛出异常，而是打印警告
        with patch('builtins.print') as mock_print:
            client._validate_token_limit(messages)
            mock_print.assert_called_once()
            assert "Warning: Token验证失败" in mock_print.call_args[0][0]


def test_generate_with_token_validation(client, messages):
    """测试generate方法包含token验证"""
    with patch('src.services.history.injection.get_token_calculation_service') as mock_get_service:
        # Mock TokenCalculationService
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 50  # 小于限制
        mock_get_service.return_value = mock_service
        
        # 调用generate方法
        import asyncio
        response = asyncio.run(client.generate(messages))
        
        # 验证token验证被调用
        mock_service.calculate_messages_tokens.assert_called_once_with(
            messages, "openai", "gpt-3.5-turbo"
        )
        assert response.content == "Test response"


def test_stream_generate_with_token_validation(client, messages):
    """测试stream_generate方法包含token验证"""
    with patch('src.services.history.injection.get_token_calculation_service') as mock_get_service:
        # Mock TokenCalculationService
        mock_service = Mock()
        mock_service.calculate_messages_tokens.return_value = 50  # 小于限制
        mock_get_service.return_value = mock_service
        
        # 调用stream_generate方法
        import asyncio
        chunks = list(asyncio.run(client.stream_generate(messages)))
        
        # 验证token验证被调用
        mock_service.calculate_messages_tokens.assert_called_once_with(
            messages, "openai", "gpt-3.5-turbo"
        )
        assert chunks == ["Test", " ", "response"]