"""降级系统测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from langchain_core.messages import BaseMessage

from src.services.llm.fallback_system import (
    FallbackManager,
    FallbackExecutor,
    FallbackOrchestrator,
    FallbackStatistics,
    FallbackSessionManager,
    FallbackStrategyManager,
    FallbackConfigurationManager,
    LoggerAdapter,
    FallbackConfig,
    FallbackSession,
    FallbackAttempt
)
from src.services.llm.fallback_system.interfaces import IClientFactory, IFallbackLogger
from src.core.llm.models import LLMResponse
from core.common.exceptions.llm import LLMCallError
from src.core.llm.wrappers.fallback_manager import DefaultFallbackLogger


class TestFallbackConfigurationManager:
    """测试降级配置管理器"""
    
    def test_init(self):
        """测试初始化"""
        config = FallbackConfig(enabled=True, max_attempts=3, fallback_models=["model1", "model2"])
        manager = FallbackConfigurationManager(config)
        
        assert manager.is_enabled() == True
        assert manager.get_max_attempts() == 3
        assert manager.get_fallback_models() == ["model1", "model2"]
    
    def test_update_config(self):
        """测试更新配置"""
        config1 = FallbackConfig(enabled=True, max_attempts=3)
        manager = FallbackConfigurationManager(config1)
        
        config2 = FallbackConfig(enabled=False, max_attempts=5)
        manager.update_config(config2)
        
        assert manager.is_enabled() == False
        assert manager.get_max_attempts() == 5
    
    def test_get_config_summary(self):
        """测试获取配置摘要"""
        config = FallbackConfig(enabled=True, max_attempts=3, fallback_models=["model1"])
        manager = FallbackConfigurationManager(config)
        
        summary = manager.get_config_summary()
        assert summary["enabled"] == True
        assert summary["max_attempts"] == 3
        assert summary["fallback_models_count"] == 1


class TestFallbackSessionManager:
    """测试降级会话管理器"""
    
    def test_add_session(self):
        """测试添加会话"""
        manager = FallbackSessionManager()
        session = FallbackSession(primary_model="model1", start_time=123456789)
        
        manager.add_session(session)
        
        assert manager.get_session_count() == 1
        assert len(manager.get_sessions()) == 1
    
    def test_get_successful_sessions(self):
        """测试获取成功会话"""
        manager = FallbackSessionManager()
        
        # 创建成功会话
        success_session = FallbackSession(primary_model="model1", start_time=123456789)
        success_session.mark_success(LLMResponse(content="success"))
        manager.add_session(success_session)
        
        # 创建失败会话
        fail_session = FallbackSession(primary_model="model2", start_time=123456789)
        fail_session.mark_failure(Exception("error"))
        manager.add_session(fail_session)
        
        successful_sessions = manager.get_successful_sessions()
        assert len(successful_sessions) == 1
        assert successful_sessions[0].success == True
    
    def test_clear_sessions(self):
        """测试清空会话"""
        manager = FallbackSessionManager()
        session = FallbackSession(primary_model="model1", start_time=123456789)
        manager.add_session(session)
        
        assert manager.get_session_count() == 1
        
        manager.clear_sessions()
        
        assert manager.get_session_count() == 0


class TestFallbackStatistics:
    """测试降级统计管理器"""
    
    def test_update_core_stats(self):
        """测试更新 Core 层统计"""
        stats = FallbackStatistics()
        
        # 创建测试会话
        session1 = FallbackSession(primary_model="model1", start_time=123456789)
        session1.mark_success(LLMResponse(content="success"))
        
        session2 = FallbackSession(primary_model="model2", start_time=123456789)
        session2.mark_failure(Exception("error"))
        
        stats.update_core_stats([session1, session2])
        
        core_stats = stats.get_core_stats()
        assert core_stats["total_sessions"] == 2
        assert core_stats["successful_sessions"] == 1
        assert core_stats["failed_sessions"] == 1
    
    def test_increment_services_stats(self):
        """测试增加 Services 层统计"""
        stats = FallbackStatistics()
        
        stats.increment_total_requests()
        stats.increment_successful_requests()
        stats.increment_group_fallbacks()
        
        services_stats = stats.get_services_stats()
        assert services_stats["total_requests"] == 1
        assert services_stats["successful_requests"] == 1
        assert services_stats["group_fallbacks"] == 1
    
    def test_reset_stats(self):
        """测试重置统计"""
        stats = FallbackStatistics()
        stats.increment_total_requests()
        
        assert stats.get_stats()["total_requests"] == 1
        
        stats.reset_stats()
        
        assert stats.get_stats()["total_requests"] == 0


class TestFallbackStrategyManager:
    """测试降级策略管理器"""
    
    def test_init(self):
        """测试初始化"""
        config = FallbackConfig(enabled=True)
        manager = FallbackStrategyManager(config)
        
        assert manager.config == config
        assert manager._strategies_initialized == False
    
    def test_initialize_strategies(self):
        """测试初始化策略"""
        config = FallbackConfig(enabled=True)
        manager = FallbackStrategyManager(config)
        
        # 初始化前
        assert manager._strategy is None
        
        # 获取策略会触发初始化
        strategy = manager.get_core_strategy()
        
        # 初始化后
        assert manager._strategies_initialized == True
        assert strategy is not None
    
    def test_update_config(self):
        """测试更新配置"""
        config1 = FallbackConfig(enabled=True)
        manager = FallbackStrategyManager(config1)
        
        config2 = FallbackConfig(enabled=False)
        manager.update_config(config2)
        
        assert manager.config == config2
        assert manager._strategies_initialized == False


class TestLoggerAdapter:
    """测试日志记录器适配器"""
    
    def test_adapter(self):
        """测试适配器功能"""
        core_logger = DefaultFallbackLogger()
        adapter = LoggerAdapter(core_logger)
        
        # 测试适配器实现了 IFallbackLogger 接口
        assert hasattr(adapter, 'log_fallback_attempt')
        assert hasattr(adapter, 'log_fallback_success')
        assert hasattr(adapter, 'log_fallback_failure')
        
        # 测试方法调用不会抛出异常
        adapter.log_fallback_attempt("model1", "model2", Exception("test"), 1)
        adapter.log_fallback_success("model1", "model2", LLMResponse(content="test"), 1)
        adapter.log_fallback_failure("model1", Exception("test"), 1)


class TestFallbackManager:
    """测试降级管理器"""
    
    def test_init(self):
        """测试初始化"""
        config = FallbackConfig(enabled=True)
        manager = FallbackManager(config=config)
        
        assert manager.is_enabled() == True
        assert manager._config_manager is not None
        assert manager._session_manager is not None
        assert manager._statistics is not None
        assert manager._strategy_manager is not None
        assert manager._executor is not None
        assert manager._orchestrator is not None
    
    def test_get_stats(self):
        """测试获取统计信息"""
        config = FallbackConfig(enabled=True)
        manager = FallbackManager(config=config)
        
        stats = manager.get_stats()
        assert isinstance(stats, dict)
        assert "total_sessions" in stats
        assert "total_requests" in stats
    
    def test_get_sessions(self):
        """测试获取会话"""
        config = FallbackConfig(enabled=True)
        manager = FallbackManager(config=config)
        
        sessions = manager.get_sessions()
        assert isinstance(sessions, list)
    
    def test_clear_sessions(self):
        """测试清空会话"""
        config = FallbackConfig(enabled=True)
        manager = FallbackManager(config=config)
        
        # 清空会话不会抛出异常
        manager.clear_sessions()
        
        # 统计信息应该被重置
        stats = manager.get_stats()
        assert stats["total_sessions"] == 0
    
    def test_update_config(self):
        """测试更新配置"""
        config1 = FallbackConfig(enabled=True)
        manager = FallbackManager(config=config1)
        
        config2 = FallbackConfig(enabled=False)
        manager.update_config(config2)
        
        assert manager.is_enabled() == False
    
    def test_get_config_summary(self):
        """测试获取配置摘要"""
        config = FallbackConfig(enabled=True, max_attempts=3)
        manager = FallbackManager(config=config)
        
        summary = manager.get_config_summary()
        assert summary["enabled"] == True
        assert summary["max_attempts"] == 3
    
    def test_export_import_config(self):
        """测试导出导入配置"""
        config1 = FallbackConfig(enabled=True, max_attempts=3, fallback_models=["model1"])
        manager = FallbackManager(config=config1)
        
        # 导出配置
        exported_config = manager.export_config()
        assert exported_config["enabled"] == True
        assert exported_config["max_attempts"] == 3
        assert exported_config["fallback_models"] == ["model1"]
        
        # 导入配置
        config2_dict = {"enabled": False, "max_attempts": 5, "fallback_models": ["model2"]}
        manager.import_config(config2_dict)
        
        assert manager.is_enabled() == False
        assert manager.get_config_summary()["max_attempts"] == 5


@pytest.mark.asyncio
class TestFallbackManagerAsync:
    """测试降级管理器异步方法"""
    
    async def test_generate_with_fallback_disabled(self):
        """测试降级未启用时的生成"""
        config = FallbackConfig(enabled=False)
        
        # 创建模拟客户端工厂
        mock_client = AsyncMock()
        mock_client.generate_async.return_value = LLMResponse(content="test response")
        
        mock_factory = Mock(spec=IClientFactory)
        mock_factory.create_client.return_value = mock_client
        
        manager = FallbackManager(config=config, client_factory=mock_factory)
        
        messages = [BaseMessage(content="test")]
        response = await manager.generate_with_fallback(messages, primary_model="model1")
        
        assert response.content == "test response"
        assert manager.get_session_count() == 1
    
    async def test_execute_with_fallback(self):
        """测试执行带降级的请求"""
        config = FallbackConfig(enabled=True)
        
        # 创建模拟任务组管理器
        mock_task_group_manager = Mock()
        mock_task_group_manager.get_models_for_group.return_value = ["model1"]
        
        # 创建模拟客户端
        mock_client = AsyncMock()
        mock_client.generate_async.return_value = LLMResponse(content="test response")
        
        # 创建模拟客户端工厂
        mock_factory = Mock(spec=IClientFactory)
        mock_factory.create_client.return_value = mock_client
        
        manager = FallbackManager(
            config=config, 
            client_factory=mock_factory,
            task_group_manager=mock_task_group_manager
        )
        
        result = await manager.execute_with_fallback(
            primary_target="group1",
            fallback_groups=["group2"],
            prompt="test prompt"
        )
        
        assert result.content == "test response"
        
        # 检查统计信息
        stats = manager.get_services_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1


if __name__ == "__main__":
    pytest.main([__file__])