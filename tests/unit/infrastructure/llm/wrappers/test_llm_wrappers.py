"""LLM包装器单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.infrastructure.llm.wrappers import (
    BaseLLMWrapper, TaskGroupWrapper, PollingPoolWrapper, LLMWrapperFactory
)
from src.infrastructure.llm.wrappers.exceptions import (
    TaskGroupWrapperError, PollingPoolWrapperError, WrapperFactoryError
)
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.enhanced_fallback_manager import EnhancedFallbackManager
from src.infrastructure.llm.polling_pool import PollingPoolManager, PollingPool
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.interfaces import ILLMClient
from langchain_core.messages import HumanMessage


class TestBaseLLMWrapper:
    """基础LLM包装器测试"""
    
    def test_init(self):
        """测试初始化"""
        mock_manager = Mock(spec=TaskGroupManager)
        wrapper = TaskGroupWrapper("test_wrapper", mock_manager, config={"key": "value"})
        assert wrapper.name == "test_wrapper"
        assert wrapper.config == {"key": "value"}
        assert wrapper._stats["total_requests"] == 0
    
    def test_get_token_count(self):
        """测试token计数"""
        mock_manager = Mock(spec=TaskGroupManager)
        wrapper = TaskGroupWrapper("test_wrapper", mock_manager)
        assert wrapper.get_token_count("hello world") == 2  # 简单估算
    
    def test_get_messages_token_count(self):
        """测试消息token计数"""
        mock_manager = Mock(spec=TaskGroupManager)
        wrapper = TaskGroupWrapper("test_wrapper", mock_manager)
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "hello world"
        
        messages = [mock_message]
        assert wrapper.get_messages_token_count(messages) == 2
    
    def test_messages_to_prompt(self):
        """测试消息转换为提示词"""
        mock_manager = Mock(spec=TaskGroupManager)
        wrapper = TaskGroupWrapper("test_wrapper", mock_manager)
        
        # 创建模拟消息
        mock_message1 = Mock()
        mock_message1.content = "Hello"
        mock_message2 = Mock()
        mock_message2.content = "World"
        
        messages = [mock_message1, mock_message2]
        prompt = wrapper._messages_to_prompt(messages)
        assert prompt == "Hello\nWorld"
    
    def test_create_llm_response(self):
        """测试创建LLM响应"""
        mock_manager = Mock(spec=TaskGroupManager)
        wrapper = TaskGroupWrapper("test_wrapper", mock_manager)
        
        response = wrapper._create_llm_response(
            content="Test response",
            model="test_model",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20),
            message=HumanMessage(content="Test message")
        )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "test_model"
        assert response.token_usage.prompt_tokens == 10
    
    def test_update_stats(self):
        """测试更新统计信息"""
        mock_manager = Mock(spec=TaskGroupManager)
        wrapper = TaskGroupWrapper("test_wrapper", mock_manager)
        
        wrapper._update_stats(True, 1.0)
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["successful_requests"] == 1
        assert wrapper._stats["avg_response_time"] == 1.0
        
        wrapper._update_stats(False, 2.0)
        assert wrapper._stats["total_requests"] == 2
        assert wrapper._stats["failed_requests"] == 1
        assert wrapper._stats["avg_response_time"] == 1.5
    
    def test_reset_stats(self):
        """测试重置统计信息"""
        mock_manager = Mock(spec=TaskGroupManager)
        wrapper = TaskGroupWrapper("test_wrapper", mock_manager)
        wrapper._update_stats(True, 1.0)
        
        wrapper.reset_stats()
        assert wrapper._stats["total_requests"] == 0
        assert wrapper._stats["successful_requests"] == 0


class TestTaskGroupWrapper:
    """任务组包装器测试"""
    
    @pytest.fixture
    def mock_task_group_manager(self):
        """模拟任务组管理器"""
        manager = Mock(spec=TaskGroupManager)
        manager.get_models_for_group.return_value = ["model1", "model2"]
        manager.parse_group_reference.return_value = ("test_group", "echelon1")
        manager.get_fallback_groups.return_value = ["test_group.echelon2"]
        return manager
    
    @pytest.fixture
    def mock_fallback_manager(self):
        """模拟降级管理器"""
        manager = Mock(spec=EnhancedFallbackManager)
        manager.execute_with_fallback = AsyncMock(return_value="fallback response")
        return manager
    
    def test_init(self, mock_task_group_manager, mock_fallback_manager):
        """测试初始化"""
        wrapper = TaskGroupWrapper(
            name="test_wrapper",
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        assert wrapper.name == "test_wrapper"
        assert wrapper.task_group_manager == mock_task_group_manager
        assert wrapper.fallback_manager == mock_fallback_manager
    
    @pytest.mark.asyncio
    async def test_generate_async_with_fallback(self, mock_task_group_manager, mock_fallback_manager):
        """测试使用降级的异步生成"""
        wrapper = TaskGroupWrapper(
            name="test_wrapper",
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager,
            config={"target": "test_group.echelon1"}
        )
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "Test message"
        messages = [mock_message]
        
        response = await wrapper.generate_async(messages)
        
        assert response.content == "fallback response"
        mock_fallback_manager.execute_with_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_async_direct(self, mock_task_group_manager):
        """测试直接异步生成（无降级）"""
        wrapper = TaskGroupWrapper(
            name="test_wrapper",
            task_group_manager=mock_task_group_manager,
            fallback_manager=None,
            config={"target": "test_group.echelon1"}
        )
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "Test message"
        messages = [mock_message]
        
        response = await wrapper.generate_async(messages)
        
        assert "模拟响应" in response.content
        assert "model1" in response.content
    
    def test_generate_sync(self, mock_task_group_manager, mock_fallback_manager):
        """测试同步生成"""
        wrapper = TaskGroupWrapper(
            name="test_wrapper",
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager,
            config={"target": "test_group.echelon1"}
        )
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "Test message"
        messages = [mock_message]
        
        with patch.object(wrapper, 'generate_async', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = LLMResponse(
                content="test response",
                message=HumanMessage(content="test response"),
                token_usage=TokenUsage(),
                model="test_model"
            )
            
            response = wrapper.generate(messages)
            assert response.content == "test response"
    
    def test_get_fallback_groups_from_config(self, mock_task_group_manager):
        """测试从配置获取降级组"""
        wrapper = TaskGroupWrapper(
            name="test_wrapper",
            task_group_manager=mock_task_group_manager,
            fallback_manager=None,
            config={
                "target": "test_group.echelon1",
                "fallback_groups": ["fallback1", "fallback2"]
            }
        )
        
        fallback_groups = wrapper._get_fallback_groups("test_group.echelon1")
        assert fallback_groups == ["fallback1", "fallback2"]
    
    def test_get_fallback_groups_from_manager(self, mock_task_group_manager):
        """测试从管理器获取降级组"""
        wrapper = TaskGroupWrapper(
            name="test_wrapper",
            task_group_manager=mock_task_group_manager,
            fallback_manager=None,
            config={"target": "test_group.echelon1"}
        )
        
        fallback_groups = wrapper._get_fallback_groups("test_group.echelon1")
        assert fallback_groups == ["test_group.echelon2"]
    
    def test_supports_function_calling(self, mock_task_group_manager):
        """测试函数调用支持检查"""
        # 模拟层级配置
        mock_echelon_config = Mock()
        mock_echelon_config.function_calling = "enabled"
        
        mock_task_group_manager.get_echelon_config.return_value = mock_echelon_config
        
        wrapper = TaskGroupWrapper(
            name="test_wrapper",
            task_group_manager=mock_task_group_manager,
            fallback_manager=None,
            config={"target": "test_group.echelon1"}
        )
        
        assert wrapper.supports_function_calling() == True


class TestPollingPoolWrapper:
    """轮询池包装器测试"""
    
    @pytest.fixture
    def mock_polling_pool_manager(self):
        """模拟轮询池管理器"""
        manager = Mock(spec=PollingPoolManager)
        return manager
    
    @pytest.fixture
    def mock_pool(self):
        """模拟轮询池"""
        pool = Mock(spec=PollingPool)
        pool.name = "test_pool"
        pool.config = {
            "task_groups": ["test_group"],
            "rotation_strategy": "round_robin",
            "health_check_interval": 30,
            "failure_threshold": 3,
            "recovery_time": 60
        }
        pool.instances = []
        pool.get_status.return_value = {"healthy": True}
        return pool
    
    def test_init(self, mock_polling_pool_manager):
        """测试初始化"""
        wrapper = PollingPoolWrapper(
            name="test_wrapper",
            polling_pool_manager=mock_polling_pool_manager
        )
        
        assert wrapper.name == "test_wrapper"
        assert wrapper.polling_pool_manager == mock_polling_pool_manager
    
    @pytest.mark.asyncio
    async def test_generate_async_success(self, mock_polling_pool_manager, mock_pool):
        """测试成功的异步生成"""
        mock_polling_pool_manager.get_pool.return_value = mock_pool
        
        # 模拟实例
        mock_instance = Mock()
        mock_instance.instance_id = "instance1"
        mock_pool.get_instance = AsyncMock(return_value=mock_instance)
        mock_pool.release_instance = Mock()
        
        wrapper = PollingPoolWrapper(
            name="test_wrapper",
            polling_pool_manager=mock_polling_pool_manager,
            config={"max_instance_attempts": 2}
        )
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "Test message"
        messages = [mock_message]
        
        response = await wrapper.generate_async(messages)
        
        assert "轮询池响应" in response.content
        assert "instance1" in response.content
    
    @pytest.mark.asyncio
    async def test_generate_async_pool_unavailable(self, mock_polling_pool_manager):
        """测试轮询池不可用的情况"""
        mock_polling_pool_manager.get_pool.return_value = None
        
        wrapper = PollingPoolWrapper(
            name="test_wrapper",
            polling_pool_manager=mock_polling_pool_manager
        )
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "Test message"
        messages = [mock_message]
        
        with pytest.raises(PollingPoolWrapperError):
            await wrapper.generate_async(messages)
    
    def test_get_pool_status(self, mock_polling_pool_manager, mock_pool):
        """测试获取轮询池状态"""
        mock_polling_pool_manager.get_pool.return_value = mock_pool
        
        wrapper = PollingPoolWrapper(
            name="test_wrapper",
            polling_pool_manager=mock_polling_pool_manager
        )
        
        status = wrapper.get_pool_status()
        assert status is not None
        assert status["healthy"] == True
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_polling_pool_manager, mock_pool):
        """测试健康检查"""
        mock_polling_pool_manager.get_pool.return_value = mock_pool
        
        # 模拟健康实例
        mock_instance1 = Mock()
        mock_instance1.status.value = "healthy"
        mock_instance2 = Mock()
        mock_instance2.status.value = "healthy"
        mock_pool.instances = [mock_instance1, mock_instance2]
        
        wrapper = PollingPoolWrapper(
            name="test_wrapper",
            polling_pool_manager=mock_polling_pool_manager
        )
        
        health = await wrapper.health_check()
        assert health["healthy"] == True
        assert health["healthy_instances"] == 2
        assert health["total_instances"] == 2


class TestLLMWrapperFactory:
    """LLM包装器工厂测试"""
    
    @pytest.fixture
    def mock_task_group_manager(self):
        """模拟任务组管理器"""
        return Mock(spec=TaskGroupManager)
    
    @pytest.fixture
    def mock_polling_pool_manager(self):
        """模拟轮询池管理器"""
        return Mock(spec=PollingPoolManager)
    
    @pytest.fixture
    def mock_fallback_manager(self):
        """模拟降级管理器"""
        return Mock(spec=EnhancedFallbackManager)
    
    def test_init(self, mock_task_group_manager, mock_polling_pool_manager, mock_fallback_manager):
        """测试初始化"""
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager,
            fallback_manager=mock_fallback_manager
        )
        
        assert factory.task_group_manager == mock_task_group_manager
        assert factory.polling_pool_manager == mock_polling_pool_manager
        assert factory.fallback_manager == mock_fallback_manager
    
    def test_create_task_group_wrapper(self, mock_task_group_manager, mock_fallback_manager):
        """测试创建任务组包装器"""
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        wrapper = factory.create_task_group_wrapper("test_wrapper", {"key": "value"})
        
        assert isinstance(wrapper, TaskGroupWrapper)
        assert wrapper.name == "test_wrapper"
        assert wrapper.config == {"key": "value"}
        assert "test_wrapper" in factory._wrappers
    
    def test_create_polling_pool_wrapper(self, mock_task_group_manager, mock_polling_pool_manager):
        """测试创建轮询池包装器"""
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager
        )
        
        wrapper = factory.create_polling_pool_wrapper("test_wrapper", {"key": "value"})
        
        assert isinstance(wrapper, PollingPoolWrapper)
        assert wrapper.name == "test_wrapper"
        assert wrapper.config == {"key": "value"}
        assert "test_wrapper" in factory._wrappers
    
    def test_create_polling_pool_wrapper_no_manager(self, mock_task_group_manager):
        """测试没有轮询池管理器时创建轮询池包装器"""
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        with pytest.raises(WrapperFactoryError):
            factory.create_polling_pool_wrapper("test_wrapper")
    
    def test_get_wrapper(self, mock_task_group_manager, mock_fallback_manager):
        """测试获取包装器"""
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        # 创建包装器
        wrapper = factory.create_task_group_wrapper("test_wrapper")
        
        # 获取包装器
        retrieved_wrapper = factory.get_wrapper("test_wrapper")
        assert retrieved_wrapper == wrapper
        
        # 获取不存在的包装器
        non_existent = factory.get_wrapper("non_existent")
        assert non_existent is None
    
    def test_remove_wrapper(self, mock_task_group_manager, mock_fallback_manager):
        """测试移除包装器"""
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        # 创建包装器
        wrapper = factory.create_task_group_wrapper("test_wrapper")
        
        # 移除包装器
        result = factory.remove_wrapper("test_wrapper")
        assert result == True
        assert "test_wrapper" not in factory._wrappers
        
        # 移除不存在的包装器
        result = factory.remove_wrapper("non_existent")
        assert result == False
    
    def test_list_wrappers(self, mock_task_group_manager, mock_fallback_manager):
        """测试列出包装器"""
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        # 创建不同类型的包装器
        factory.create_task_group_wrapper("task_wrapper")
        factory.create_polling_pool_wrapper("pool_wrapper")
        
        wrappers = factory.list_wrappers()
        assert wrappers["task_wrapper"] == "TaskGroupWrapper"
        assert wrappers["pool_wrapper"] == "PollingPoolWrapper"
    
    def test_get_wrapper_stats(self, mock_task_group_manager, mock_fallback_manager):
        """测试获取包装器统计信息"""
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        # 创建包装器
        factory.create_task_group_wrapper("test_wrapper")
        
        stats = factory.get_wrapper_stats()
        assert stats["total_wrappers"] == 1
        assert "TaskGroupWrapper" in stats["wrapper_types"]
        assert "test_wrapper" in stats["wrapper_stats"]