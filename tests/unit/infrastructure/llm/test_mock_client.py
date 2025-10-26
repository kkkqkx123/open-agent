"""Mock客户端单元测试"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.infrastructure.llm.clients.mock import MockLLMClient
from src.infrastructure.llm.config import MockConfig
from src.infrastructure.llm.models import TokenUsage
from src.infrastructure.llm.exceptions import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
)


class TestMockLLMClient:
    """Mock客户端测试类"""

    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MockConfig(
            model_type="mock",
            model_name="mock-model",
            response_delay=0.0,  # 测试时不延迟
            error_rate=0.0,  # 测试时不产生错误
            error_types=["timeout", "rate_limit"],
        )

    @pytest.fixture
    def client(self, config):
        """创建客户端实例"""
        return MockLLMClient(config)

    def test_init(self, config):
        """测试初始化"""
        client = MockLLMClient(config)

        assert client.config == config
        assert client.response_delay == 0.0
        assert client.error_rate == 0.0
        assert client.error_types == ["timeout", "rate_limit"]

    def test_generate_success(self, client):
        """测试成功生成"""
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        response = client.generate(messages)

        # 验证结果
        assert response.content == "这是一个模拟的LLM响应。"
        assert response.model == "mock-model"
        assert response.token_usage.total_tokens > 0
        assert response.finish_reason == "stop"

    def test_generate_coding_response(self, client):
        """测试代码生成响应"""
        # 执行测试
        messages = [HumanMessage(content="请写一个Python函数")]
        response = client.generate(messages)

        # 验证结果
        assert "代码生成" in response.content
        assert "def hello_world" in response.content

    def test_generate_analysis_response(self, client):
        """测试分析响应"""
        # 执行测试
        messages = [HumanMessage(content="请分析这些数据")]
        response = client.generate(messages)

        # 验证结果
        assert "数据分析" in response.content
        assert "结论" in response.content

    def test_generate_creative_response(self, client):
        """测试创意响应"""
        # 执行测试
        messages = [HumanMessage(content="请写一个创意故事")]
        response = client.generate(messages)

        # 验证结果
        assert "创意写作" in response.content
        assert "星球" in response.content

    def test_generate_translation_response(self, client):
        """测试翻译响应"""
        # 执行测试
        messages = [HumanMessage(content="请翻译这段文字")]
        response = client.generate(messages)

        # 验证结果
        assert "翻译" in response.content
        assert "Hello, World!" in response.content
        assert "你好，世界！" in response.content

    @pytest.mark.asyncio
    async def test_generate_async_success(self, client):
        """测试异步成功生成"""
        # 执行测试
        messages = [HumanMessage(content="测试输入")]
        response = await client.generate_async(messages)

        # 验证结果
        assert response.content == "这是一个模拟的LLM响应。"
        assert response.model == "mock-model"
        assert response.token_usage.total_tokens > 0

    def test_generate_with_error(self, config):
        """测试生成时产生错误"""
        # 设置错误率为100%
        config.error_rate = 1.0
        client = MockLLMClient(config)

        # 执行测试
        messages = [HumanMessage(content="测试输入")]

        # 应该抛出错误
        with pytest.raises(
            (
                LLMTimeoutError,
                LLMRateLimitError,
                LLMServiceUnavailableError,
                LLMInvalidRequestError,
            )
        ):
            client.generate(messages)

    def test_stream_generate(self, client):
        """测试流式生成"""
        # 执行测试
        messages = [HumanMessage(content="测试输入")]

        # 收集流式输出
        chunks = []
        for chunk in client.stream_generate(messages):
            chunks.append(chunk)

        # 验证结果
        full_content = "".join(chunks)
        assert full_content == "这是一个模拟的LLM响应。"
        assert len(chunks) > 1  # 应该有多个chunk

    @pytest.mark.asyncio
    async def test_stream_generate_async(self, client):
        """测试异步流式生成"""
        # 执行测试
        messages = [HumanMessage(content="测试输入")]

        # 收集流式输出
        chunks = []
        stream = client.stream_generate_async(messages)
        async for chunk in stream:
            chunks.append(chunk)

        # 验证结果
        full_content = "".join(chunks)
        assert full_content == "这是一个模拟的LLM响应。"
        assert len(chunks) > 1  # 应该有多个chunk

    def test_get_token_count(self, client):
        """测试计算token数量"""
        # 执行测试
        token_count = client.get_token_count("测试文本")

        # 验证结果（简单估算：字符数/4）
        assert token_count == 2  # "测试文本"有8个字符，8//4=2

    def test_get_messages_token_count(self, client):
        """测试计算消息列表的token数量"""
        # 执行测试
        messages = [HumanMessage(content="消息1"), AIMessage(content="消息2")]
        token_count = client.get_messages_token_count(messages)

        # 验证结果
        # 每条消息2个token + 4个格式token + 3个回复token
        assert token_count == 2 + 2 + 4 + 4 + 3

    def test_supports_function_calling(self, client):
        """测试是否支持函数调用"""
        assert client.supports_function_calling() is True

    def test_set_response_template(self, client):
        """测试设置响应模板"""
        # 设置自定义模板
        client.set_response_template("custom", "自定义响应模板")

        # 验证模板被设置
        assert client.get_response_template("custom") == "自定义响应模板"

    def test_set_error_rate(self, client):
        """测试设置错误率"""
        # 设置有效错误率
        client.set_error_rate(0.5)
        assert client.error_rate == 0.5

        # 设置无效错误率
        with pytest.raises(ValueError):
            client.set_error_rate(1.5)

        with pytest.raises(ValueError):
            client.set_error_rate(-0.1)

    def test_set_response_delay(self, client):
        """测试设置响应延迟"""
        # 设置有效延迟
        client.set_response_delay(0.5)
        assert client.response_delay == 0.5

        # 设置无效延迟
        with pytest.raises(ValueError):
            client.set_response_delay(-0.1)

    def test_maybe_throw_error(self, client):
        """测试随机错误抛出"""
        # 设置错误率为0，不应该抛出错误
        client.set_error_rate(0.0)
        client._maybe_throw_error()  # 不应该抛出错误

        # 设置错误率为100%，应该抛出错误
        client.set_error_rate(1.0)
        with pytest.raises(
            (
                LLMTimeoutError,
                LLMRateLimitError,
                LLMServiceUnavailableError,
                LLMInvalidRequestError,
            )
        ):
            client._maybe_throw_error()

    def test_handle_mock_error(self, client):
        """测试处理Mock错误"""
        # 测试已经是LLM错误的情况
        error = LLMTimeoutError("测试超时")
        result = client._handle_mock_error(error)
        assert result is error

        # 测试普通错误
        error = Exception("普通错误")
        result = client._handle_mock_error(error)
        assert isinstance(result, LLMInvalidRequestError)
        assert "Mock错误" in str(result)

    def test_generate_response_content(self, client):
        """测试生成响应内容"""
        # 测试默认响应
        messages = [HumanMessage(content="普通消息")]
        content = client._generate_response_content(messages)
        assert content == "这是一个模拟的LLM响应。"

        # 测试代码相关响应
        messages = [HumanMessage(content="请写代码")]
        content = client._generate_response_content(messages)
        assert "代码生成" in content

        # 测试分析相关响应
        messages = [HumanMessage(content="请分析数据")]
        content = client._generate_response_content(messages)
        assert "数据分析" in content

        # 测试创意相关响应
        messages = [HumanMessage(content="请创意写作")]
        content = client._generate_response_content(messages)
        assert "创意写作" in content

        # 测试翻译相关响应
        messages = [HumanMessage(content="请翻译文本")]
        content = client._generate_response_content(messages)
        assert "翻译" in content

    def test_estimate_token_usage(self, client):
        """测试估算Token使用情况"""
        # 执行测试
        token_usage = client._estimate_token_usage("测试内容")

        # 验证结果
        assert token_usage.prompt_tokens > 0
        assert token_usage.completion_tokens > 0
        assert (
            token_usage.total_tokens
            == token_usage.prompt_tokens + token_usage.completion_tokens
        )

    def test_empty_messages(self, client):
        """测试空消息列表"""
        # 执行测试
        response = client.generate([])

        # 验证结果
        assert response.content == "这是一个模拟的LLM响应。"

    def test_system_message_handling(self, client):
        """测试系统消息处理"""
        # 执行测试
        messages = [SystemMessage(content="系统指令"), HumanMessage(content="用户输入")]
        response = client.generate(messages)

        # 验证结果（Mock客户端不特别处理系统消息）
        assert response.content == "这是一个模拟的LLM响应。"
