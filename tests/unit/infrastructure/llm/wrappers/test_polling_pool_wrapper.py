"""PollingPoolWrapper单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Sequence
import time
from datetime import datetime

from src.infrastructure.llm.wrappers.polling_pool_wrapper import PollingPoolWrapper
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.exceptions import LLMError
from src.infrastructure.llm.wrappers.exceptions import PollingPoolWrapperError


class TestPollingPoolWrapper:
    """PollingPoolWrapper测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        mock_pool_manager = Mock()
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager, {"param": "value"})
        
        assert wrapper.name == "test-wrapper"
        assert wrapper.config == {"param": "value"}
        assert wrapper.polling_pool_manager == mock_pool_manager
        assert wrapper._pool is None
        assert wrapper._attempt_count == 0
        assert wrapper._rotation_history == []
        assert wrapper._metadata["polling_pool_manager"] is True
        assert wrapper._metadata["wrapper_type"] == "polling_pool"
    
    def test_initialization_with_none_config(self):
        """测试用None配置初始化"""
        mock_pool_manager = Mock()
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager, None)
        
        assert wrapper.config == {}
    
    @pytest.mark.asyncio
    async def test_generate_async_success(self):
        """测试异步生成成功"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool_manager.get_pool.return_value = mock_pool
        mock_pool.name = "test-pool"
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        wrapper._get_pool = Mock(return_value=mock_pool)
        wrapper._call_with_simple_fallback = AsyncMock(return_value="test response")
        
        messages = [Mock(content="Hello")]
        result = await wrapper.generate_async(messages)
        
        assert isinstance(result, LLMResponse)
        assert result.content == "test response"
        assert result.model == "test-pool_pool"
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["successful_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_async_pool_unavailable(self):
        """测试异步生成时轮询池不可用"""
        mock_pool_manager = Mock()
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        wrapper._get_pool = Mock(return_value=None)
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(PollingPoolWrapperError, match="轮询池不可用"):
            await wrapper.generate_async(messages)
        
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["failed_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_async_exception(self):
        """测试异步生成时发生异常"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool_manager.get_pool.return_value = mock_pool
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        wrapper._get_pool = Mock(return_value=mock_pool)
        wrapper._call_with_simple_fallback = AsyncMock(side_effect=Exception("Test error"))
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(PollingPoolWrapperError, match="轮询池包装器生成失败"):
            await wrapper.generate_async(messages)
        
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["failed_requests"] == 1
    
    def test_generate_sync_success(self):
        """测试同步生成成功"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool_manager.get_pool.return_value = mock_pool
        mock_pool.name = "test-pool"
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        wrapper._get_pool = Mock(return_value=mock_pool)
        wrapper._call_with_simple_fallback = AsyncMock(return_value="test response")
        
        messages = [Mock(content="Hello")]
        result = wrapper.generate(messages)
        
        assert isinstance(result, LLMResponse)
        assert result.content == "test response"
        assert result.model == "test-pool_pool"
    
    def test_generate_sync_exception(self):
        """测试同步生成时发生异常"""
        mock_pool_manager = Mock()
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        wrapper._get_pool = Mock(return_value=None)
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(PollingPoolWrapperError, match="轮询池包装器同步生成失败"):
            wrapper.generate(messages)
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool.name = "test-pool"
        mock_pool.config = {
            "task_groups": ["group1", "group2"],
            "rotation_strategy": "round_robin",
            "health_check_interval": 30,
            "failure_threshold": 3,
            "recovery_time": 60
        }
        mock_pool.instances = [
            Mock(status=Mock(value="healthy")),
            Mock(status=Mock(value="unhealthy")),
            Mock(status=Mock(value="healthy"))
        ]
        mock_pool_manager.get_pool.return_value = mock_pool
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        info = wrapper.get_model_info()
        
        assert info["type"] == "polling_pool_wrapper"
        assert info["name"] == "test-wrapper"
        assert info["pool_info"]["name"] == "test-pool"
        assert info["pool_info"]["task_groups"] == ["group1", "group2"]
        assert info["pool_info"]["instance_count"] == 3
        assert info["pool_info"]["healthy_instances"] == 2
        assert info["attempt_count"] == 0
        assert info["rotation_history"] == []
    
    def test_get_model_info_no_pool(self):
        """测试获取模型信息（无池）"""
        mock_pool_manager = Mock()
        mock_pool_manager.get_pool.return_value = None
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        info = wrapper.get_model_info()
        
        assert info["pool_info"] == {}
    
    def test_get_pool(self):
        """测试获取轮询池"""
        mock_pool_manager = Mock()
        expected_pool = Mock()
        mock_pool_manager.get_pool.return_value = expected_pool
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        # 第一次调用应该从管理器获取
        pool1 = wrapper._get_pool()
        assert pool1 == expected_pool
        assert wrapper._pool == expected_pool
        mock_pool_manager.get_pool.assert_called_once_with("test-wrapper")
        
        # 第二次调用应该返回缓存的池
        mock_pool_manager.get_pool.reset_mock()
        pool2 = wrapper._get_pool()
        assert pool2 == expected_pool
        assert wrapper._pool == expected_pool
        mock_pool_manager.get_pool.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_call_with_simple_fallback_success(self):
        """测试简单降级策略调用成功"""
        mock_pool = Mock()
        mock_instance = Mock()
        mock_instance.instance_id = "instance-1"
        mock_instance.success_count = 0
        mock_instance.failure_count = 0
        
        mock_pool.get_instance = AsyncMock(return_value=mock_instance)
        mock_pool.release_instance = Mock()
        
        wrapper = PollingPoolWrapper("test-wrapper", Mock())
        wrapper._call_instance = AsyncMock(return_value="instance response")
        
        result = await wrapper._call_with_simple_fallback(
            mock_pool, "test prompt", {"param": "value"}
        )
        
        assert result == "instance response"
        assert wrapper._attempt_count == 1
        assert len(wrapper._rotation_history) == 1
        assert wrapper._rotation_history[0]["instance_id"] == "instance-1"
        assert mock_instance.success_count == 1
        mock_pool.release_instance.assert_called_once_with(mock_instance)
    
    @pytest.mark.asyncio
    async def test_call_with_simple_fallback_multiple_attempts(self):
        """测试简单降级策略调用多次尝试"""
        mock_pool = Mock()
        mock_instance1 = Mock()
        mock_instance1.instance_id = "instance-1"
        mock_instance1.failure_count = 0
        
        mock_instance2 = Mock()
        mock_instance2.instance_id = "instance-2"
        mock_instance2.failure_count = 0
        
        mock_pool.get_instance = AsyncMock(side_effect=[mock_instance1, mock_instance2])
        mock_pool.release_instance = Mock()
        
        wrapper = PollingPoolWrapper("test-wrapper", Mock(), {"max_instance_attempts": 2})
        wrapper._call_instance = AsyncMock(side_effect=[Exception("First failure"), "second response"])
        
        result = await wrapper._call_with_simple_fallback(
            mock_pool, "test prompt", {"param": "value"}
        )
        
        assert result == "second response"
        assert wrapper._attempt_count == 2
        assert len(wrapper._rotation_history) == 2
        assert mock_instance1.failure_count == 1
        assert mock_instance2.failure_count == 0
        assert mock_pool.release_instance.call_count == 2
    
    @pytest.mark.asyncio
    async def test_call_with_simple_fallback_all_failures(self):
        """测试简单降级策略所有尝试都失败"""
        mock_pool = Mock()
        mock_instance = Mock()
        mock_instance.instance_id = "instance-1"
        mock_instance.failure_count = 0
        
        mock_pool.get_instance = AsyncMock(return_value=mock_instance)
        mock_pool.release_instance = Mock()
        
        wrapper = PollingPoolWrapper("test-wrapper", Mock(), {"max_instance_attempts": 2})
        wrapper._call_instance = AsyncMock(side_effect=Exception("Instance failure"))
        
        with pytest.raises(PollingPoolWrapperError, match="轮询池所有实例尝试失败"):
            await wrapper._call_with_simple_fallback(
                mock_pool, "test prompt", {"param": "value"}
            )
        
        assert wrapper._attempt_count == 2
        assert len(wrapper._rotation_history) == 2
        assert mock_instance.failure_count == 2
        assert mock_pool.release_instance.call_count == 2
    
    @pytest.mark.asyncio
    async def test_call_instance(self):
        """测试调用具体实例"""
        wrapper = PollingPoolWrapper("test-wrapper", Mock())
        
        mock_instance = Mock()
        mock_instance.instance_id = "test-instance"
        
        result = await wrapper._call_instance(
            mock_instance, "test prompt", {"param": "value"}
        )
        
        assert "轮询池响应 from test-instance" in result
        assert "test prompt" in result
    
    def test_create_llm_response(self):
        """测试创建LLM响应"""
        wrapper = PollingPoolWrapper("test-wrapper", Mock())
        
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
        assert response.metadata["wrapper"] == "polling_pool"
        assert response.metadata["attempt_count"] == 0
        assert response.metadata["rotation_history_count"] == 0
    
    def test_create_llm_response_with_defaults(self):
        """测试创建LLM响应（使用默认值）"""
        wrapper = PollingPoolWrapper("test-wrapper", Mock())
        
        response = wrapper._create_llm_response(
            content="Test content",
            model="test-model"
        )
        
        assert response.content == "Test content"
        assert response.model == "test-model"
        assert response.token_usage.prompt_tokens > 0
        assert response.token_usage.completion_tokens > 0
        assert response.token_usage.total_tokens > 0
        assert response.metadata["wrapper"] == "polling_pool"
    
    def test_get_rotation_history(self):
        """测试获取旋转历史"""
        wrapper = PollingPoolWrapper("test-wrapper", Mock())
        
        # 添加一些历史记录
        wrapper._rotation_history = [
            {"instance_id": f"instance-{i}", "attempt": i, "timestamp": "time"}
            for i in range(15)  # 创建15个记录
        ]
        
        history = wrapper.get_rotation_history(limit=10)
        
        assert len(history) == 10
        # 检查是最近的10条记录
        assert history[0]["instance_id"] == "instance-5"  # 最旧的
        assert history[-1]["instance_id"] == "instance-14"  # 最新的
    
    def test_reset_rotation_history(self):
        """测试重置旋转历史"""
        wrapper = PollingPoolWrapper("test-wrapper", Mock())
        
        wrapper._rotation_history = [{"instance_id": "test", "attempt": 1, "timestamp": "time"}]
        wrapper._attempt_count = 5
        
        wrapper.reset_rotation_history()
        
        assert wrapper._rotation_history == []
        assert wrapper._attempt_count == 0
    
    def test_get_pool_status(self):
        """测试获取轮询池状态"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool.get_status = Mock(return_value={"status": "healthy"})
        mock_pool_manager.get_pool.return_value = mock_pool
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        status = wrapper.get_pool_status()
        
        assert status == {"status": "healthy"}
        mock_pool.get_status.assert_called_once()
    
    def test_get_pool_status_no_pool(self):
        """测试获取轮询池状态（无池）"""
        mock_pool_manager = Mock()
        mock_pool_manager.get_pool.return_value = None
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        status = wrapper.get_pool_status()
        
        assert status is None
    
    def test_supports_function_calling(self):
        """测试函数调用支持"""
        wrapper = PollingPoolWrapper("test-wrapper", Mock())
        
        # 轮询池包装器默认不支持函数调用
        assert wrapper.supports_function_calling() is False
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """测试健康检查（健康）"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool.instances = [
            Mock(status=Mock(value="healthy")),
            Mock(status=Mock(value="healthy")),
            Mock(status=Mock(value="healthy"))
        ]
        mock_pool_manager.get_pool.return_value = mock_pool
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        health = await wrapper.health_check()
        
        assert health["healthy"] is True
        assert health["healthy_instances"] == 3
        assert health["total_instances"] == 3
        assert health["health_ratio"] == 1.0
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """测试健康检查（不健康）"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool.instances = [
            Mock(status=Mock(value="healthy")),
            Mock(status=Mock(value="unhealthy")),
            Mock(status=Mock(value="unhealthy"))
        ]
        mock_pool_manager.get_pool.return_value = mock_pool
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        health = await wrapper.health_check()
        
        assert health["healthy"] is False
        assert health["healthy_instances"] == 1
        assert health["total_instances"] == 3
        assert health["health_ratio"] == 1/3
    
    @pytest.mark.asyncio
    async def test_health_check_no_pool(self):
        """测试健康检查（无池）"""
        mock_pool_manager = Mock()
        mock_pool_manager.get_pool.return_value = None
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        health = await wrapper.health_check()
        
        assert health["healthy"] is False
        assert health["error"] == "轮询池不可用"
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self):
        """测试健康检查（异常）"""
        mock_pool_manager = Mock()
        mock_pool = Mock()
        mock_pool.instances = Mock(side_effect=Exception("Pool error"))
        mock_pool_manager.get_pool.return_value = mock_pool
        
        wrapper = PollingPoolWrapper("test-wrapper", mock_pool_manager)
        
        health = await wrapper.health_check()
        
        assert health["healthy"] is False
        assert health["error"] == "Pool error"