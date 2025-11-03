"""连接池、降级系统和重试机制集成测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage

from src.infrastructure.llm.pool.connection_pool import HTTPConnectionPool
from src.infrastructure.llm.pool.factory import ConnectionPoolFactory
from src.infrastructure.llm.fallback_system.fallback_manager import FallbackManager
from src.infrastructure.llm.fallback_system.fallback_config import FallbackConfig
from src.infrastructure.llm.fallback_system.interfaces import IClientFactory
from src.infrastructure.llm.retry.retry_manager import RetryManager
from src.infrastructure.llm.retry.retry_config import RetryConfig
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.exceptions import LLMCallError


class MockLLMClient:
    """模拟LLM客户端"""
    
    def __init__(self, model_name: str, should_fail: bool = False,
                 fail_on_attempt: int | None = None, response_delay: float = 0.0):
        self.model_name = model_name
        self.should_fail = should_fail
        self.fail_on_attempt = fail_on_attempt
        self.response_delay = response_delay
        self.call_count = 0
        self.pool = None  # 用于测试连接池集成
    
    async def generate_async(self, messages, parameters=None, **kwargs):
        """异步生成方法"""
        self.call_count += 1
        
        # 模拟响应延迟
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)
        
        # 模拟失败
        if self.should_fail:
            if self.fail_on_attempt is None or self.call_count >= self.fail_on_attempt:
                if "timeout" in self.model_name.lower():
                    raise asyncio.TimeoutError("请求超时")
                elif "rate_limit" in self.model_name.lower():
                    raise LLMCallError("频率限制")
                else:
                    raise LLMCallError(f"模拟失败 - {self.model_name}")
        
        return LLMResponse(
            content=f"来自 {self.model_name} 的响应",
            message=f"来自 {self.model_name} 的响应",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            model=self.model_name
        )


class MockClientFactory(IClientFactory):
    """模拟客户端工厂"""
    
    def __init__(self):
        self.clients = {}
        self.available_models = ["primary_model", "fallback_model1", "fallback_model2"]
    
    def create_client(self, model_name: str):
        """创建客户端"""
        if model_name not in self.clients:
            # 根据模型名称创建不同行为的客户端
            if "timeout" in model_name:
                self.clients[model_name] = MockLLMClient(model_name, should_fail=True, response_delay=2.0)
            elif "rate_limit" in model_name:
                self.clients[model_name] = MockLLMClient(model_name, should_fail=True)
            else:
                self.clients[model_name] = MockLLMClient(model_name)
        return self.clients[model_name]
    
    def get_available_models(self):
        """获取可用模型列表"""
        return self.available_models.copy()


class TestPoolFallbackRetryIntegration:
    """连接池、降级系统和重试机制集成测试"""
    
    @pytest.fixture
    def connection_pool(self):
        """创建连接池"""
        return HTTPConnectionPool(max_connections=5, max_keepalive=3, timeout=10.0)
    
    @pytest.fixture
    def fallback_config(self):
        """创建降级配置"""
        return FallbackConfig(
            enabled=True,
            max_attempts=3,
            fallback_models=["fallback_model1", "fallback_model2"],
            strategy_type="sequential",
            base_delay=0.1,
            max_delay=1.0
        )
    
    @pytest.fixture
    def retry_config(self):
        """创建重试配置"""
        return RetryConfig(
            enabled=True,
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            jitter=False
        )
    
    @pytest.fixture
    def client_factory(self):
        """创建客户端工厂"""
        return MockClientFactory()
    
    @pytest.fixture
    def fallback_manager(self, fallback_config, client_factory):
        """创建降级管理器"""
        return FallbackManager(fallback_config, client_factory)
    
    @pytest.fixture
    def retry_manager(self, retry_config):
        """创建重试管理器"""
        return RetryManager(retry_config)
    
    @pytest.mark.asyncio
    async def test_successful_request_with_all_systems(self, connection_pool, fallback_manager):
        """测试所有系统正常工作时的成功请求"""
        messages = [HumanMessage(content="测试消息")]
        
        # 模拟连接池获取连接
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 获取连接
            connection = await connection_pool.acquire("https://api.example.com")
            
            # 执行降级管理器
            response = await fallback_manager.generate_with_fallback(
                messages, primary_model="primary_model"
            )
            
            # 释放连接
            await connection_pool.release("https://api.example.com", connection)
            
            # 验证响应
            assert response.content == "来自 primary_model 的响应"
            assert response.model == "primary_model"
            
            # 验证连接池统计
            stats = connection_pool.get_stats()
            assert stats["total_requests"] == 1
            assert stats["created_connections"] == 1
            
            # 验证降级管理器统计
            fallback_stats = fallback_manager.get_stats()
            assert fallback_stats["successful_sessions"] == 1
            assert fallback_stats["total_attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_fallback_with_retry_integration(self, connection_pool, fallback_manager, retry_manager):
        """测试降级与重试的集成"""
        messages = [HumanMessage(content="测试消息")]
        
        # 设置主模型失败，需要降级
        client_factory = fallback_manager.client_factory
        client_factory.clients["primary_model"] = MockLLMClient("primary_model", should_fail=True)
        
        # 模拟连接池获取连接
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 获取连接
            connection = await connection_pool.acquire("https://api.example.com")
            
            # 使用重试管理器包装降级管理器
            async def fallback_with_retry():
                return await fallback_manager.generate_with_fallback(
                    messages, primary_model="primary_model"
                )
            
            response = await retry_manager.execute_with_retry_async(fallback_with_retry)
            
            # 释放连接
            await connection_pool.release("https://api.example.com", connection)
            
            # 验证响应来自降级模型
            assert response.content == "来自 fallback_model1 的响应"
            assert response.model == "fallback_model1"
            
            # 验证降级管理器统计
            fallback_stats = fallback_manager.get_stats()
            assert fallback_stats["successful_sessions"] == 1
            assert fallback_stats["fallback_usage"] == 1
            
            # 验证重试管理器统计
            retry_stats = retry_manager.get_stats()
            assert retry_stats["successful_sessions"] == 1
    
    @pytest.mark.asyncio
    async def test_connection_pool_with_fallback_failures(self, connection_pool, fallback_manager):
        """测试连接池与降级失败的集成"""
        messages = [HumanMessage(content="测试消息")]
        
        # 设置所有模型都失败
        client_factory = fallback_manager.client_factory
        for model in ["primary_model", "fallback_model1", "fallback_model2"]:
            client_factory.clients[model] = MockLLMClient(model, should_fail=True)
        
        # 模拟连接池获取连接
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 获取连接
            connection = await connection_pool.acquire("https://api.example.com")
            
            # 执行降级管理器，应该失败
            with pytest.raises(LLMCallError):
                await fallback_manager.generate_with_fallback(
                    messages, primary_model="primary_model"
                )
            
            # 释放连接
            await connection_pool.release("https://api.example.com", connection)
            
            # 验证降级管理器统计
            fallback_stats = fallback_manager.get_stats()
            assert fallback_stats["failed_sessions"] == 1
            assert fallback_stats["total_attempts"] == 3
            
            # 验证连接池统计
            pool_stats = connection_pool.get_stats()
            assert pool_stats["total_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_connection_pool_reuse_with_fallback(self, connection_pool, fallback_manager):
        """测试连接池重用与降级的集成"""
        messages = [HumanMessage(content="测试消息")]
        
        # 模拟连接池获取连接
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 第一次请求
            connection1 = await connection_pool.acquire("https://api.example.com")
            response1 = await fallback_manager.generate_with_fallback(
                messages, primary_model="primary_model"
            )
            await connection_pool.release("https://api.example.com", connection1)
            
            # 第二次请求，应该重用连接
            connection2 = await connection_pool.acquire("https://api.example.com")
            response2 = await fallback_manager.generate_with_fallback(
                messages, primary_model="primary_model"
            )
            await connection_pool.release("https://api.example.com", connection2)
            
            # 验证响应
            assert response1.content == "来自 primary_model 的响应"
            assert response2.content == "来自 primary_model 的响应"
            
            # 验证连接重用
            pool_stats = connection_pool.get_stats()
            assert pool_stats["created_connections"] == 1
            assert pool_stats["connection_reuses"] == 1
            assert pool_stats["total_requests"] == 2
    
    @pytest.mark.asyncio
    async def test_timeout_handling_with_all_systems(self, connection_pool, fallback_manager, retry_manager):
        """测试超时处理与所有系统的集成"""
        messages = [HumanMessage(content="测试消息")]
        
        # 设置超时客户端
        client_factory = fallback_manager.client_factory
        client_factory.clients["primary_model"] = MockLLMClient("timeout_model", should_fail=True)
        client_factory.clients["fallback_model1"] = MockLLMClient("fallback_model1")
        
        # 模拟连接池获取连接
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 获取连接
            connection = await connection_pool.acquire("https://api.example.com")
            
            # 使用重试管理器包装降级管理器
            async def fallback_with_retry():
                return await fallback_manager.generate_with_fallback(
                    messages, primary_model="timeout_model"
                )
            
            # 设置较短的超时时间
            retry_manager.config.per_attempt_timeout = 1.0
            
            response = await retry_manager.execute_with_retry_async(fallback_with_retry)
            
            # 释放连接
            await connection_pool.release("https://api.example.com", connection)
            
            # 验证响应来自降级模型
            assert response.content == "来自 fallback_model1 的响应"
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling_with_all_systems(self, connection_pool, fallback_manager, retry_manager):
        """测试频率限制处理与所有系统的集成"""
        messages = [HumanMessage(content="测试消息")]
        
        # 设置频率限制客户端
        client_factory = fallback_manager.client_factory
        client_factory.clients["primary_model"] = MockLLMClient("rate_limit_model", should_fail=True)
        client_factory.clients["fallback_model1"] = MockLLMClient("rate_limit_model", should_fail=True)
        client_factory.clients["fallback_model2"] = MockLLMClient("fallback_model2")
        
        # 模拟连接池获取连接
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 获取连接
            connection = await connection_pool.acquire("https://api.example.com")
            
            # 使用重试管理器包装降级管理器
            async def fallback_with_retry():
                return await fallback_manager.generate_with_fallback(
                    messages, primary_model="rate_limit_model"
                )
            
            response = await retry_manager.execute_with_retry_async(fallback_with_retry)
            
            # 释放连接
            await connection_pool.release("https://api.example.com", connection)
            
            # 验证响应来自第二个降级模型
            assert response.content == "来自 fallback_model2 的响应"
            
            # 验证降级管理器统计
            fallback_stats = fallback_manager.get_stats()
            assert fallback_stats["successful_sessions"] == 1
            assert fallback_stats["total_attempts"] == 3  # 主模型 + 两个降级模型
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_with_all_systems(self, connection_pool, fallback_manager):
        """测试并发请求与所有系统的集成"""
        messages = [HumanMessage(content="测试消息")]
        
        # 模拟连接池获取连接
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_sessions = [AsyncMock() for _ in range(5)]
            mock_session_class.side_effect = mock_sessions
            
            # 创建多个并发请求
            async def make_request(request_id):
                connection = await connection_pool.acquire("https://api.example.com")
                response = await fallback_manager.generate_with_fallback(
                    messages, primary_model="primary_model"
                )
                await connection_pool.release("https://api.example.com", connection)
                return request_id, response
            
            # 执行并发请求
            tasks = [make_request(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            # 验证所有请求都成功
            assert len(results) == 5
            for request_id, response in results:
                assert response.content == "来自 primary_model 的响应"
            
            # 验证连接池统计
            pool_stats = connection_pool.get_stats()
            assert pool_stats["total_requests"] == 5
            assert pool_stats["created_connections"] == 5
            
            # 验证降级管理器统计
            fallback_stats = fallback_manager.get_stats()
            assert fallback_stats["successful_sessions"] == 5
    
    def test_factory_integration(self):
        """测试工厂集成"""
        # 测试连接池工厂
        pool1 = ConnectionPoolFactory.create_connection_pool(max_connections=10)
        pool2 = ConnectionPoolFactory.get_global_connection_pool()
        
        # 验证工厂创建的连接池
        assert isinstance(pool1, HTTPConnectionPool)
        assert isinstance(pool2, HTTPConnectionPool)
        
        # 测试配置集成
        fallback_config = FallbackConfig(
            enabled=True,
            fallback_models=["model1", "model2"]
        )
        retry_config = RetryConfig(
            enabled=True,
            max_attempts=3
        )
        
        # 验证配置可以正常创建
        assert fallback_config.is_enabled() == True
        assert retry_config.is_enabled() == True
        assert len(fallback_config.get_fallback_models()) == 2
        assert retry_config.get_max_attempts() == 3