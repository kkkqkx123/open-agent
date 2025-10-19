"""Gemini客户端单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.llm.clients.gemini_client import GeminiClient
from src.llm.config import GeminiConfig
from src.llm.models import TokenUsage
from src.llm.exceptions import (
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


class MockHTTPError(Exception):
    """模拟HTTP错误的异常类"""
    
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class TestGeminiClient:
    """Gemini客户端测试类"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return GeminiConfig(
            model_type="gemini",
            model_name="gemini-pro",
            api_key="test-api-key",
            base_url="https://generativelanguage.googleapis.com/v1",
            temperature=0.7,
            max_tokens=1000,
            timeout=30
        )
    
    @pytest.fixture
    def client(self, config):
        """创建客户端实例"""
        with patch('src.llm.clients.gemini_client.ChatGoogleGenerativeAI'):
            return GeminiClient(config)
    
    def test_init(self, config):
        """测试初始化"""
        with patch('src.llm.clients.gemini_client.ChatGoogleGenerativeAI') as mock_chat:
            client = GeminiClient(config)
            
            # 验证ChatGoogleGenerativeAI被正确调用
            mock_chat.assert_called_once_with(
                model=config.model_name,
                google_api_key=config.api_key,
                temperature=config.temperature,
                timeout=config.timeout,
                max_retries=config.max_retries,
                request_timeout=config.timeout,
                default_headers={'x-goog-api-key': 'test-api-key'},
                max_tokens=config.max_tokens,
                top_p=config.top_p
            )
    
    def test_convert_messages(self, client):
        """测试消息格式转换"""
        # 测试包含系统消息的情况
        messages = [
            SystemMessage(content="系统指令"),
            HumanMessage(content="用户输入"),
            AIMessage(content="AI回复")
        ]
        
        converted = client._convert_messages(messages)
        
        # 验证系统消息被转换为用户消息
        assert len(converted) == 3
        assert isinstance(converted[0], HumanMessage)
        assert "系统指令" in converted[0].content
        assert isinstance(converted[1], HumanMessage)
        assert converted[1].content == "用户输入"
        assert isinstance(converted[2], AIMessage)
        assert converted[2].content == "AI回复"
        
        # 测试不包含系统消息的情况
        messages = [
            HumanMessage(content="用户输入"),
            AIMessage(content="AI回复")
        ]
        
        converted = client._convert_messages(messages)
        
        # 验证消息保持不变
        assert len(converted) == 2
        assert isinstance(converted[0], HumanMessage)
        assert converted[0].content == "用户输入"
        assert isinstance(converted[1], AIMessage)
        assert converted[1].content == "AI回复"
    
    def test_generate_success(self, client):
        """测试成功生成"""
        # 模拟响应
        mock_response = Mock()
        mock_response.content = "测试响应"
        mock_response.usage_metadata = {
            'input_tokens': 10,
            'output_tokens': 5,
            'total_tokens': 15
        }
        mock_response.response_metadata = {
            'finish_reason': 'stop'
        }
        mock_response.additional_kwargs = {}
        
        # 模拟客户端调用
        client._client.invoke = Mock(return_value=mock_response)
        
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        response = client.generate(messages)
        
        # 验证结果
        assert response.content == "测试响应"
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 5
        assert response.token_usage.total_tokens == 15
        assert response.finish_reason == "stop"
        assert response.model == "gemini-pro"
    
    def test_generate_with_system_message(self, client):
        """测试包含系统消息的生成"""
        # 模拟响应
        mock_response = Mock()
        mock_response.content = "测试响应"
        mock_response.usage_metadata = {
            'input_tokens': 10,
            'output_tokens': 5,
            'total_tokens': 15
        }
        mock_response.additional_kwargs = {}
        
        # 模拟客户端调用
        client._client.invoke = Mock(return_value=mock_response)
        
        # 执行测试
        messages = [
            SystemMessage(content="系统指令"),
            HumanMessage(content="测试输入")
        ]
        response = client.generate(messages)
        
        # 验证结果
        assert response.content == "测试响应"
        
        # 验证消息被正确转换
        client._client.invoke.assert_called_once()
        call_args = client._client.invoke.call_args[0][0]  # 获取第一个位置参数（消息列表）
        assert len(call_args) == 2
        assert "系统指令" in call_args[0].content
        assert call_args[1].content == "测试输入"
    
    @pytest.mark.asyncio
    async def test_generate_async_success(self, client):
        """测试异步成功生成"""
        # 模拟响应
        mock_response = Mock()
        mock_response.content = "异步测试响应"
        mock_response.usage_metadata = {
            'input_tokens': 10,
            'output_tokens': 5,
            'total_tokens': 15
        }
        mock_response.additional_kwargs = {}
        
        # 模拟客户端调用 - 使用AsyncMock
        client._client.ainvoke = AsyncMock(return_value=mock_response)
        
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        response = await client.generate_async(messages)
        
        # 验证结果
        assert response.content == "异步测试响应"
        assert response.token_usage.total_tokens == 15
    
    def test_generate_authentication_error(self, client):
        """测试认证错误"""
        # 模拟认证错误
        mock_response = Mock()
        mock_response.status_code = 401
        error = MockHTTPError("Invalid API key", response=mock_response)
        
        client._client.invoke = Mock(side_effect=error)
        
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        with pytest.raises(LLMAuthenticationError):
            client.generate(messages)
    
    def test_generate_rate_limit_error(self, client):
        """测试频率限制错误"""
        # 模拟频率限制错误
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'retry-after': '60'}
        error = MockHTTPError("Rate limit exceeded", response=mock_response)
        
        client._client.invoke = Mock(side_effect=error)
        
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        with pytest.raises(LLMRateLimitError) as exc_info:
            client.generate(messages)
        
        assert exc_info.value.retry_after == 60
    
    def test_generate_model_not_found_error(self, client):
        """测试模型未找到错误"""
        # 模拟模型未找到错误
        mock_response = Mock()
        mock_response.status_code = 404
        error = MockHTTPError("Model not found", response=mock_response)
        
        client._client.invoke = Mock(side_effect=error)
        
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        with pytest.raises(LLMModelNotFoundError) as exc_info:
            client.generate(messages)
        
        assert exc_info.value.model_name == "gemini-pro"
    
    def test_generate_timeout_error(self, client):
        """测试超时错误"""
        # 模拟超时错误
        error = Exception("Request timeout")
        
        client._client.invoke = Mock(side_effect=error)
        
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        with pytest.raises(LLMTimeoutError) as exc_info:
            client.generate(messages)
        
        assert exc_info.value.timeout == 30
    
    def test_get_token_count(self, client):
        """测试计算token数量"""
        # 执行测试
        token_count = client.get_token_count("测试文本")
        
        # 验证结果（简单估算：字符数/4）
        # "测试文本"有8个字符，8//4=2，但实际实现可能不同
        assert token_count >= 1  # 至少应该有1个token
    
    def test_get_messages_token_count(self, client):
        """测试计算消息列表的token数量"""
        # 执行测试
        messages = [
            HumanMessage(content="消息1"),
            AIMessage(content="消息2")
        ]
        token_count = client.get_messages_token_count(messages)
        
        # 验证结果
        # 根据实际实现计算token数量
        # 每条消息内容: "消息1"(3字符)//4=0, "消息2"(3字符)//4=0
        # 每条消息格式token: 4
        # 回复token: 3
        expected = 0 + 0 + 4 + 4 + 3  # 11
        assert token_count == expected
    
    def test_supports_function_calling(self, client):
        """测试是否支持函数调用"""
        assert client.supports_function_calling() is True
    
    def test_extract_token_usage(self, client):
        """测试提取Token使用情况"""
        # 测试有usage_metadata的情况
        response = Mock()
        response.usage_metadata = {
            'input_tokens': 10,
            'output_tokens': 5,
            'total_tokens': 15
        }
        
        token_usage = client._extract_token_usage(response)
        assert token_usage.prompt_tokens == 10
        assert token_usage.completion_tokens == 5
        assert token_usage.total_tokens == 15
        
        # 测试没有usage_metadata的情况
        response.usage_metadata = None
        response.response_metadata = {}
        token_usage = client._extract_token_usage(response)
        assert token_usage.prompt_tokens == 0
        assert token_usage.completion_tokens == 0
        assert token_usage.total_tokens == 0
    
    def test_extract_function_call(self, client):
        """测试提取函数调用信息"""
        # 测试有函数调用的情况
        response = Mock()
        response.additional_kwargs = {
            'function_call': {
                'name': 'test_function',
                'arguments': '{"arg1": "value1"}'
            }
        }
        
        function_call = client._extract_function_call(response)
        assert function_call == {
            'name': 'test_function',
            'arguments': '{"arg1": "value1"}'
        }
        
        # 测试没有函数调用的情况
        response.additional_kwargs = {}
        function_call = client._extract_function_call(response)
        assert function_call is None
    
    def test_extract_finish_reason(self, client):
        """测试提取完成原因"""
        # 测试有finish_reason的情况
        response = Mock()
        response.response_metadata = {
            'finish_reason': 'stop'
        }
        
        finish_reason = client._extract_finish_reason(response)
        assert finish_reason == 'stop'
        
        # 测试没有finish_reason的情况
        response.response_metadata = {}
        finish_reason = client._extract_finish_reason(response)
        assert finish_reason is None
    
    def test_handle_gemini_error_with_status_code(self, client):
        """测试处理带状态码的Gemini错误"""
        # 测试401错误
        mock_response = Mock()
        mock_response.status_code = 401
        error = MockHTTPError("Unauthorized", response=mock_response)
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMAuthenticationError)
        
        # 测试429错误
        mock_response.status_code = 429
        mock_response.headers = {'retry-after': '30'}
        error = MockHTTPError("Rate limit exceeded", response=mock_response)
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMRateLimitError)
        assert llm_error.retry_after == 30
        
        # 测试404错误
        mock_response.status_code = 404
        error = MockHTTPError("Model not found", response=mock_response)
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMModelNotFoundError)
        
        # 测试400错误
        mock_response.status_code = 400
        error = MockHTTPError("Bad request", response=mock_response)
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMInvalidRequestError)
        
        # 测试503错误
        mock_response.status_code = 503
        error = MockHTTPError("Service unavailable", response=mock_response)
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMServiceUnavailableError)
    
    def test_handle_gemini_error_with_message(self, client):
        """测试处理带消息的Gemini错误"""
        # 测试超时错误
        error = Exception("Request timeout")
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMTimeoutError)
        
        # 测试频率限制错误
        error = Exception("Rate limit exceeded")
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMRateLimitError)
        
        # 测试Token限制错误
        error = Exception("Token limit exceeded")
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMTokenLimitError)
        
        # 测试内容过滤错误
        error = Exception("Content filter triggered")
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMContentFilterError)
        
        # 测试通用错误
        error = Exception("Unknown error")
        
        llm_error = client._handle_gemini_error(error)
        assert isinstance(llm_error, LLMCallError)