"""灵活图构建器测试

测试图构建器对灵活条件边的支持。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.infrastructure.graph.builder import UnifiedGraphBuilder
from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.route_functions import get_route_function_manager, reset_route_function_manager


class TestFlexibleGraphBuilder:
    """灵活图构建器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        reset_route_function_manager()
        self.route_function_manager = get_route_function_manager()
        self.builder = UnifiedGraphBuilder(
            route_function_config_dir="configs/edges"
        )
    
    def test_builder_initialization(self):
        """测试构建器初始化"""
        assert self.builder.route_function_manager is not None
        assert self.builder.flexible_edge_factory is not None
    
    def test_build_graph_with_flexible_edges(self):
        """测试构建包含灵活条件边的图"""
        # 创建图配置
        config = GraphConfig(
            name="test_graph",
            description="测试图"
        )
        
        # 添加节点
        config.nodes["agent"] = NodeConfig(
            name="agent",
            function_name="llm_node"
        )
        config.nodes["tool_executor"] = NodeConfig(
            name="tool_executor",
            function_name="tool_node"
        )
        config.nodes["response_generator"] = NodeConfig(
            name="response_generator",
            function_name="llm_node"
        )
        
        # 添加灵活条件边
        config.edges.append(EdgeConfig(
            from_node="__start__",
            to_node="agent",
            type=EdgeType.SIMPLE
        ))
        
        config.edges.append(EdgeConfig(
            from_node="agent",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_tool_calls",
            route_parameters={},
            path_map={
                "continue": "tool_executor",
                "end": "response_generator"
            }
        ))
        
        config.edges.append(EdgeConfig(
            from_node="tool_executor",
            to_node="response_generator",
            type=EdgeType.SIMPLE
        ))
        
        config.edges.append(EdgeConfig(
            from_node="response_generator",
            to_node="__end__",
            type=EdgeType.SIMPLE
        ))
        
        config.entry_point = "agent"
        
        # 构建图
        with patch('src.infrastructure.graph.builder.StateGraph') as mock_state_graph:
            mock_builder = Mock()
            mock_state_graph.return_value = mock_builder
            
            # 模拟节点函数
            with patch.object(self.builder, '_get_node_function') as mock_get_node:
                mock_get_node.return_value = Mock()
                
                # 构建图
                graph = self.builder.build_graph(config)
                
                # 验证调用
                mock_builder.add_node.assert_called()
                mock_builder.add_edge.assert_called()
                mock_builder.add_conditional_edges.assert_called()
    
    def test_add_flexible_conditional_edge(self):
        """测试添加灵活条件边"""
        config = EdgeConfig(
            from_node="agent",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_tool_calls",
            route_parameters={},
            path_map={
                "continue": "tool_executor",
                "end": "response_generator"
            }
        )
        
        mock_builder = Mock()
        
        # 添加灵活条件边
        self.builder._add_flexible_conditional_edge(mock_builder, config)
        
        # 验证调用了add_conditional_edges
        mock_builder.add_conditional_edges.assert_called_once()
        call_args = mock_builder.add_conditional_edges.call_args
        assert call_args[0][0] == "agent"  # from_node
        assert call_args[0][2] == {  # path_map
            "continue": "tool_executor",
            "end": "response_generator"
        }
    
    def test_add_legacy_conditional_edge(self):
        """测试添加传统条件边"""
        config = EdgeConfig(
            from_node="agent",
            to_node="tool_executor",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls",
            path_map={
                "continue": "tool_executor",
                "end": "__end__"
            }
        )
        
        mock_builder = Mock()
        
        # 添加传统条件边
        with patch.object(self.builder, '_get_condition_function') as mock_get_condition:
            mock_get_condition.return_value = Mock()
            
            self.builder._add_legacy_conditional_edge(mock_builder, config)
            
            # 验证调用了add_conditional_edges
            mock_builder.add_conditional_edges.assert_called_once()
    
    def test_add_conditional_edge_error_handling(self):
        """测试条件边错误处理"""
        config = EdgeConfig(
            from_node="agent",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="non_existent_function",
            route_parameters={}
        )
        
        mock_builder = Mock()
        
        # 应该抛出异常
        with pytest.raises(Exception):
            self.builder._add_conditional_edge(mock_builder, config)
    
    def test_get_condition_function_priority(self):
        """测试条件函数获取优先级"""
        # 1. 优先从路由函数管理器获取
        route_func = self.builder._get_condition_function("has_tool_calls")
        assert route_func is not None
        
        # 2. 测试不存在的函数
        route_func = self.builder._get_condition_function("non_existent")
        assert route_func is None
    
    def test_build_graph_validation(self):
        """测试图构建验证"""
        # 创建无效配置（缺少入口点）
        config = GraphConfig(
            name="test_graph",
            description="测试图"
        )
        
        # 应该抛出验证错误
        with pytest.raises(ValueError, match="图配置验证失败"):
            self.builder.build_graph(config)
    
    def test_build_graph_with_complex_routing(self):
        """测试构建包含复杂路由的图"""
        config = GraphConfig(
            name="complex_graph",
            description="复杂路由测试图"
        )
        
        # 添加节点
        config.nodes["classifier"] = NodeConfig(
            name="classifier",
            function_name="llm_node"
        )
        config.nodes["urgent_handler"] = NodeConfig(
            name="urgent_handler",
            function_name="tool_node"
        )
        config.nodes["normal_handler"] = NodeConfig(
            name="normal_handler",
            function_name="llm_node"
        )
        config.nodes["error_handler"] = NodeConfig(
            name="error_handler",
            function_name="error_node"
        )
        
        # 添加复杂路由边
        config.edges.append(EdgeConfig(
            from_node="__start__",
            to_node="classifier",
            type=EdgeType.SIMPLE
        ))
        
        config.edges.append(EdgeConfig(
            from_node="classifier",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="keyword_match",
            route_parameters={
                "keywords": ["urgent", "emergency"],
                "case_sensitive": False
            },
            path_map={
                "matched": "urgent_handler",
                "not_matched": "normal_handler"
            }
        ))
        
        config.edges.append(EdgeConfig(
            from_node="urgent_handler",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_errors",
            route_parameters={},
            path_map={
                "error": "error_handler",
                "continue": "__end__"
            }
        ))
        
        config.edges.append(EdgeConfig(
            from_node="normal_handler",
            to_node="__end__",
            type=EdgeType.SIMPLE
        ))
        
        config.edges.append(EdgeConfig(
            from_node="error_handler",
            to_node="__end__",
            type=EdgeType.SIMPLE
        ))
        
        config.entry_point = "classifier"
        
        # 构建图
        with patch('src.infrastructure.graph.builder.StateGraph') as mock_state_graph:
            mock_builder = Mock()
            mock_state_graph.return_value = mock_builder
            
            with patch.object(self.builder, '_get_node_function') as mock_get_node:
                mock_get_node.return_value = Mock()
                
                graph = self.builder.build_graph(config)
                
                # 验证条件边被正确添加
                conditional_calls = [call for call in mock_builder.add_conditional_edges.call_args_list 
                                  if call[0][0] in ["classifier", "urgent_handler"]]
                assert len(conditional_calls) == 2
    
    def test_edge_type_detection(self):
        """测试边类型检测"""
        # 灵活条件边
        flexible_config = EdgeConfig(
            from_node="agent",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_tool_calls",
            route_parameters={}
        )
        
        assert flexible_config.is_flexible_conditional() == True
        
        # 传统条件边
        legacy_config = EdgeConfig(
            from_node="agent",
            to_node="tool_executor",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls"
        )
        
        assert legacy_config.is_flexible_conditional() == False
        
        # 简单边
        simple_config = EdgeConfig(
            from_node="agent",
            to_node="tool_executor",
            type=EdgeType.SIMPLE
        )
        
        assert simple_config.is_flexible_conditional() == False


class TestGraphBuilderIntegration:
    """图构建器集成测试"""
    
    def setup_method(self):
        """设置测试环境"""
        reset_route_function_manager()
    
    def test_end_to_end_graph_building(self):
        """测试端到端图构建"""
        # 创建带有路由函数配置目录的构建器
        builder = UnifiedGraphBuilder(
            route_function_config_dir="configs/edges"
        )
        
        # 创建完整的图配置
        config = GraphConfig(
            name="end_to_end_test",
            description="端到端测试图"
        )
        
        # 添加状态定义
        config.state_schema.fields["messages"] = {
            "type": "List[BaseMessage]",
            "reducer": "operator.add"
        }
        config.state_schema.fields["iteration_count"] = {
            "type": "int",
            "default": 0
        }
        config.state_schema.fields["max_iterations"] = {
            "type": "int",
            "default": 5
        }
        
        # 添加节点
        config.nodes["agent"] = NodeConfig(
            name="agent",
            function_name="llm_node"
        )
        config.nodes["tool_executor"] = NodeConfig(
            name="tool_executor",
            function_name="tool_node"
        )
        config.nodes["finalizer"] = NodeConfig(
            name="finalizer",
            function_name="llm_node"
        )
        
        # 添加边
        config.edges.append(EdgeConfig(
            from_node="__start__",
            to_node="agent",
            type=EdgeType.SIMPLE
        ))
        
        # 灵活条件边：检查工具调用
        config.edges.append(EdgeConfig(
            from_node="agent",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_tool_calls",
            route_parameters={},
            path_map={
                "continue": "tool_executor",
                "end": "finalizer"
            }
        ))
        
        # 灵活条件边：检查迭代次数
        config.edges.append(EdgeConfig(
            from_node="tool_executor",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="max_iterations_reached",
            route_parameters={
                "max_iterations": 5
            },
            path_map={
                "continue": "agent",
                "end": "finalizer"
            }
        ))
        
        config.edges.append(EdgeConfig(
            from_node="finalizer",
            to_node="__end__",
            type=EdgeType.SIMPLE
        ))
        
        config.entry_point = "agent"
        
        # 验证配置
        errors = config.validate()
        assert len(errors) == 0
        
        # 模拟构建图
        with patch('src.infrastructure.graph.builder.StateGraph') as mock_state_graph:
            mock_builder = Mock()
            mock_state_graph.return_value = mock_builder
            mock_compiled = Mock()
            mock_builder.compile.return_value = mock_compiled
            
            with patch.object(builder, '_get_node_function') as mock_get_node:
                mock_get_node.return_value = Mock()
                
                graph = builder.build_graph(config)
                
                # 验证图被构建
                assert graph == mock_compiled
                
                # 验证节点被添加
                assert mock_builder.add_node.call_count == 3
                
                # 验证边被添加
                assert mock_builder.add_edge.call_count >= 2
                assert mock_builder.add_conditional_edges.call_count == 2
    
    def test_mixed_edge_types(self):
        """测试混合边类型"""
        builder = UnifiedGraphBuilder(
            route_function_config_dir="configs/edges"
        )
        
        config = GraphConfig(
            name="mixed_edges_test",
            description="混合边类型测试"
        )
        
        # 添加节点
        config.nodes["start"] = NodeConfig(
            name="start",
            function_name="llm_node"
        )
        config.nodes["process"] = NodeConfig(
            name="process",
            function_name="tool_node"
        )
        config.nodes["end"] = NodeConfig(
            name="end",
            function_name="llm_node"
        )
        
        # 混合边类型
        config.edges.append(EdgeConfig(
            from_node="__start__",
            to_node="start",
            type=EdgeType.SIMPLE
        ))
        
        # 灵活条件边
        config.edges.append(EdgeConfig(
            from_node="start",
            to_node="",
            type=EdgeType.CONDITIONAL,
            route_function="has_tool_calls",
            route_parameters={},
            path_map={
                "continue": "process",
                "end": "end"
            }
        ))
        
        # 传统条件边（兼容性）
        config.edges.append(EdgeConfig(
            from_node="process",
            to_node="",
            type=EdgeType.CONDITIONAL,
            condition="has_errors",
            path_map={
                "error": "end",
                "continue": "end"
            }
        ))
        
        config.entry_point = "start"
        
        # 模拟构建
        with patch('src.infrastructure.graph.builder.StateGraph') as mock_state_graph:
            mock_builder = Mock()
            mock_state_graph.return_value = mock_builder
            
            with patch.object(builder, '_get_node_function') as mock_get_node:
                with patch.object(builder, '_get_condition_function') as mock_get_condition:
                    mock_get_node.return_value = Mock()
                    mock_get_node.return_value = Mock()
                    
                    graph = builder.build_graph(config)
                    
                    # 验证不同类型的边都被处理
                    assert mock_builder.add_edge.call_count >= 1
                    assert mock_builder.add_conditional_edges.call_count >= 2


if __name__ == "__main__":
    pytest.main([__file__])