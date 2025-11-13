"""LLMWrapperFactory单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional

from src.infrastructure.llm.wrappers.wrapper_factory import LLMWrapperFactory
from src.infrastructure.llm.wrappers.base_wrapper import BaseLLMWrapper
from src.infrastructure.llm.wrappers.task_group_wrapper import TaskGroupWrapper
from src.infrastructure.llm.wrappers.polling_pool_wrapper import PollingPoolWrapper
from src.infrastructure.llm.wrappers.exceptions import WrapperFactoryError, WrapperConfigError


class MockWrapper(BaseLLMWrapper):
    """模拟包装器用于测试"""
    
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
    
    async def generate_async(self, messages, parameters=None, **kwargs):
        pass
    
    def generate(self, messages, parameters=None, **kwargs):
        pass
    
    def get_model_info(self) -> dict:
        return {"name": self.name}


class TestLLMWrapperFactory:
    """LLMWrapperFactory测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        mock_task_group_manager = Mock()
        mock_polling_pool_manager = Mock()
        mock_fallback_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager,
            fallback_manager=mock_fallback_manager
        )
        
        assert factory.task_group_manager == mock_task_group_manager
        assert factory.polling_pool_manager == mock_polling_pool_manager
        assert factory.fallback_manager == mock_fallback_manager
        assert factory._wrappers == {}
        assert "task_group" in factory._wrapper_types
        assert "polling_pool" in factory._wrapper_types
        assert factory._wrapper_types["task_group"] == TaskGroupWrapper
        assert factory._wrapper_types["polling_pool"] == PollingPoolWrapper
    
    def test_initialization_optional_params(self):
        """测试初始化（可选参数）"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager
        )
        
        assert factory.task_group_manager == mock_task_group_manager
        assert factory.polling_pool_manager is None
        assert factory.fallback_manager is None
    
    def test_create_task_group_wrapper(self):
        """测试创建任务组包装器"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        wrapper = factory.create_task_group_wrapper("test-wrapper", {"param": "value"})
        
        assert isinstance(wrapper, TaskGroupWrapper)
        assert wrapper.name == "test-wrapper"
        assert wrapper.config == {"param": "value"}
        assert wrapper.task_group_manager == mock_task_group_manager
        assert wrapper.fallback_manager == mock_fallback_manager
        assert factory._wrappers["test-wrapper"] == wrapper
    
    def test_create_task_group_wrapper_error(self):
        """测试创建任务组包装器错误"""
        mock_task_group_manager = Mock()
        mock_task_group_manager.side_effect = Exception("Creation error")
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        with pytest.raises(WrapperFactoryError, match="创建任务组包装器失败"):
            factory.create_task_group_wrapper("test-wrapper", {"param": "value"})
    
    def test_create_polling_pool_wrapper(self):
        """测试创建轮询池包装器"""
        mock_task_group_manager = Mock()
        mock_polling_pool_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager
        )
        
        wrapper = factory.create_polling_pool_wrapper("test-wrapper", {"param": "value"})
        
        assert isinstance(wrapper, PollingPoolWrapper)
        assert wrapper.name == "test-wrapper"
        assert wrapper.config == {"param": "value"}
        assert wrapper.polling_pool_manager == mock_polling_pool_manager
        assert factory._wrappers["test-wrapper"] == wrapper
    
    def test_create_polling_pool_wrapper_no_manager(self):
        """测试创建轮询池包装器但没有管理器"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        with pytest.raises(WrapperFactoryError, match="轮询池管理器未配置"):
            factory.create_polling_pool_wrapper("test-wrapper", {"param": "value"})
    
    def test_create_polling_pool_wrapper_error(self):
        """测试创建轮询池包装器错误"""
        mock_task_group_manager = Mock()
        mock_polling_pool_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager
        )
        # 模拟创建失败
        original_init = PollingPoolWrapper.__init__
        def failing_init(self, name, polling_pool_manager, config=None):
            raise Exception("Creation error")
        PollingPoolWrapper.__init__ = failing_init
        
        try:
            with pytest.raises(WrapperFactoryError, match="创建轮询池包装器失败"):
                factory.create_polling_pool_wrapper("test-wrapper", {"param": "value"})
        finally:
            PollingPoolWrapper.__init__ = original_init
    
    def test_create_wrapper_from_config_task_group(self):
        """测试从配置创建任务组包装器"""
        mock_task_group_manager = Mock()
        mock_fallback_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            fallback_manager=mock_fallback_manager
        )
        
        wrapper = factory.create_wrapper_from_config(
            "test-wrapper", 
            "task_group", 
            {"param": "value"}
        )
        
        assert isinstance(wrapper, TaskGroupWrapper)
        assert wrapper.name == "test-wrapper"
        assert factory._wrappers["test-wrapper"] == wrapper
    
    def test_create_wrapper_from_config_polling_pool(self):
        """测试从配置创建轮询池包装器"""
        mock_task_group_manager = Mock()
        mock_polling_pool_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager
        )
        
        wrapper = factory.create_wrapper_from_config(
            "test-wrapper", 
            "polling_pool", 
            {"param": "value"}
        )
        
        assert isinstance(wrapper, PollingPoolWrapper)
        assert wrapper.name == "test-wrapper"
        assert factory._wrappers["test-wrapper"] == wrapper
    
    def test_create_wrapper_from_config_unsupported_type(self):
        """测试从配置创建不支持的包装器类型"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        with pytest.raises(WrapperFactoryError, match="不支持的包装器类型"):
            factory.create_wrapper_from_config("test-wrapper", "unsupported_type", {"param": "value"})
    
    def test_create_wrapper_from_config_custom_type(self):
        """测试从配置创建自定义包装器类型"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        factory.register_wrapper_type("mock", MockWrapper)
        
        wrapper = factory.create_wrapper_from_config(
            "test-wrapper", 
            "mock", 
            {"param": "value"}
        )
        
        assert isinstance(wrapper, MockWrapper)
        assert wrapper.name == "test-wrapper"
        assert factory._wrappers["test-wrapper"] == wrapper
    
    def test_get_wrapper(self):
        """测试获取包装器"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        wrapper = MockWrapper("test-wrapper")
        factory._wrappers["test-wrapper"] = wrapper
        
        retrieved_wrapper = factory.get_wrapper("test-wrapper")
        
        assert retrieved_wrapper == wrapper
    
    def test_get_wrapper_not_found(self):
        """测试获取不存在的包装器"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        retrieved_wrapper = factory.get_wrapper("non-existent")
        
        assert retrieved_wrapper is None
    
    def test_list_wrappers(self):
        """测试列出包装器"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        wrapper1 = MockWrapper("wrapper1")
        wrapper2 = TaskGroupWrapper("wrapper2", Mock(), Mock())
        factory._wrappers["wrapper1"] = wrapper1
        factory._wrappers["wrapper2"] = wrapper2
        
        wrapper_list = factory.list_wrappers()
        
        assert wrapper_list["wrapper1"] == "MockWrapper"
        assert wrapper_list["wrapper2"] == "TaskGroupWrapper"
    
    def test_remove_wrapper(self):
        """测试移除包装器"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        wrapper = MockWrapper("test-wrapper")
        factory._wrappers["test-wrapper"] = wrapper
        
        result = factory.remove_wrapper("test-wrapper")
        
        assert result is True
        assert "test-wrapper" not in factory._wrappers
    
    def test_remove_wrapper_not_found(self):
        """测试移除不存在的包装器"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        result = factory.remove_wrapper("non-existent")
        
        assert result is False
    
    def test_register_wrapper_type(self):
        """测试注册包装器类型"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        factory.register_wrapper_type("custom", MockWrapper)
        
        assert factory._wrapper_types["custom"] == MockWrapper
    
    def test_register_wrapper_type_invalid(self):
        """测试注册无效的包装器类型"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        class InvalidClass:
            pass
        
        with pytest.raises(WrapperFactoryError, match="包装器类必须继承自BaseLLMWrapper"):
            factory.register_wrapper_type("invalid", InvalidClass)
    
    def test_create_wrappers_from_config(self):
        """测试从配置批量创建包装器"""
        mock_task_group_manager = Mock()
        mock_polling_pool_manager = Mock()
        mock_fallback_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager,
            fallback_manager=mock_fallback_manager
        )
        
        wrappers_config = {
            "wrapper1": {
                "type": "task_group",
                "param": "value1"
            },
            "wrapper2": {
                "type": "polling_pool",
                "param": "value2"
            }
        }
        
        created_wrappers = factory.create_wrappers_from_config(wrappers_config)
        
        assert len(created_wrappers) == 2
        assert "wrapper1" in created_wrappers
        assert "wrapper2" in created_wrappers
        assert isinstance(created_wrappers["wrapper1"], TaskGroupWrapper)
        assert isinstance(created_wrappers["wrapper2"], PollingPoolWrapper)
        assert len(factory._wrappers) == 2
        assert "wrapper1" in factory._wrappers
        assert "wrapper2" in factory._wrappers
    
    def test_create_wrappers_from_config_missing_type(self):
        """测试从配置批量创建包装器但缺少类型"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        wrappers_config = {
            "wrapper1": {
                "param": "value1"  # 缺少type
            },
            "wrapper2": {
                "type": "task_group",
                "param": "value2"
            }
        }
        
        created_wrappers = factory.create_wrappers_from_config(wrappers_config)
        
        assert len(created_wrappers) == 1  # 只有wrapper2被创建
        assert "wrapper2" in created_wrappers
        assert "wrapper1" not in created_wrappers
    
    def test_create_wrappers_from_config_error(self):
        """测试从配置批量创建包装器时发生错误"""
        mock_task_group_manager = Mock()
        mock_polling_pool_manager = Mock()
        
        factory = LLMWrapperFactory(
            task_group_manager=mock_task_group_manager,
            polling_pool_manager=mock_polling_pool_manager
        )
        
        # 模拟创建失败
        original_create = factory.create_wrapper_from_config
        def failing_create(name, wrapper_type, config=None):
            if name == "wrapper1":
                raise Exception("Creation error")
            return original_create(name, wrapper_type, config)
        factory.create_wrapper_from_config = failing_create
        
        wrappers_config = {
            "wrapper1": {
                "type": "task_group",
                "param": "value1"
            },
            "wrapper2": {
                "type": "task_group",
                "param": "value2"
            }
        }
        
        created_wrappers = factory.create_wrappers_from_config(wrappers_config)
        
        assert len(created_wrappers) == 1  # 只有wrapper2被创建
        assert "wrapper2" in created_wrappers
        assert "wrapper1" not in created_wrappers
    
    def test_get_wrapper_stats(self):
        """测试获取包装器统计信息"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        # 创建一些包装器
        wrapper1 = MockWrapper("wrapper1")
        wrapper1.get_stats = Mock(return_value={"total_requests": 10})
        wrapper2 = TaskGroupWrapper("wrapper2", Mock(), Mock())
        wrapper2.get_stats = Mock(return_value={"total_requests": 5})
        factory._wrappers["wrapper1"] = wrapper1
        factory._wrappers["wrapper2"] = wrapper2
        
        stats = factory.get_wrapper_stats()
        
        assert stats["total_wrappers"] == 2
        assert stats["wrapper_types"]["MockWrapper"] == 1
        assert stats["wrapper_types"]["TaskGroupWrapper"] == 1
        assert stats["wrapper_stats"]["wrapper1"]["type"] == "MockWrapper"
        assert stats["wrapper_stats"]["wrapper1"]["stats"]["total_requests"] == 10
        assert stats["wrapper_stats"]["wrapper2"]["type"] == "TaskGroupWrapper"
        assert stats["wrapper_stats"]["wrapper2"]["stats"]["total_requests"] == 5
    
    def test_get_wrapper_stats_with_error(self):
        """测试获取包装器统计信息时发生错误"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        # 创建一个包装器，其get_stats方法会抛出异常
        wrapper1 = MockWrapper("wrapper1")
        wrapper1.get_stats = Mock(side_effect=Exception("Stats error"))
        factory._wrappers["wrapper1"] = wrapper1
        
        stats = factory.get_wrapper_stats()
        
        assert stats["total_wrappers"] == 1
        assert stats["wrapper_stats"]["wrapper1"]["type"] == "MockWrapper"
        assert stats["wrapper_stats"]["wrapper1"]["error"] == "Stats error"
    
    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """测试对所有包装器执行健康检查"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        # 创建一个有health_check方法的包装器
        wrapper_with_health = Mock()
        wrapper_with_health.name = "wrapper_with_health"
        async def async_health_check():
            return {"healthy": True}
        wrapper_with_health.health_check = async_health_check
        wrapper_with_health.__class__.__name__ = "TestWrapper"
        
        # 创建一个没有health_check方法的包装器
        wrapper_without_health = Mock()
        wrapper_without_health.name = "wrapper_without_health"
        wrapper_without_health.__class__.__name__ = "TestWrapper2"
        wrapper_without_health.health_check = None
        
        factory._wrappers["wrapper_with_health"] = wrapper_with_health
        factory._wrappers["wrapper_without_health"] = wrapper_without_health
        
        health_status = factory.health_check_all()
        
        assert "wrapper_with_health" in health_status
        assert "wrapper_without_health" in health_status
        assert health_status["wrapper_with_health"]["healthy"] is True
        assert health_status["wrapper_without_health"]["healthy"] is True
        assert health_status["wrapper_without_health"]["note"] == "无健康检查方法"
    
    @pytest.mark.asyncio
    async def test_health_check_all_with_error(self):
        """测试对所有包装器执行健康检查时发生错误"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        # 创建一个health_check方法会抛出异常的包装器
        wrapper = Mock()
        wrapper.name = "failing_wrapper"
        async def failing_health_check():
            raise Exception("Health check error")
        wrapper.health_check = failing_health_check
        wrapper.__class__.__name__ = "TestWrapper"
        
        factory._wrappers["failing_wrapper"] = wrapper
        
        health_status = factory.health_check_all()
        
        assert "failing_wrapper" in health_status
        assert health_status["failing_wrapper"]["healthy"] is False
        assert health_status["failing_wrapper"]["error"] == "Health check error"
    
    def test_reset_all_stats(self):
        """测试重置所有包装器的统计信息"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        # 创建一个有reset_stats方法的包装器
        wrapper_with_reset = Mock()
        wrapper_with_reset.reset_stats = Mock()
        wrapper_with_reset.reset_fallback_history = None
        wrapper_with_reset.reset_rotation_history = None
        
        # 创建一个有reset_fallback_history方法的包装器
        wrapper_with_fallback_reset = Mock()
        wrapper_with_fallback_reset.reset_stats = None
        wrapper_with_fallback_reset.reset_fallback_history = Mock()
        wrapper_with_fallback_reset.reset_rotation_history = None
        
        # 创建一个有reset_rotation_history方法的包装器
        wrapper_with_rotation_reset = Mock()
        wrapper_with_rotation_reset.reset_stats = None
        wrapper_with_rotation_reset.reset_fallback_history = None
        wrapper_with_rotation_reset.reset_rotation_history = Mock()
        
        # 创建一个没有重置方法的包装器
        wrapper_without_reset = Mock()
        wrapper_without_reset.reset_stats = None
        wrapper_without_reset.reset_fallback_history = None
        wrapper_without_reset.reset_rotation_history = None
        
        factory._wrappers["wrapper_with_reset"] = wrapper_with_reset
        factory._wrappers["wrapper_with_fallback_reset"] = wrapper_with_fallback_reset
        factory._wrappers["wrapper_with_rotation_reset"] = wrapper_with_rotation_reset
        factory._wrappers["wrapper_without_reset"] = wrapper_without_reset
        
        factory.reset_all_stats()
        
        wrapper_with_reset.reset_stats.assert_called_once()
        wrapper_with_fallback_reset.reset_fallback_history.assert_called_once()
        wrapper_with_rotation_reset.reset_rotation_history.assert_called_once()
    
    def test_reset_all_stats_with_error(self):
        """测试重置所有包装器统计信息时发生错误"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        # 创建一个重置方法会抛出异常的包装器
        wrapper = Mock()
        wrapper.reset_stats = Mock(side_effect=Exception("Reset error"))
        wrapper.reset_fallback_history = None
        wrapper.reset_rotation_history = None
        
        factory._wrappers["failing_wrapper"] = wrapper
        
        # 应该不会抛出异常，只是记录警告
        factory.reset_all_stats()
        
        wrapper.reset_stats.assert_called_once()
    
    def test_shutdown(self):
        """测试关闭包装器工厂"""
        mock_task_group_manager = Mock()
        
        factory = LLMWrapperFactory(task_group_manager=mock_task_group_manager)
        
        # 添加一些包装器
        factory._wrappers["wrapper1"] = MockWrapper("wrapper1")
        factory._wrappers["wrapper2"] = MockWrapper("wrapper2")
        
        assert len(factory._wrappers) == 2
        
        factory.shutdown()
        
        assert len(factory._wrappers) == 0