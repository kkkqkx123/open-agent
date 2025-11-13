"""BaseLLMWrapper单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Sequence, Optional

from src.infrastructure.llm.wrappers.base_wrapper import BaseLLMWrapper
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.exceptions import LLMError


class ConcreteLLMWrapper(BaseLLMWrapper):
    """具体实现类用于测试"""
    
    def __init__(self, name: str, config: Optional[dict] = None):
        super().__init__(name, config or {})
        self.generate_called = False
        self.generate_async_called = False
        self._supports_function_calling = False
    
    def set_supports_function_calling(self, value: bool):
        self._supports_function_calling = value
    
    async def generate_async(
        self,
        messages: Sequence,
        parameters=None,
        **kwargs
    ) -> LLMResponse:
        self.generate_async_called = True
        # 返回消息内容的处理结果
        prompt = self._messages_to_prompt(messages)
        return LLMResponse(
            content=f"async processed: {prompt}",
            message=Mock(),
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            model="test-model"
        )
    
    def generate(
        self,
        messages: Sequence,
        parameters=None,
        **kwargs
    ) -> LLMResponse:
        self.generate_called = True
        # 返回消息内容的处理结果
        prompt = self._messages_to_prompt(messages)
        return LLMResponse(
            content=f"sync processed: {prompt}",
            message=Mock(),
            token_usage=TokenUsage(
                prompt_tokens=5,
                completion_tokens=15,
                total_tokens=20
            ),
            model="test-model"
        )
    
    def get_model_info(self) -> dict:
        return {"name": self.name, "type": "test"}


class TestBaseLLMWrapper:
    """BaseLLMWrapper测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        wrapper = ConcreteLLMWrapper("test-wrapper", {"param": "value"})
        
        assert wrapper.name == "test-wrapper"
        assert wrapper.config == {"param": "value"}
        assert wrapper._metadata == {}
        assert wrapper._stats["total_requests"] == 0
        assert wrapper._stats["successful_requests"] == 0
        assert wrapper._stats["failed_requests"] == 0
        assert wrapper._stats["total_response_time"] == 0.0
        assert wrapper._stats["avg_response_time"] == 0.0
    
    def test_initialization_with_none_config(self):
        """测试用None配置初始化"""
        wrapper = ConcreteLLMWrapper("test-wrapper", None)
        
        assert wrapper.config == {}
    
    def test_generate_called(self):
        """测试同步生成方法被调用"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        result = wrapper.generate([])
        
        assert wrapper.generate_called
        assert "sync processed:" in result.content
        assert result.model == "test-model"
    
    def test_generate_async_called(self):
        """测试异步生成方法被调用"""
        async def run_test():
            wrapper = ConcreteLLMWrapper("test-wrapper")
            result = await wrapper.generate_async([])
            
            assert wrapper.generate_async_called
            assert "async processed:" in result.content
            assert result.model == "test-model"
        
        asyncio.run(run_test())
    
    def test_stream_generate(self):
        """测试流式生成"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        messages = [Mock(content="Hello world! This is a test message for streaming.")]
        
        chunks = list(wrapper.stream_generate(messages))
        
        # 检查内容是否被分块
        assert len(chunks) > 0
        combined = "".join(chunks)
        assert "Hello world!" in combined
    
    def test_stream_generate_async(self):
        """测试异步流式生成"""
        async def run_test():
            wrapper = ConcreteLLMWrapper("test-wrapper")
            messages = [Mock(content="Hello async world! This is a test message for streaming.")]
            
            chunks = []
            async for chunk in wrapper.stream_generate_async(messages):
                chunks.append(chunk)
            
            assert len(chunks) > 0
            combined = "".join(chunks)
            assert "Hello async world!" in combined
        
        asyncio.run(run_test())
    
    def test_get_token_count(self):
        """测试获取token数量"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        text = "Hello world! This is a test text."
        token_count = wrapper.get_token_count(text)
        
        # 默认实现是按字符数除以4
        expected = max(1, len(text) // 4)
        assert token_count == expected
    
    def test_get_messages_token_count(self):
        """测试获取消息列表的token数量"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        messages = [
            Mock(content="First message."),
            Mock(content="Second message."),
            Mock(content="Third message.")
        ]
        
        total_tokens = wrapper.get_messages_token_count(messages)
        
        # 每个消息的token数相加
        expected = sum(wrapper.get_token_count(str(msg.content)) for msg in messages)
        assert total_tokens == expected
    
    def test_supports_function_calling_default(self):
        """测试默认不支持函数调用"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        assert wrapper.supports_function_calling() is False
    
    def test_get_metadata(self):
        """测试获取元数据"""
        wrapper = ConcreteLLMWrapper("test-wrapper", {"param": "value"})
        wrapper._metadata = {"custom": "data"}
        
        metadata = wrapper.get_metadata()
        
        assert metadata["name"] == "test-wrapper"
        assert metadata["type"] == "ConcreteLLMWrapper"
        assert metadata["config"] == {"param": "value"}
        assert metadata["custom"] == "data"
        assert metadata["stats"] == wrapper._stats
    
    def test_get_stats(self):
        """测试获取统计信息"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        stats = wrapper.get_stats()
        
        assert stats == wrapper._stats
    
    def test_reset_stats(self):
        """测试重置统计信息"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        # 修改一些统计值
        wrapper._stats["total_requests"] = 10
        wrapper._stats["successful_requests"] = 8
        wrapper._stats["failed_requests"] = 2
        wrapper._stats["total_response_time"] = 5.0
        wrapper._stats["avg_response_time"] = 0.5
        
        wrapper.reset_stats()
        
        assert wrapper._stats["total_requests"] == 0
        assert wrapper._stats["successful_requests"] == 0
        assert wrapper._stats["failed_requests"] == 0
        assert wrapper._stats["total_response_time"] == 0.0
        assert wrapper._stats["avg_response_time"] == 0.0
    
    def test_update_stats_success(self):
        """测试更新统计信息（成功）"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        wrapper._update_stats(success=True, response_time=1.5)
        
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["successful_requests"] == 1
        assert wrapper._stats["failed_requests"] == 0
        assert wrapper._stats["total_response_time"] == 1.5
        assert wrapper._stats["avg_response_time"] == 1.5
    
    def test_update_stats_failure(self):
        """测试更新统计信息（失败）"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        wrapper._update_stats(success=False, response_time=2.0)
        
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["successful_requests"] == 0
        assert wrapper._stats["failed_requests"] == 1
        assert wrapper._stats["total_response_time"] == 2.0
        assert wrapper._stats["avg_response_time"] == 2.0
    
    def test_update_stats_multiple_calls(self):
        """测试多次更新统计信息"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        wrapper._update_stats(success=True, response_time=1.0)
        wrapper._update_stats(success=False, response_time=2.0)
        wrapper._update_stats(success=True, response_time=1.5)
        
        assert wrapper._stats["total_requests"] == 3
        assert wrapper._stats["successful_requests"] == 2
        assert wrapper._stats["failed_requests"] == 1
        assert wrapper._stats["total_response_time"] == 4.5
        assert wrapper._stats["avg_response_time"] == 1.5  # 4.5 / 3
    
    def test_messages_to_prompt(self):
        """测试将消息列表转换为提示词"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        messages = [
            Mock(content="First message"),
            Mock(content="Second message"),
            Mock(content="Third message")
        ]
        
        prompt = wrapper._messages_to_prompt(messages)
        
        expected = "First message\nSecond message\nThird message"
        assert prompt == expected
    
    def test_messages_to_prompt_with_non_content_messages(self):
        """测试将包含非内容消息的列表转换为提示词"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        messages = [
            Mock(content="First message"),
            "Plain string message",  # 没有content属性
            Mock(content="Third message")
        ]
        
        prompt = wrapper._messages_to_prompt(messages)
        
        expected = "First message\nPlain string message\nThird message"
        assert prompt == expected
    
    def test_messages_to_prompt_empty_list(self):
        """测试空消息列表转换"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        prompt = wrapper._messages_to_prompt([])
        
        assert prompt == ""
    
    def test_create_llm_response(self):
        """测试创建LLM响应"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        response = wrapper._create_llm_response(
            content="Test content",
            model="test-model",
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            metadata={"custom": "data"}
        )
        
        assert response.content == "Test content"
        assert response.model == "test-model"
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 20
        assert response.token_usage.total_tokens == 30
        assert response.metadata["custom"] == "data"
    
    def test_create_llm_response_with_defaults(self):
        """测试创建LLM响应（使用默认值）"""
        wrapper = ConcreteLLMWrapper("test-wrapper")
        
        response = wrapper._create_llm_response(
            content="Test content",
            model="test-model"
        )
        
        assert response.content == "Test content"
        assert response.model == "test-model"
        assert response.token_usage.prompt_tokens == 0
        assert response.token_usage.completion_tokens == 0
        assert response.token_usage.total_tokens == 0
        assert response.metadata == {}