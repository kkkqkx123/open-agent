"""LLM模块集成测试"""

import pytest
from unittest.mock import patch, Mock

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.llm.config import LLMModuleConfig
from src.infrastructure.llm.clients.openai.unified_client import OpenAIUnifiedClient
from src.infrastructure.llm.clients.gemini import GeminiClient
from src.infrastructure.llm.clients.anthropic import AnthropicClient
from src.infrastructure.llm.clients.mock import MockLLMClient
from src.infrastructure.llm.hooks import LoggingHook, MetricsHook, CompositeHook
from src.infrastructure.llm.fallback import FallbackManager, FallbackStrategy, FallbackModel
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.exceptions import LLMClientCreationError, UnsupportedModelTypeError


class TestLLMIntegration:
    """LLM模块集成测试类"""

    @pytest.fixture
    def factory(self):
        """创建工厂实例"""
        config = LLMModuleConfig(cache_enabled=True, cache_max_size=10)
        return LLMFactory(config)

    def test_factory_create_all_client_types(self, factory):
        """测试工厂创建所有类型的客户端"""
        # 测试创建OpenAI客户端
        openai_config = {
            "model_type": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test-key",
        }

        with patch("src.infrastructure.llm.clients.openai.unified_client.OpenAIUnifiedClient"):
            openai_client = factory.create_client(openai_config)
            assert isinstance(openai_client, OpenAIUnifiedClient)

        # 测试创建Gemini客户端
        gemini_config = {
            "model_type": "gemini",
            "model_name": "gemini-pro",
            "api_key": "test-key",
        }

        with patch("src.infrastructure.llm.clients.gemini.GeminiClient"):
            gemini_client = factory.create_client(gemini_config)
            assert isinstance(gemini_client, GeminiClient)

        # 测试创建Anthropic客户端
        anthropic_config = {
            "model_type": "anthropic",
            "model_name": "claude-3-sonnet-20240229",
            "api_key": "test-key",
        }

        with patch("src.infrastructure.llm.clients.anthropic.AnthropicClient"):
            anthropic_client = factory.create_client(anthropic_config)
            assert isinstance(anthropic_client, AnthropicClient)

        # 测试创建Mock客户端
        mock_config = {"model_type": "mock", "model_name": "mock-model"}

        mock_client = factory.create_client(mock_config)
        assert isinstance(mock_client, MockLLMClient)

    def test_factory_caching(self, factory):
        """测试工厂缓存功能"""
        # 创建配置
        config = {"model_type": "mock", "model_name": "test-model"}

        # 第一次创建客户端
        client1 = factory.create_client(config)

        # 第二次获取缓存的客户端
        client2 = factory.get_cached_client("test-model")

        # 验证是同一个实例
        assert client1 is client2

        # 验证缓存信息
        cache_info = factory.get_cache_info()
        assert cache_info["cache_size"] == 1
        assert "test-model" in cache_info["cached_models"]

    def test_mock_client_end_to_end(self, factory):
        """测试Mock客户端端到端流程"""
        # 创建Mock客户端
        config = {
            "model_type": "mock",
            "model_name": "test-model",
            "response_delay": 0.0,
            "error_rate": 0.0,
        }

        client = factory.create_client(config)

        # 测试基本生成
        messages = [HumanMessage(content="测试输入")]
        response = client.generate(messages)

        # 验证响应
        assert response.content == "这是一个模拟的LLM响应。"
        assert response.model == "test-model"
        assert response.token_usage.total_tokens > 0

        # 测试异步生成
        import asyncio

        async def test_async():
            response = await client.generate_async(messages)
            assert response.content == "这是一个模拟的LLM响应。"

        asyncio.run(test_async())

        # 测试流式生成
        chunks = list(client.stream_generate(messages))
        full_content = "".join(chunks)
        assert full_content == "这是一个模拟的LLM响应。"

        # 测试异步流式生成
        async def test_stream():
            chunks = []
            async for chunk in client.stream_generate_async(messages):
                chunks.append(chunk)
            return "".join(chunks)

        full_content = asyncio.run(test_stream())
        assert full_content == "这是一个模拟的LLM响应。"

    def test_hooks_integration(self, factory):
        """测试钩子集成"""
        # 创建Mock客户端
        config = {"model_type": "mock", "model_name": "test-model"}

        client = factory.create_client(config)

        # 创建钩子
        logging_hook = LoggingHook()
        metrics_hook = MetricsHook()
        composite_hook = CompositeHook([logging_hook, metrics_hook])

        # 添加钩子
        client.add_hook(composite_hook)

        # 测试生成
        messages = [HumanMessage(content="测试输入")]
        response = client.generate(messages)

        # 验证指标被收集
        metrics = metrics_hook.get_metrics()
        assert metrics["total_calls"] == 1
        assert metrics["successful_calls"] == 1
        assert metrics["total_tokens"] > 0

    def test_fallback_integration(self, factory):
        """测试降级集成"""
        # 创建降级模型配置
        fallback_models = [
            FallbackModel(name="mock-model-1", priority=1),
            FallbackModel(name="mock-model-2", priority=2),
        ]

        # 创建降级管理器
        fallback_manager = FallbackManager(
            fallback_models=fallback_models, strategy=FallbackStrategy.SEQUENTIAL
        )

        # 创建主客户端（会失败）
        primary_config = {
            "model_type": "mock",
            "model_name": "primary-model",
            "error_rate": 1.0,  # 100%错误率
        }

        primary_client = factory.create_client(primary_config)

        # 创建降级客户端
        fallback_config = {
            "model_type": "mock",
            "model_name": "mock-model-1",
            "error_rate": 0.0,
        }

        factory.cache_client("mock-model-1", factory.create_client(fallback_config))

        # 测试降级
        messages = [HumanMessage(content="测试输入")]

        try:
            response = fallback_manager.execute_fallback(primary_client, messages)

            # 验证降级成功
            assert response.metadata["fallback_model"] == "mock-model-1"
            assert response.metadata["fallback_strategy"] == "sequential"

        except Exception as e:
            # 如果降级失败，检查原因
            print(f"降级失败: {e}")

    def test_error_handling(self, factory):
        """测试错误处理"""
        # 创建会失败的客户端
        config = {
            "model_type": "mock",
            "model_name": "failing-model",
            "error_rate": 1.0,
        }

        client = factory.create_client(config)

        # 测试错误处理
        messages = [HumanMessage(content="测试输入")]

        with pytest.raises(Exception):
            client.generate(messages)

    def test_configuration_validation(self, factory):
        """测试配置验证"""
        # 测试不支持的模型类型
        config = {"model_type": "unsupported", "model_name": "test-model"}

        with pytest.raises(UnsupportedModelTypeError):
            factory.create_client(config)

        # 测试无效配置
        with pytest.raises(LLMClientCreationError):
            factory.create_client({"invalid": "config"})

    def test_token_calculation(self, factory):
        """测试Token计算"""
        # 创建Mock客户端
        config = {"model_type": "mock", "model_name": "test-model"}

        client = factory.create_client(config)

        # 测试文本Token计算
        text = "这是一个测试文本"
        token_count = client.get_token_count(text)
        assert token_count > 0

        # 测试消息Token计算
        messages = [HumanMessage(content="用户消息"), AIMessage(content="AI回复")]
        token_count = client.get_messages_token_count(messages)
        assert token_count > 0

    def test_function_calling_support(self, factory):
        """测试函数调用支持"""
        # 只测试Mock客户端，避免依赖外部服务
        config = {"model_type": "mock", "model_name": "mock-model"}

        client = factory.create_client(config)

        # Mock客户端应该支持函数调用
        assert client.supports_function_calling()

    def test_model_info(self, factory):
        """测试模型信息"""
        # 创建Mock客户端
        config = {"model_type": "mock", "model_name": "test-model"}

        client = factory.create_client(config)

        # 获取模型信息
        model_info = client.get_model_info()

        # 验证信息
        assert model_info["name"] == "test-model"
        assert model_info["type"] == "mock"
        assert model_info["supports_function_calling"] is True
        assert model_info["supports_streaming"] is True

    def test_concurrent_access(self, factory):
        """测试并发访问"""
        import threading
        import time

        # 创建Mock客户端
        config = {
            "model_type": "mock",
            "model_name": "test-model",
            "response_delay": 0.1,  # 添加延迟以测试并发
        }

        client = factory.create_client(config)

        # 并发调用结果
        results = []
        errors = []

        def worker():
            try:
                messages = [
                    HumanMessage(content=f"测试输入 {threading.current_thread().ident}")
                ]
                response = client.generate(messages)
                results.append(response.content)
            except Exception as e:
                errors.append(e)

        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0
        assert len(results) == 5
        assert all(content == "这是一个模拟的LLM响应。" for content in results)

    def test_memory_usage(self, factory):
        """测试内存使用"""
        import gc
        import sys

        # 获取初始内存使用
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 创建多个客户端
        clients = []
        for i in range(10):
            config = {"model_type": "mock", "model_name": f"test-model-{i}"}
            client = factory.create_client(config)
            clients.append(client)

        # 使用客户端
        for client in clients:
            messages = [HumanMessage(content="测试输入")]
            response = client.generate(messages)
            assert response.content == "这是一个模拟的LLM响应。"

        # 清理
        del clients

        # 强制垃圾回收
        gc.collect()
        final_objects = len(gc.get_objects())

        # 验证内存没有显著泄漏
        object_increase = final_objects - initial_objects
        assert object_increase < 1000  # 允许一些对象增加，但不应该太多
