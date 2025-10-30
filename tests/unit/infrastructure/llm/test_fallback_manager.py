"""降级管理器单元测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage

from src.infrastructure.llm.fallback_system.fallback_manager import (
    FallbackManager,
    DefaultFallbackLogger
)
from src.infrastructure.llm.fallback_system.fallback_config import FallbackConfig
from src.infrastructure.llm.fallback_system.interfaces import IClientFactory, IFallbackLogger
from src.infrastructure.llm.models import LLMResponse
from src.infrastructure.llm.exceptions import LLMCallError


class MockClient:
    """模拟客户端"""
    
    def __init__(self, should_fail=False, fail_on_attempt=None, response_text="Test response"):
        self.should_fail = should_fail
        self.fail_on_attempt = fail_on_attempt
        self.response_text = response_text
        self.call_count = 0
    
    async def generate_async(self, messages, parameters=None, **kwargs):
        """异步生成方法"""
        self.call_count += 1
        
        if self.should_fail:
            if self.fail_on_attempt is None or self.call_count >= self.fail_on_attempt:
                raise LLMCallError(f"模拟失败 - 尝试 {self.call_count}")
        
        return LLMResponse(
            content=self.response_text,
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )


class MockClientFactory(IClientFactory):
    """模拟客户端工厂"""
    
    def __init__(self):
        self.clients = {}
        self.available_models = ["model1", "model2", "model3"]
    
    def create_client(self, model_name: str):
        """创建客户端"""
        if model_name not in self.clients:
            # 默认成功客户端
            self.clients[model_name] = MockClient()
        return self.clients[model_name]
    
    def get_available_models(self):
        """获取可用模型列表"""
        return self.available_models.copy()


class TestDefaultFallbackLogger:
    """默认降级日志记录器测试"""
    
    def test_log_fallback_attempt_enabled(self):
        """测试启用时记录降级尝试"""
        logger = DefaultFallbackLogger(enabled=True)
        
        with patch('builtins.print') as mock_print:
            logger.log_fallback_attempt("model1", "model2", Exception("test error"), 1)
            
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[Fallback]" in call_args
            assert "model1" in call_args
            assert "model2" in call_args
            assert "test error" in call_args
    
    def test_log_fallback_attempt_disabled(self):
        """测试禁用时不记录降级尝试"""
        logger = DefaultFallbackLogger(enabled=False)
        
        with patch('builtins.print') as mock_print:
            logger.log_fallback_attempt("model1", "model2", Exception("test error"), 1)
            
            mock_print.assert_not_called()
    
    def test_log_fallback_success_enabled(self):
        """测试启用时记录降级成功"""
        logger = DefaultFallbackLogger(enabled=True)
        response = LLMResponse(content="test", model="model2")
        
        with patch('builtins.print') as mock_print:
            logger.log_fallback_success("model1", "model2", response, 2)
            
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[Fallback]" in call_args
            assert "成功" in call_args
            assert "model1" in call_args
            assert "model2" in call_args
    
    def test_log_fallback_failure_enabled(self):
        """测试启用时记录降级失败"""
        logger = DefaultFallbackLogger(enabled=True)
        
        with patch('builtins.print') as mock_print:
            logger.log_fallback_failure("model1", Exception("test error"), 3)
            
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[Fallback]" in call_args
            assert "失败" in call_args
            assert "model1" in call_args
            assert "test error" in call_args
    
    def test_session_management(self):
        """测试会话管理"""
        logger = DefaultFallbackLogger(enabled=True)
        
        from src.infrastructure.llm.fallback_system.fallback_config import FallbackSession
        
        session1 = FallbackSession(primary_model="model1", start_time=123.0)
        session2 = FallbackSession(primary_model="model2", start_time=124.0)
        
        # 添加会话
        logger.add_session(session1)
        logger.add_session(session2)
        
        sessions = logger.get_sessions()
        assert len(sessions) == 2
        assert sessions[0] == session1
        assert sessions[1] == session2
        
        # 清空会话
        logger.clear_sessions()
        sessions = logger.get_sessions()
        assert len(sessions) == 0


class TestFallbackManager:
    """降级管理器测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return FallbackConfig(
            enabled=True,
            max_attempts=3,
            fallback_models=["model2", "model3"],
            strategy_type="sequential"
        )
    
    @pytest.fixture
    def client_factory(self):
        """创建客户端工厂"""
        return MockClientFactory()
    
    @pytest.fixture
    def manager(self, config, client_factory):
        """创建降级管理器"""
        return FallbackManager(config, client_factory)
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_success_on_first_attempt(self, manager):
        """测试第一次尝试成功"""
        messages = [HumanMessage(content="test")]
        
        response = await manager.generate_with_fallback(messages, primary_model="model1")
        
        assert response.content == "Test response"
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == True
        assert manager._sessions[0].get_total_attempts() == 1
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_success_on_fallback(self, manager, client_factory):
        """测试降级成功"""
        # 设置主模型失败，降级模型成功
        client_factory.clients["model1"] = MockClient(should_fail=True)
        
        messages = [HumanMessage(content="test")]
        
        response = await manager.generate_with_fallback(messages, primary_model="model1")
        
        assert response.content == "Test response"
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == True
        assert manager._sessions[0].get_total_attempts() == 2
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_all_attempts_fail(self, manager, client_factory):
        """测试所有尝试都失败"""
        # 设置所有模型都失败
        for model in ["model1", "model2", "model3"]:
            client_factory.clients[model] = MockClient(should_fail=True)
        
        messages = [HumanMessage(content="test")]
        
        with pytest.raises(LLMCallError):
            await manager.generate_with_fallback(messages, primary_model="model1")
        
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == False
        assert manager._sessions[0].get_total_attempts() == 3
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_disabled(self, config, client_factory):
        """测试降级禁用时直接使用主模型"""
        config.enabled = False
        manager = FallbackManager(config, client_factory)
        
        messages = [HumanMessage(content="test")]
        
        response = await manager.generate_with_fallback(messages, primary_model="model1")
        
        assert response.content == "Test response"
        assert len(manager._sessions) == 1  # 仍然记录会话
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_sync(self, manager):
        """测试同步生成方法"""
        messages = [HumanMessage(content="test")]
        
        response = manager.generate_with_fallback_sync(messages, primary_model="model1")
        
        assert response.content == "Test response"
        assert len(manager._sessions) == 1
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_async_alias(self, manager):
        """测试异步生成方法别名"""
        messages = [HumanMessage(content="test")]
        
        response = await manager.generate_with_fallback_async(messages, primary_model="model1")
        
        assert response.content == "Test response"
        assert len(manager._sessions) == 1
    
    def test_get_stats(self, manager):
        """测试获取统计信息"""
        # 模拟一些会话
        from src.infrastructure.llm.fallback_system.fallback_config import FallbackSession
        
        # 成功会话
        success_session = FallbackSession(primary_model="model1", start_time=123.0)
        success_session.mark_success(LLMResponse(content="success", model="model1"))
        manager._sessions.append(success_session)
        
        # 失败会话
        fail_session = FallbackSession(primary_model="model2", start_time=124.0)
        fail_session.mark_failure(Exception("failed"))
        manager._sessions.append(fail_session)
        
        stats = manager.get_stats()
        
        assert stats["total_sessions"] == 2
        assert stats["successful_sessions"] == 1
        assert stats["failed_sessions"] == 1
        assert stats["success_rate"] == 0.5
        assert "config" in stats
    
    def test_get_sessions(self, manager):
        """测试获取会话记录"""
        from src.infrastructure.llm.fallback_system.fallback_config import FallbackSession
        
        # 添加多个会话
        for i in range(5):
            session = FallbackSession(primary_model=f"model{i}", start_time=123.0 + i)
            manager._sessions.append(session)
        
        # 获取所有会话
        all_sessions = manager.get_sessions()
        assert len(all_sessions) == 5
        
        # 获取限制数量的会话
        limited_sessions = manager.get_sessions(limit=3)
        assert len(limited_sessions) == 3
        # 应该是最后3个会话
        assert limited_sessions[0].primary_model == "model2"
        assert limited_sessions[2].primary_model == "model4"
    
    def test_clear_sessions(self, manager):
        """测试清空会话记录"""
        from src.infrastructure.llm.fallback_system.fallback_config import FallbackSession
        
        # 添加会话
        session = FallbackSession(primary_model="model1", start_time=123.0)
        manager._sessions.append(session)
        
        assert len(manager._sessions) == 1
        
        # 清空会话
        manager.clear_sessions()
        assert len(manager._sessions) == 0
    
    def test_is_enabled(self, manager):
        """测试检查是否启用"""
        assert manager.is_enabled() == True
        
        manager.config.enabled = False
        assert manager.is_enabled() == False
    
    def test_get_available_models(self, manager, client_factory):
        """测试获取可用模型"""
        models = manager.get_available_models()
        assert models == client_factory.available_models
    
    def test_update_config(self, manager):
        """测试更新配置"""
        new_config = FallbackConfig(
            enabled=False,
            max_attempts=5,
            fallback_models=["model4", "model5"],
            strategy_type="random"
        )
        
        manager.update_config(new_config)
        
        assert manager.config == new_config
        assert manager.is_enabled() == False
    
    @pytest.mark.asyncio
    async def test_delay_between_attempts(self, manager, client_factory):
        """测试尝试之间的延迟"""
        # 设置主模型失败，降级模型成功
        client_factory.clients["model1"] = MockClient(should_fail=True)
        
        messages = [HumanMessage(content="test")]
        
        start_time = asyncio.get_event_loop().time()
        await manager.generate_with_fallback(messages, primary_model="model1")
        end_time = asyncio.get_event_loop().time()
        
        # 应该有延迟（至少1秒，因为base_delay=1.0）
        elapsed = end_time - start_time
        assert elapsed >= 1.0
    
    @pytest.mark.asyncio
    async def test_custom_logger(self, config, client_factory):
        """测试自定义日志记录器"""
        custom_logger = MagicMock(spec=IFallbackLogger)
        manager = FallbackManager(config, client_factory, custom_logger)
        
        # 设置主模型失败以触发降级
        client_factory.clients["model1"] = MockClient(should_fail=True)
        
        messages = [HumanMessage(content="test")]
        await manager.generate_with_fallback(messages, primary_model="model1")
        
        # 验证日志记录器被调用
        assert custom_logger.log_fallback_success.called