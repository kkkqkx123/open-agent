"""TaskGroupWrapper单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Sequence
import time
from datetime import datetime

from src.infrastructure.llm.wrappers.task_group_wrapper import TaskGroupWrapper
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.exceptions import LLMError
from src.infrastructure.llm.wrappers.exceptions import TaskGroupWrapperError


class TestTaskGroupWrapper:
    """TaskGroupWrapper测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper(
            "test-wrapper", 
            mock_task_group_manager, 
            mock_fallback_manager, 
            {"param": "value"}
        )
        
        assert wrapper.name == "test-wrapper"
        assert wrapper.config == {"param": "value"}
        assert wrapper.task_group_manager == mock_task_group_manager
        assert wrapper.fallback_manager == mock_fallback_manager
        assert wrapper._current_target is None
        assert wrapper._attempt_count == 0
        assert wrapper._fallback_history == []
        assert wrapper._metadata["task_group_manager"] is True
        assert wrapper._metadata["fallback_manager"] is True
        assert wrapper._metadata["wrapper_type"] == "task_group"
    
    def test_initialization_without_fallback_manager(self):
        """测试不带降级管理器的初始化"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None, {"param": "value"})
        
        assert wrapper.task_group_manager == mock_task_group_manager
        assert wrapper.fallback_manager is None
        assert wrapper._metadata["task_group_manager"] is True
        assert wrapper._metadata["fallback_manager"] is False
    
    def test_initialization_with_none_config(self):
        """测试用None配置初始化"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager, None)
        
        assert wrapper.config == {}
    
    @pytest.mark.asyncio
    async def test_generate_async_with_fallback(self):
        """测试异步生成（使用降级）"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="test-target")
        wrapper._generate_with_fallback = AsyncMock(return_value=LLMResponse(
            content="fallback response",
            message=Mock(),
            token_usage=TokenUsage(0, 0, 0),
            model="test-model"
        ))
        
        messages = [Mock(content="Hello")]
        result = await wrapper.generate_async(messages)
        
        assert result.content == "fallback response"
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["successful_requests"] == 1
        wrapper._generate_with_fallback.assert_called_once_with(messages, None)
    
    @pytest.mark.asyncio
    async def test_generate_async_without_fallback(self):
        """测试异步生成（不使用降级）"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = None
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="test-target")
        wrapper._generate_direct = AsyncMock(return_value=LLMResponse(
            content="direct response",
            message=Mock(),
            token_usage=TokenUsage(0, 0),
            model="test-model"
        ))
        
        messages = [Mock(content="Hello")]
        result = await wrapper.generate_async(messages)
        
        assert result.content == "direct response"
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["successful_requests"] == 1
        wrapper._generate_direct.assert_called_once_with(messages, None)
    
    @pytest.mark.asyncio
    async def test_generate_async_exception(self):
        """测试异步生成时发生异常"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="test-target")
        wrapper._generate_with_fallback = AsyncMock(side_effect=Exception("Test error"))
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(TaskGroupWrapperError, match="任务组包装器生成失败"):
            await wrapper.generate_async(messages)
        
        assert wrapper._stats["total_requests"] == 1
        assert wrapper._stats["failed_requests"] == 1
    
    def test_generate_sync_with_fallback(self):
        """测试同步生成（使用降级）"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="test-target")
        wrapper._generate_with_fallback = AsyncMock(return_value=LLMResponse(
            content="fallback response",
            message=Mock(),
            token_usage=TokenUsage(0, 0, 0),
            model="test-model"
        ))
        
        messages = [Mock(content="Hello")]
        result = wrapper.generate(messages)
        
        assert result.content == "fallback response"
    
    def test_generate_sync_without_fallback(self):
        """测试同步生成（不使用降级）"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = None
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="test-target")
        wrapper._generate_direct = AsyncMock(return_value=LLMResponse(
            content="direct response",
            message=Mock(),
            token_usage=TokenUsage(0, 0, 0),
            model="test-model"
        ))
        
        messages = [Mock(content="Hello")]
        result = wrapper.generate(messages)
        
        assert result.content == "direct response"
    
    def test_generate_sync_exception(self):
        """测试同步生成时发生异常"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="test-target")
        wrapper._generate_with_fallback = AsyncMock(side_effect=Exception("Test error"))
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(TaskGroupWrapperError, match="任务组包装器同步生成失败"):
            wrapper.generate(messages)
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._current_target = "current-target"
        wrapper._fallback_history = [
            {"target": "target1", "success": True, "timestamp": "time1"},
            {"target": "target2", "success": False, "error": "error", "timestamp": "time2"}
        ]
        wrapper._attempt_count = 5
        
        info = wrapper.get_model_info()
        
        assert info["type"] == "task_group_wrapper"
        assert info["name"] == "test-wrapper"
        assert info["current_target"] == "current-target"
        assert info["fallback_history"] == [
            {"target": "target1", "success": True, "timestamp": "time1"},
            {"target": "target2", "success": False, "error": "error", "timestamp": "time2"}
        ]
        assert info["task_group_manager"] is True
        assert info["fallback_manager"] is True
        assert info["attempt_count"] == 5
    
    def test_get_target(self):
        """测试获取当前目标"""
        mock_task_group_manager = Mock()
        
        # 从配置获取目标
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None, {"target": "config-target"})
        target = wrapper._get_target()
        
        assert target == "config-target"
        assert wrapper._current_target == "config-target"
    
    def test_get_target_default(self):
        """测试获取默认目标"""
        mock_task_group_manager = Mock()
        
        # 使用包装器名称作为默认目标
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        target = wrapper._get_target()
        
        assert target == "test-wrapper"
        assert wrapper._current_target == "test-wrapper"
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_success(self):
        """测试使用降级机制生成成功"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="primary-target")
        wrapper._get_fallback_groups = Mock(return_value=["fallback1", "fallback2"])
        wrapper.fallback_manager.execute_with_fallback = AsyncMock(return_value="fallback response")
        
        messages = [Mock(content="Hello")]
        result = await wrapper._generate_with_fallback(messages, {"param": "value"})
        
        assert result.content == "fallback response"
        assert result.model == "primary-target"
        wrapper.fallback_manager.execute_with_fallback.assert_called_once_with(
            primary_target="primary-target",
            fallback_groups=["fallback1", "fallback2"],
            prompt="Hello",
            parameters={"param": "value"}
        )
        assert wrapper._attempt_count == 1
        assert len(wrapper._fallback_history) == 1
        assert wrapper._fallback_history[0]["target"] == "primary-target"
        assert wrapper._fallback_history[0]["success"] is True
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_no_fallback_manager(self):
        """测试使用降级机制生成但没有降级管理器"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._get_target = Mock(return_value="primary-target")
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(TaskGroupWrapperError, match="降级管理器未初始化"):
            await wrapper._generate_with_fallback(messages, {"param": "value"})
    
    @pytest.mark.asyncio
    async def test_generate_with_fallback_failure(self):
        """测试使用降级机制生成失败"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, mock_fallback_manager)
        wrapper._get_target = Mock(return_value="primary-target")
        wrapper._get_fallback_groups = Mock(return_value=["fallback1", "fallback2"])
        wrapper.fallback_manager.execute_with_fallback = AsyncMock(side_effect=Exception("Fallback error"))
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(Exception, match="Fallback error"):
            await wrapper._generate_with_fallback(messages, {"param": "value"})
        
        assert wrapper._attempt_count == 1
        assert len(wrapper._fallback_history) == 1
        assert wrapper._fallback_history[0]["target"] == "primary-target"
        assert wrapper._fallback_history[0]["success"] is False
        assert wrapper._fallback_history[0]["error"] == "Fallback error"
    
    @pytest.mark.asyncio
    async def test_generate_direct_success(self):
        """测试直接生成成功"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.get_models_for_group.return_value = ["model-1"]
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._get_target = Mock(return_value="test-target")
        
        messages = [Mock(content="Hello")]
        result = await wrapper._generate_direct(messages, {"param": "value"})
        
        assert "模拟响应 from model-1" in result.content
        assert result.model == "model-1"
        mock_task_group_manager.get_models_for_group.assert_called_once_with("test-target")
    
    @pytest.mark.asyncio
    async def test_generate_direct_no_models(self):
        """测试直接生成但没有找到模型"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.get_models_for_group.return_value = []
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._get_target = Mock(return_value="test-target")
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(TaskGroupWrapperError, match="没有找到模型"):
            await wrapper._generate_direct(messages, {"param": "value"})
    
    @pytest.mark.asyncio
    async def test_generate_direct_exception(self):
        """测试直接生成时发生异常"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.get_models_for_group.side_effect = Exception("Get models error")
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._get_target = Mock(return_value="test-target")
        
        messages = [Mock(content="Hello")]
        
        with pytest.raises(Exception, match="Get models error"):
            await wrapper._generate_direct(messages, {"param": "value"})
    
    def test_get_fallback_groups_from_config(self):
        """测试从配置获取降级组"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None, {
            "fallback_groups": ["config-fallback1", "config-fallback2"]
        })
        
        groups = wrapper._get_fallback_groups("test-target")
        
        assert groups == ["config-fallback1", "config-fallback2"]
        # 任务组管理器的方法不应该被调用，因为配置中已有
        mock_task_group_manager.parse_group_reference.assert_not_called()
    
    def test_get_fallback_groups_from_task_group(self):
        """测试从任务组配置获取降级组"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.parse_group_reference.return_value = ("group1", "echelon1")
        mock_task_group_manager.get_fallback_groups.return_value = ["group-fallback1", "group-fallback2"]
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        
        groups = wrapper._get_fallback_groups("test-target")
        
        assert groups == ["group-fallback1", "group-fallback2"]
        mock_task_group_manager.parse_group_reference.assert_called_once_with("test-target")
        mock_task_group_manager.get_fallback_groups.assert_called_once_with("test-target")
    
    def test_get_fallback_groups_empty(self):
        """测试获取空降级组"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.parse_group_reference.return_value = ("group1", "echelon1")
        mock_task_group_manager.get_fallback_groups.return_value = []
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        
        groups = wrapper._get_fallback_groups("test-target")
        
        assert groups == []
    
    def test_create_llm_response(self):
        """测试创建LLM响应"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._current_target = "test-target"
        
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
        assert response.metadata["wrapper"] == "task_group"
        assert response.metadata["target"] == "test-target"
        assert response.metadata["attempt_count"] == 0
    
    def test_create_llm_response_with_defaults(self):
        """测试创建LLM响应（使用默认值）"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._current_target = "test-target"
        
        response = wrapper._create_llm_response(
            content="Test content",
            model="test-model"
        )
        
        assert response.content == "Test content"
        assert response.model == "test-model"
        assert response.token_usage.prompt_tokens > 0
        assert response.token_usage.completion_tokens > 0
        assert response.token_usage.total_tokens > 0
        assert response.metadata["wrapper"] == "task_group"
        assert response.metadata["target"] == "test-target"
    
    def test_record_success(self):
        """测试记录成功"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        
        wrapper._record_success("test-target")
        
        assert wrapper._attempt_count == 1
        assert len(wrapper._fallback_history) == 1
        assert wrapper._fallback_history[0]["target"] == "test-target"
        assert wrapper._fallback_history[0]["success"] is True
        assert wrapper._fallback_history[0]["timestamp"] is not None
    
    def test_record_failure(self):
        """测试记录失败"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        
        wrapper._record_failure("test-target", "test error")
        
        assert wrapper._attempt_count == 1
        assert len(wrapper._fallback_history) == 1
        assert wrapper._fallback_history[0]["target"] == "test-target"
        assert wrapper._fallback_history[0]["success"] is False
        assert wrapper._fallback_history[0]["error"] == "test error"
        assert wrapper._fallback_history[0]["timestamp"] is not None
    
    def test_record_history_limit(self):
        """测试历史记录限制"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        
        # 添加101个记录
        for i in range(101):
            wrapper._record_success(f"target-{i}")
        
        assert wrapper._attempt_count == 101
        assert len(wrapper._fallback_history) == 100 # 应该限制为100个
        # 检查保留的是最近的100个
        assert wrapper._fallback_history[0]["target"] == "target-1"  # 最旧的应该是target-1
        assert wrapper._fallback_history[-1]["target"] == "target-10"  # 最新的应该是target-100
    
    def test_get_fallback_history(self):
        """测试获取降级历史"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        
        # 添加一些历史记录
        for in range(15):  # 创建15个记录
            wrapper._record_success(f"target-{i}")
        
        history = wrapper.get_fallback_history(limit=10)
        
        assert len(history) == 10
        # 检查是最近的10条记录
        assert history[0]["target"] == "target-5"  # 最旧的
        assert history[-1]["target"] == "target-14"  # 最新的
    
    def test_reset_fallback_history(self):
        """测试重置降级历史"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        
        wrapper._fallback_history = [{"target": "test", "success": True, "timestamp": "time"}]
        wrapper._attempt_count = 5
        
        wrapper.reset_fallback_history()
        
        assert wrapper._fallback_history == []
        assert wrapper._attempt_count == 0
    
    def test_supports_function_calling_false_no_target(self):
        """测试不支持函数调用（无当前目标）"""
        mock_task_group_manager = Mock()
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._current_target = None
        
        assert wrapper.supports_function_calling() is False
    
    def test_supports_function_calling_false_parse_error(self):
        """测试不支持函数调用（解析错误）"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.parse_group_reference.side_effect = Exception("Parse error")
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._current_target = "invalid-target"
        
        assert wrapper.supports_function_calling() is False
        mock_task_group_manager.parse_group_reference.assert_called_once_with("invalid-target")
    
    def test_supports_function_calling_true(self):
        """测试支持函数调用"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.parse_group_reference.return_value = ("group1", "echelon1")
        
        mock_echelon_config = Mock()
        mock_echelon_config.function_calling = True  # 有function_calling配置
        mock_task_group_manager.get_echelon_config.return_value = mock_echelon_config
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._current_target = "group1.echelon1"
        
        assert wrapper.supports_function_calling() is True
        mock_task_group_manager.parse_group_reference.assert_called_once_with("group1.echelon1")
        mock_task_group_manager.get_echelon_config.assert_called_once_with("group1", "echelon1")
    
    def test_supports_function_calling_false_no_function_calling(self):
        """测试不支持函数调用（无function_calling配置）"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.parse_group_reference.return_value = ("group1", "echelon1")
        
        mock_echelon_config = Mock()
        mock_echelon_config.function_calling = None  # 无function_calling配置
        mock_task_group_manager.get_echelon_config.return_value = mock_echelon_config
        
        wrapper = TaskGroupWrapper("test-wrapper", mock_task_group_manager, None)
        wrapper._current_target = "group1.echelon1"
        
        assert wrapper.supports_function_calling() is False