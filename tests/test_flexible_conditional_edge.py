"""灵活条件边测试

测试灵活条件边的功能。
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.infrastructure.graph.edges.flexible_conditional_edge import (
    FlexibleConditionalEdge,
    FlexibleConditionalEdgeFactory
)
from src.infrastructure.graph.config import EdgeConfig, EdgeType
from src.infrastructure.graph.route_functions import (
    RouteFunctionManager,
    get_route_function_manager,
    reset_route_function_manager
)


class TestFlexibleConditionalEdge:
    """灵活条件边测试"""
    
    def setup_method(self):
        """设置测试环境"""
        reset_route_function_manager()
        self.manager = get_route_function_manager()
    
    def test_create_flexible_conditional_edge(self):
        """测试创建灵活条件边"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={},
            description="测试边"
        )
        
        assert edge.from_node == "agent"
        assert edge.route_function == "has_tool_calls"
        assert edge.route_parameters == {}
        assert edge.description == "测试边"
    
    def test_set_route_function_manager(self):
        """测试设置路由函数管理器"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={}
        )
        
        edge.set_route_function_manager(self.manager)
        assert edge._route_function_manager == self.manager
    
    def test_validate_with_valid_config(self):
        """测试验证有效配置"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={}
        )
        edge.set_route_function_manager(self.manager)
        
        errors = edge.validate()
        assert len(errors) == 0
    
    def test_validate_with_invalid_function(self):
        """测试验证无效函数名"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="non_existent_function",
            route_parameters={}
        )
        edge.set_route_function_manager(self.manager)
        
        errors = edge.validate()
        assert len(errors) > 0
        assert any("路由函数不存在" in error for error in errors)
    
    def test_validate_without_manager(self):
        """测试没有设置管理器时的验证"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={}
        )
        
        errors = edge.validate()
        assert len(errors) > 0
        assert any("路由函数管理器未设置" in error for error in errors)
    
    def test_create_route_function(self):
        """测试创建路由函数"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={}
        )
        edge.set_route_function_manager(self.manager)
        
        route_func = edge.create_route_function()
        assert route_func is not None
        
        # 测试路由函数执行
        state = {"messages": []}
        result = route_func(state)
        assert result in ["continue", "end"]
    
    def test_create_route_function_with_parameters(self):
        """测试创建带参数的路由函数"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="iteration_count_equals",
            route_parameters={"count": 5}
        )
        edge.set_route_function_manager(self.manager)
        
        route_func = edge.create_route_function()
        assert route_func is not None
        
        # 测试路由函数执行
        state = {"iteration_count": 5}
        result = route_func(state)
        assert result == "equals"
        
        state = {"iteration_count": 3}
        result = route_func(state)
        assert result == "not_equals"
    
    def test_from_config_with_route_function(self):
        """测试从配置创建灵活条件边（新格式）"""
        config = EdgeConfig(
            from_node="agent",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_tool_calls",
            route_parameters={},
            description="测试边"
        )
        
        edge = FlexibleConditionalEdge.from_config(config, self.manager)
        
        assert edge.from_node == "agent"
        assert edge.route_function == "has_tool_calls"
        assert edge.route_parameters == {}
        assert edge.description == "测试边"
    
    def test_from_config_with_condition(self):
        """测试从配置创建灵活条件边（兼容旧格式）"""
        config = EdgeConfig(
            from_node="agent",
            to_node="tool_executor",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls",
            description="测试边"
        )
        
        edge = FlexibleConditionalEdge.from_config(config, self.manager)
        
        assert edge.from_node == "agent"
        assert edge.route_function == "has_tool_calls"
        assert edge.route_parameters == {}
    
    def test_from_config_with_parameterized_condition(self):
        """测试从配置创建带参数的条件边（兼容旧格式）"""
        config = EdgeConfig(
            from_node="agent",
            to_node="tool_executor",
            type=EdgeType.CONDITIONAL,
            condition="iteration_count_equals:5",
            description="测试边"
        )
        
        edge = FlexibleConditionalEdge.from_config(config, self.manager)
        
        assert edge.from_node == "agent"
        assert edge.route_function == "iteration_count_equals"
        assert edge.route_parameters == {"count": 5}
    
    def test_from_config_with_invalid_type(self):
        """测试从配置创建边时类型不匹配"""
        config = EdgeConfig(
            from_node="agent",
            to_node="tool_executor",
            type=EdgeType.SIMPLE,
            description="测试边"
        )
        
        with pytest.raises(ValueError, match="配置类型不匹配"):
            FlexibleConditionalEdge.from_config(config, self.manager)
    
    def test_to_config(self):
        """测试转换为配置"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={},
            description="测试边"
        )
        
        config = edge.to_config()
        
        assert config.from_node == "agent"
        assert config.to_node == ""  # 灵活条件边不指定目标节点
        assert config.type == EdgeType.CONDITIONAL
        assert config.description == "测试边"
    
    def test_get_route_info(self):
        """测试获取路由函数信息"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={}
        )
        edge.set_route_function_manager(self.manager)
        
        info = edge.get_route_info()
        
        assert info is not None
        assert info["name"] == "has_tool_calls"
        assert info["category"] == "builtin"
        assert "continue" in info["return_values"]
        assert "end" in info["return_values"]
    
    def test_string_representation(self):
        """测试字符串表示"""
        edge = FlexibleConditionalEdge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={},
            description="测试边"
        )
        
        str_repr = str(edge)
        assert "FlexibleConditionalEdge" in str_repr
        assert "agent" in str_repr
        assert "has_tool_calls" in str_repr
        
        repr_str = repr(edge)
        assert "FlexibleConditionalEdge" in repr_str
        assert "from_node='agent'" in repr_str
        assert "route_function='has_tool_calls'" in repr_str


class TestFlexibleConditionalEdgeFactory:
    """灵活条件边工厂测试"""
    
    def setup_method(self):
        """设置测试环境"""
        reset_route_function_manager()
        self.manager = get_route_function_manager()
        self.factory = FlexibleConditionalEdgeFactory(self.manager)
    
    def test_create_edge(self):
        """测试创建边"""
        edge = self.factory.create_edge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={},
            description="测试边"
        )
        
        assert isinstance(edge, FlexibleConditionalEdge)
        assert edge.from_node == "agent"
        assert edge.route_function == "has_tool_calls"
        assert edge.route_parameters == {}
        assert edge.description == "测试边"
    
    def test_create_edge_with_invalid_function(self):
        """测试创建边时函数无效"""
        with pytest.raises(ValueError, match="灵活条件边配置错误"):
            self.factory.create_edge(
                from_node="agent",
                route_function="non_existent_function",
                route_parameters={}
            )
    
    def test_create_from_config(self):
        """测试从配置创建边"""
        config = EdgeConfig(
            from_node="agent",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_tool_calls",
            route_parameters={},
            description="测试边"
        )
        
        edge = self.factory.create_from_config(config)
        
        assert isinstance(edge, FlexibleConditionalEdge)
        assert edge.from_node == "agent"
        assert edge.route_function == "has_tool_calls"
    
    def test_create_batch(self):
        """测试批量创建边"""
        configs = [
            EdgeConfig(
                from_node="agent",
                to_node="",
                type=EdgeType.CONDITIONAL,
                route_function="has_tool_calls",
                route_parameters={}
            ),
            EdgeConfig(
                from_node="tool_executor",
                to_node="",
                type=EdgeType.CONDITIONAL,
                route_function="has_tool_results",
                route_parameters={}
            )
        ]
        
        edges = self.factory.create_batch(configs)
        
        assert len(edges) == 2
        assert all(isinstance(edge, FlexibleConditionalEdge) for edge in edges)
        assert edges[0].route_function == "has_tool_calls"
        assert edges[1].route_function == "has_tool_results"
    
    def test_create_batch_with_error(self):
        """测试批量创建边时有错误"""
        configs = [
            EdgeConfig(
                from_node="agent",
                to_node="",
                type=EdgeType.CONDITIONAL,
                route_function="has_tool_calls",
                route_parameters={}
            ),
            EdgeConfig(
                from_node="tool_executor",
                to_node="",
                type=EdgeType.CONDITIONAL,
                route_function="non_existent_function",
                route_parameters={}
            )
        ]
        
        with pytest.raises(ValueError, match="批量创建灵活条件边失败"):
            self.factory.create_batch(configs)


class TestEdgeIntegration:
    """边集成测试"""
    
    def setup_method(self):
        """设置测试环境"""
        reset_route_function_manager()
        self.manager = get_route_function_manager()
        self.factory = FlexibleConditionalEdgeFactory(self.manager)
    
    def test_edge_with_complex_parameters(self):
        """测试带复杂参数的边"""
        edge = self.factory.create_edge(
            from_node="decision_node",
            route_function="keyword_match",
            route_parameters={
                "keywords": ["error", "exception", "failed"],
                "case_sensitive": False,
                "match_all": False
            }
        )
        
        route_func = edge.create_route_function()
        
        # 模拟消息对象
        class MockMessage:
            def __init__(self, content: str):
                self.content = content
        
        # 测试匹配关键词
        state = {"messages": [MockMessage("There was an error")]}
        result = route_func(state)
        assert result == "matched"
        
        # 测试不匹配关键词
        state = {"messages": [MockMessage("Everything is fine")]}
        result = route_func(state)
        assert result == "not_matched"
    
    def test_edge_with_state_check(self):
        """测试状态检查边"""
        edge = self.factory.create_edge(
            from_node="status_checker",
            route_function="status_check",
            route_parameters={
                "state_key": "process_status",
                "value_mapping": {
                    "success": "complete",
                    "error": "error_handler",
                    "pending": "continue"
                },
                "default_route": "default_handler"
            }
        )
        
        route_func = edge.create_route_function()
        
        # 测试不同状态
        state = {"process_status": "success"}
        assert route_func(state) == "complete"
        
        state = {"process_status": "error"}
        assert route_func(state) == "error_handler"
        
        state = {"process_status": "unknown"}
        assert route_func(state) == "default_handler"
    
    def test_edge_caching(self):
        """测试边函数缓存"""
        edge = self.factory.create_edge(
            from_node="agent",
            route_function="has_tool_calls",
            route_parameters={}
        )
        
        # 第一次创建函数
        func1 = edge.create_route_function()
        
        # 第二次创建函数（应该使用缓存）
        func2 = edge.create_route_function()
        
        assert func1 is func2  # 应该是同一个对象


if __name__ == "__main__":
    pytest.main([__file__])