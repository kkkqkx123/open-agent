"""路由函数系统测试

测试路由函数注册表、管理器和加载器的功能。
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.infrastructure.graph.route_functions import (
    RouteFunctionRegistry,
    RouteFunctionConfig,
    RouteFunctionManager,
    RouteFunctionLoader,
    BuiltinRouteFunctions,
    get_route_function_manager,
    reset_route_function_manager
)


class TestRouteFunctionRegistry:
    """路由函数注册表测试"""
    
    def test_register_route_function(self):
        """测试注册路由函数"""
        registry = RouteFunctionRegistry()
        config = RouteFunctionConfig(
            name="test_func",
            description="测试函数",
            category="test"
        )
        
        def test_function(state: Dict[str, Any]) -> str:
            return "test"
        
        registry.register_route_function("test_func", test_function, config)
        
        assert registry.get_route_function("test_func") == test_function
        assert registry.get_route_config("test_func") == config
        assert "test_func" in registry.list_route_functions()
        assert "test" in registry.list_categories()
    
    def test_unregister_route_function(self):
        """测试注销路由函数"""
        registry = RouteFunctionRegistry()
        config = RouteFunctionConfig(
            name="test_func",
            description="测试函数",
            category="test"
        )
        
        def test_function(state: Dict[str, Any]) -> str:
            return "test"
        
        registry.register_route_function("test_func", test_function, config)
        assert registry.unregister("test_func") == True
        assert registry.get_route_function("test_func") is None
        assert registry.unregister("test_func") == False
    
    def test_list_route_functions(self):
        """测试列出路由函数"""
        registry = RouteFunctionRegistry()
        
        # 添加不同分类的函数
        for i in range(3):
            config = RouteFunctionConfig(
                name=f"test_func_{i}",
                description=f"测试函数 {i}",
                category=f"category_{i % 2}"
            )
            
            def test_function(state: Dict[str, Any]) -> str:
                return f"test_{i}"
            
            registry.register_route_function(f"test_func_{i}", test_function, config)
        
        # 测试列出所有函数
        all_functions = registry.list_route_functions()
        assert len(all_functions) == 3
        
        # 测试按分类列出
        category_0_functions = registry.list_route_functions("category_0")
        category_1_functions = registry.list_route_functions("category_1")
        assert len(category_0_functions) == 2
        assert len(category_1_functions) == 1
    
    def test_validate_route_function(self):
        """测试验证路由函数"""
        registry = RouteFunctionRegistry()
        
        # 测试不存在的函数
        errors = registry.validate_route_function("non_existent")
        assert len(errors) > 0
        assert "路由函数不存在" in errors[0]
        
        # 测试有效函数
        config = RouteFunctionConfig(
            name="test_func",
            description="测试函数",
            return_values=["test"]
        )
        
        def test_function(state: Dict[str, Any]) -> str:
            return "test"
        
        registry.register_route_function("test_func", test_function, config)
        errors = registry.validate_route_function("test_func")
        assert len(errors) == 0
        
        # 测试无效配置
        invalid_config = RouteFunctionConfig(
            name="",
            description="",
            return_values=[]
        )
        
        registry.register_route_function("invalid_func", test_function, invalid_config)
        errors = registry.validate_route_function("invalid_func")
        assert len(errors) > 0


class TestRouteFunctionLoader:
    """路由函数加载器测试"""
    
    def test_create_config_based_function(self):
        """测试创建基于配置的路由函数"""
        registry = RouteFunctionRegistry()
        loader = RouteFunctionLoader(registry)
        
        # 测试状态检查函数
        config = {
            "type": "state_check",
            "state_key": "status",
            "value_mapping": {
                "success": "complete",
                "error": "failed"
            },
            "default_route": "unknown"
        }
        
        func = loader._create_config_based_function(config)
        
        # 测试成功状态
        state = {"status": "success"}
        assert func(state) == "complete"
        
        # 测试错误状态
        state = {"status": "error"}
        assert func(state) == "failed"
        
        # 测试未知状态
        state = {"status": "unknown"}
        assert func(state) == "unknown"
    
    def test_create_message_check_function(self):
        """测试创建消息检查函数"""
        registry = RouteFunctionRegistry()
        loader = RouteFunctionLoader(registry)
        
        config = {
            "keywords": ["error", "failed"],
            "case_sensitive": False,
            "return_true": "found",
            "return_false": "not_found"
        }
        
        func = loader._create_message_check_function(config)
        
        # 模拟消息对象
        class MockMessage:
            def __init__(self, content: str):
                self.content = content
        
        # 测试匹配关键词
        state = {"messages": [MockMessage("There was an error")]}
        assert func(state) == "found"
        
        # 测试不匹配关键词
        state = {"messages": [MockMessage("Everything is fine")]}
        assert func(state) == "not_found"
        
        # 测试空消息列表
        state = {"messages": []}
        assert func(state) == "not_found"
    
    def test_create_tool_check_function(self):
        """测试创建工具检查函数"""
        registry = RouteFunctionRegistry()
        loader = RouteFunctionLoader(registry)
        
        config = {
            "has_tool_calls": True,
            "return_true": "has_tools",
            "return_false": "no_tools"
        }
        
        func = loader._create_tool_check_function(config)
        
        # 模拟带工具调用的消息
        class MockMessage:
            def __init__(self, tool_calls=None):
                self.tool_calls = tool_calls
        
        # 测试有工具调用
        state = {"messages": [MockMessage([{"name": "test"}])]}
        assert func(state) == "has_tools"
        
        # 测试无工具调用
        state = {"messages": [MockMessage()]}
        assert func(state) == "no_tools"


class TestBuiltinRouteFunctions:
    """内置路由函数测试"""
    
    def test_has_tool_calls(self):
        """测试has_tool_calls函数"""
        # 模拟带工具调用的消息
        class MockMessage:
            def __init__(self, tool_calls=None):
                self.tool_calls = tool_calls
        
        # 测试有工具调用
        state = {"messages": [MockMessage([{"name": "test"}])]}
        assert BuiltinRouteFunctions.has_tool_calls(state) == "continue"
        
        # 测试无工具调用
        state = {"messages": [MockMessage()]}
        assert BuiltinRouteFunctions.has_tool_calls(state) == "end"
        
        # 测试空消息列表
        state = {"messages": []}
        assert BuiltinRouteFunctions.has_tool_calls(state) == "end"
    
    def test_no_tool_calls(self):
        """测试no_tool_calls函数"""
        # 模拟带工具调用的消息
        class MockMessage:
            def __init__(self, tool_calls=None):
                self.tool_calls = tool_calls
        
        # 测试有工具调用
        state = {"messages": [MockMessage([{"name": "test"}])]}
        assert BuiltinRouteFunctions.no_tool_calls(state) == "end"
        
        # 测试无工具调用
        state = {"messages": [MockMessage()]}
        assert BuiltinRouteFunctions.no_tool_calls(state) == "continue"
    
    def test_has_tool_results(self):
        """测试has_tool_results函数"""
        # 测试有工具结果
        state = {"tool_results": [{"result": "test"}]}
        assert BuiltinRouteFunctions.has_tool_results(state) == "continue"
        
        # 测试无工具结果
        state = {"tool_results": []}
        assert BuiltinRouteFunctions.has_tool_results(state) == "end"
    
    def test_max_iterations_reached(self):
        """测试max_iterations_reached函数"""
        # 测试达到最大迭代次数
        state = {"iteration_count": 10, "max_iterations": 10}
        assert BuiltinRouteFunctions.max_iterations_reached(state) == "end"
        
        # 测试未达到最大迭代次数
        state = {"iteration_count": 5, "max_iterations": 10}
        assert BuiltinRouteFunctions.max_iterations_reached(state) == "continue"
    
    def test_has_errors(self):
        """测试has_errors函数"""
        # 测试有错误
        state = {"tool_results": [{"success": False}]}
        assert BuiltinRouteFunctions.has_errors(state) == "error"
        
        # 测试无错误
        state = {"tool_results": [{"success": True}]}
        assert BuiltinRouteFunctions.has_errors(state) == "continue"
    
    def test_keyword_match(self):
        """测试keyword_match函数"""
        # 模拟消息对象
        class MockMessage:
            def __init__(self, content: str):
                self.content = content
        
        # 测试匹配关键词
        state = {
            "messages": [MockMessage("There was an error")],
            "_route_parameters": {"keywords": ["error", "failed"]}
        }
        assert BuiltinRouteFunctions.keyword_match(state) == "matched"
        
        # 测试不匹配关键词
        state = {
            "messages": [MockMessage("Everything is fine")],
            "_route_parameters": {"keywords": ["error", "failed"]}
        }
        assert BuiltinRouteFunctions.keyword_match(state) == "not_matched"


class TestRouteFunctionManager:
    """路由函数管理器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        reset_route_function_manager()
    
    def test_get_route_function_manager(self):
        """测试获取路由函数管理器"""
        manager = get_route_function_manager()
        assert manager is not None
        assert isinstance(manager, RouteFunctionManager)
        
        # 测试单例模式
        manager2 = get_route_function_manager()
        assert manager is manager2
    
    def test_register_custom_function(self):
        """测试注册自定义函数"""
        manager = get_route_function_manager()
        
        def custom_function(state: Dict[str, Any]) -> str:
            return "custom"
        
        config = RouteFunctionConfig(
            name="custom_func",
            description="自定义函数",
            category="custom"
        )
        
        manager.register_custom_function("custom_func", custom_function, config)
        
        assert manager.get_route_function("custom_func") == custom_function
        assert "custom_func" in manager.list_route_functions()
        assert "custom_func" in manager.list_functions_by_category("custom")
    
    def test_validate_route_function(self):
        """测试验证路由函数参数"""
        manager = get_route_function_manager()
        
        # 测试存在的函数
        errors = manager.validate_route_function("has_tool_calls", {})
        assert len(errors) == 0
        
        # 测试不存在的函数
        errors = manager.validate_route_function("non_existent", {})
        assert len(errors) > 0
        assert "路由函数不存在" in errors[0]
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        manager = get_route_function_manager()
        stats = manager.get_statistics()
        
        assert "total_functions" in stats
        assert "categories" in stats
        assert "implementations" in stats
        assert stats["total_functions"] > 0  # 应该有内置函数


class TestIntegration:
    """集成测试"""
    
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 重置管理器
        reset_route_function_manager()
        
        # 获取管理器
        manager = get_route_function_manager()
        
        # 注册自定义函数
        def custom_router(state: Dict[str, Any]) -> str:
            priority = state.get("priority", "low")
            if priority == "high":
                return "urgent"
            elif priority == "medium":
                return "normal"
            else:
                return "low_priority"
        
        config = RouteFunctionConfig(
            name="custom_router",
            description="自定义路由器",
            category="custom",
            return_values=["urgent", "normal", "low_priority"]
        )
        
        manager.register_custom_function("custom_router", custom_router, config)
        
        # 测试路由函数
        route_func = manager.get_route_function("custom_router")
        assert route_func is not None
        
        # 测试不同优先级
        assert route_func({"priority": "high"}) == "urgent"
        assert route_func({"priority": "medium"}) == "normal"
        assert route_func({"priority": "low"}) == "low_priority"
        assert route_func({}) == "low_priority"  # 默认值
        
        # 测试统计信息
        stats = manager.get_statistics()
        assert stats["categories"]["custom"] >= 1
        assert stats["implementations"]["custom"] >= 1


if __name__ == "__main__":
    pytest.main([__file__])