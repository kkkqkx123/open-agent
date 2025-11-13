"""图构建器单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call, AsyncMock
from typing import Any, Dict, Optional
from pathlib import Path
import tempfile
import yaml

from src.infrastructure.graph.builder import (
    INodeExecutor,
    GraphBuilder
)
from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.states import WorkflowState
from src.infrastructure.graph.registry import NodeRegistry


class TestINodeExecutor:
    """节点执行器接口测试"""
    
    def test_interface_methods(self) -> None:
        """测试接口方法定义"""
        # 确保接口是抽象的
        with pytest.raises(TypeError):
            INodeExecutor()  # type: ignore
    
    def test_execute_method_signature(self) -> None:
        """测试execute方法签名"""
        # 检查方法签名
        assert hasattr(INodeExecutor, 'execute')
        method = INodeExecutor.execute
        assert method.__isabstractmethod__  # type: ignore


class TestGraphBuilder:
    """图构建器测试"""
    
    @pytest.fixture
    def mock_registry(self) -> Mock:
        """模拟节点注册表"""
        return Mock(spec=NodeRegistry)
    
    @pytest.fixture
    def builder(self, mock_registry: Mock) -> GraphBuilder:
        """创建图构建器实例"""
        return GraphBuilder(mock_registry)
    
    @pytest.fixture
    def sample_config(self) -> GraphConfig:
        # 创建状态配置
        from src.infrastructure.graph.config import GraphStateConfig, StateFieldConfig
        import uuid
        
        # 为每个测试生成唯一的状态类名，避免Channel冲突
        unique_state_name = f"TestState_{uuid.uuid4().hex[:8]}"
        state_config = GraphStateConfig(
            name=unique_state_name,
            fields={
                "input": StateFieldConfig(type="str")
            }
        )
        
        # 创建节点配置
        nodes = {
            "start": NodeConfig(
                name="start",
                function_name="llm_node",
                config={"model": "gpt-3.5-turbo"}
            ),
            "end": NodeConfig(
                name="end",
                function_name="analysis_node",
                config={"type": "summary"}
            )
        }
        
        # 创建边配置
        edges = [
            EdgeConfig(
                from_node="start",
                to_node="end",
                type=EdgeType.SIMPLE
            )
        ]
        
        return GraphConfig(
            name="test_graph",
            description="测试图",
            state_schema=state_config,
            nodes=nodes,
            edges=edges,
            entry_point="start"
        )
    
    def test_init(self, mock_registry: Mock) -> None:
        """测试初始化"""
        builder = GraphBuilder(mock_registry)
        assert builder.node_registry == mock_registry
        assert builder.template_registry is None
        assert isinstance(builder._checkpointer_cache, dict)
    
    def test_init_with_defaults(self) -> None:
        """测试使用默认值初始化"""
        builder = GraphBuilder()
        assert builder.node_registry is not None
        assert isinstance(builder.node_registry, NodeRegistry)
    
    def test_build_graph_success(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试成功构建图"""
        # 执行
        result = builder.build_graph(sample_config)

        # 验证
        # 由于实际返回的是 CompiledStateGraph 对象，我们验证它不为 None 即可
        assert result is not None
        # 由于 StateGraph 是在方法内部导入的，我们无法直接 mock，所以只验证结果不为 None
    
    def test_build_graph_validation_error(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试配置验证失败"""
        # 配置验证返回错误
        sample_config.validate = Mock(return_value=["验证错误1", "验证错误2"])  # type: ignore
        
        # 验证异常
        with pytest.raises(ValueError, match="图配置验证失败"):
            builder.build_graph(sample_config)
    
    def test_add_nodes(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试添加节点"""
        # 创建模拟构建器
        mock_builder = Mock()
        
        # 模拟节点函数
        mock_node_func = Mock()
        builder._get_node_function = Mock(return_value=mock_node_func)  # type: ignore
        
        # 执行
        builder._add_nodes(mock_builder, sample_config, None)
        
        # 验证
        for node_name in sample_config.nodes:
            mock_builder.add_node.assert_any_call(node_name, mock_node_func)
    
    def test_add_nodes_missing_function(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试添加节点时缺少函数"""
        # 创建模拟构建器
        mock_builder = Mock()
        
        # 模拟节点函数返回None
        builder._get_node_function = Mock(return_value=None)  # type: ignore
        
        # 执行
        builder._add_nodes(mock_builder, sample_config, None)
        
        # 验证没有调用add_node
        mock_builder.add_node.assert_not_called()
    
    def test_add_edges(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试添加边"""
        # 创建模拟构建器
        mock_builder = Mock()
        
        # 模拟条件函数
        mock_condition_func = Mock()
        builder._get_condition_function = Mock(return_value=mock_condition_func)  # type: ignore
        
        # 执行
        builder._add_edges(mock_builder, sample_config)
        
        # 验证
        for edge in sample_config.edges:
            if edge.type == EdgeType.SIMPLE:
                mock_builder.add_edge.assert_any_call(edge.from_node, edge.to_node)
    
    def test_add_edges_to_end(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试添加到END节点的边"""
        # 修改配置，添加到END的边
        sample_config.edges[0].to_node = "__end__"
        
        # 创建模拟构建器
        mock_builder = Mock()
        
        # 执行
        builder._add_edges(mock_builder, sample_config)
        
        # 验证
        mock_builder.add_edge.assert_called()
    
    def test_add_conditional_edges(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试添加条件边"""
        # 修改配置为条件边
        sample_config.edges[0].type = EdgeType.CONDITIONAL
        sample_config.edges[0].condition = "test_condition"
        
        # 创建模拟构建器
        mock_builder = Mock()
        
        # 模拟条件函数
        mock_condition_func = Mock()
        builder._get_condition_function = Mock(return_value=mock_condition_func)
        
        # 执行
        builder._add_edges(mock_builder, sample_config)
        
        # 验证
        mock_builder.add_conditional_edges.assert_called_once_with(
            sample_config.edges[0].from_node,
            mock_condition_func
        )
    
    def test_get_node_function_from_registry(self, builder: GraphBuilder, mock_registry: Mock) -> None:
        """测试从注册表获取节点函数"""
        # 创建节点配置
        node_config = NodeConfig(
            name="test_node",
            function_name="registered_node"
        )
        
        # 模拟节点类
        mock_node_class = Mock()
        mock_node_instance = Mock()
        mock_node_instance.execute = Mock()
        mock_node_class.return_value = mock_node_instance
        
        # 配置注册表
        mock_registry.get_node_class.return_value = mock_node_class
        
        # 执行
        result = builder._get_node_function(node_config, None)
        
        # 验证
        # 由于返回的是适配器包装的函数，我们需要验证它是一个可调用对象
        assert callable(result)
        mock_registry.get_node_class.assert_called_once_with("registered_node")
    
    def test_get_node_function_from_template(self, builder: GraphBuilder) -> None:
        """测试从模板获取节点函数"""
        # 创建模拟模板注册表
        mock_template_registry = Mock()
        builder.template_registry = mock_template_registry
        
        # 创建节点配置
        node_config = NodeConfig(
            name="test_node",
            function_name="template_node"
        )
        
        # 模拟模板
        mock_template = Mock()
        mock_template.get_node_function.return_value = lambda: Mock()
        mock_template_registry.get_template.return_value = mock_template
        
        # 配置注册表返回None
        builder.node_registry.get_node_class.side_effect = ValueError("节点不存在")  # type: ignore
        
        # 执行
        result = builder._get_node_function(node_config)
        
        # 验证
        assert result == mock_template.get_node_function.return_value
        mock_template_registry.get_template.assert_called_once_with("template_node")
    
    def test_get_node_function_builtin(self, builder: GraphBuilder) -> None:
        """测试获取内置节点函数"""
        # 创建节点配置
        node_config = NodeConfig(
            name="test_node",
            function_name="llm_node"
        )
        
        # 配置注册表返回None
        builder.node_registry.get_node_class.side_effect = ValueError("节点不存在")  # type: ignore
        
        # 执行
        result = builder._get_node_function(node_config)
        
        # 验证
        assert result is not None
        assert callable(result)
    
    def test_get_condition_function(self, builder: GraphBuilder) -> None:
        """测试获取条件函数"""
        # 执行
        result = builder._get_condition_function("has_tool_calls")
        
        # 验证
        assert result is not None
        assert callable(result)
    
    def test_get_builtin_function(self, builder: GraphBuilder) -> None:
        """测试获取内置函数"""
        # 测试所有内置函数
        builtin_functions = ["llm_node", "tool_node", "analysis_node", "condition_node"]
        
        for func_name in builtin_functions:
            result = builder._get_builtin_function(func_name)
            assert result is not None
            assert callable(result)
        
        # 测试未知函数
        result = builder._get_builtin_function("unknown_function")
        assert result is None
    
    def test_get_builtin_condition(self, builder: GraphBuilder) -> None:
        """测试获取内置条件"""
        # 测试所有内置条件
        builtin_conditions = ["has_tool_calls", "needs_more_info", "is_complete"]
        
        for condition_name in builtin_conditions:
            result = builder._get_builtin_condition(condition_name)
            assert result is not None
            assert callable(result)
        
        # 测试未知条件
        result = builder._get_builtin_condition("unknown_condition")
        assert result is None
    
    def test_get_checkpointer_memory(self, builder: GraphBuilder) -> None:
        """测试获取内存检查点"""
        # 修改配置
        config = Mock()
        config.checkpointer = "memory"
        
        # 执行
        result = builder._get_checkpointer(config)
        
        # 验证
        assert result is not None
    
    def test_get_checkpointer_sqlite(self, builder: GraphBuilder) -> None:
        """测试获取SQLite检查点"""
        # 修改配置
        config = Mock()
        config.checkpointer = "sqlite:/tmp/test.db"
        
        # 执行
        result = builder._get_checkpointer(config)
        
        # 验证
        assert result is not None
    
    def test_get_checkpointer_cached(self, builder: GraphBuilder) -> None:
        """测试缓存的检查点"""
        # 修改配置
        config = Mock()
        config.checkpointer = "memory"
        
        # 第一次调用
        result1 = builder._get_checkpointer(config)
        
        # 第二次调用应该返回缓存的结果
        result2 = builder._get_checkpointer(config)
        
        # 验证
        assert result1 is result2
    
    def test_create_llm_node(self, builder: GraphBuilder) -> None:
        """测试创建LLM节点"""
        state: dict[str, Any] = {"messages": []}
        result = builder._create_llm_node(state)  # type: ignore
        
        # 验证
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert result["messages"][0]["role"] == "assistant"
    
    def test_create_tool_node(self, builder: GraphBuilder) -> None:
        """测试创建工具节点"""
        state: dict[str, Any] = {"tool_calls": [{"name": "test_tool", "args": {}}]}
        result = builder._create_tool_node(state)  # type: ignore
        
        # 验证
        assert "tool_results" in result
        assert len(result["tool_results"]) > 0
    
    def test_create_analysis_node(self, builder: GraphBuilder) -> None:
        """测试创建分析节点"""
        state: dict[str, Any] = {}
        result = builder._create_analysis_node(state)  # type: ignore
        
        # 验证
        assert "analysis" in result
        assert result["analysis"] == "分析结果"
    
    def test_create_condition_node(self, builder: GraphBuilder) -> None:
        """测试创建条件节点"""
        state: dict[str, Any] = {}
        result = builder._create_condition_node(state)  # type: ignore
        
        # 验证
        assert "condition_result" in result
        assert result["condition_result"] is True
    
    def test_condition_has_tool_calls(self, builder: GraphBuilder) -> None:
        """测试条件：有工具调用"""
        state = {"tool_calls": [{"name": "test_tool"}]}
        result = builder._condition_has_tool_calls(state)  # type: ignore
        assert result == "tool_node"

        state = {"tool_calls": []}
        result = builder._condition_has_tool_calls(state)  # type: ignore
        assert result == "llm_node"
    
    def test_condition_needs_more_info(self, builder: GraphBuilder) -> None:
        """测试条件：需要更多信息"""
        state: dict[str, Any] = {"analysis": None}
        result = builder._condition_needs_more_info(state)  # type: ignore
        assert result == "analysis_node"

        state = {"analysis": "已完成分析"}
        result = builder._condition_needs_more_info(state)  # type: ignore
        assert result == "end"
    
    def test_condition_is_complete(self, builder: GraphBuilder) -> None:
        """测试条件：是否完成"""
        state = {"complete": True}
        result = builder._condition_is_complete(state)  # type: ignore
        assert result == "end"

        state = {"complete": False}
        result = builder._condition_is_complete(state)  # type: ignore
        assert result == "continue"
    
    