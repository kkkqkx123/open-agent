"""工作流构建器测试"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import yaml

from src.application.workflow.builder import WorkflowBuilder
from src.domain.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from src.application.workflow.registry import NodeRegistry, BaseNode, NodeExecutionResult
from src.domain.workflow.state import WorkflowState


class MockNode(BaseNode):
    """模拟节点类"""
    
    def __init__(self, node_type: str = "mock_node"):
        self._node_type = node_type
    
    @property
    def node_type(self) -> str:
        return self._node_type
    
    def execute(self, state: WorkflowState, config: dict) -> NodeExecutionResult:
        return NodeExecutionResult(state=state)
    
    def get_config_schema(self) -> dict:
        return {"type": "object", "properties": {}}


class TestWorkflowBuilder:
    """工作流构建器测试"""

    def test_init_with_default_registry(self):
        """测试使用默认注册表初始化"""
        builder = WorkflowBuilder()
        
        assert builder.node_registry is not None
        assert builder.workflow_configs == {}

    def test_init_with_custom_registry(self):
        """测试使用自定义注册表初始化"""
        registry = NodeRegistry()
        builder = WorkflowBuilder(registry)
        
        assert builder.node_registry is registry

    def test_load_workflow_config_file_not_found(self):
        """测试加载不存在的配置文件"""
        builder = WorkflowBuilder()
        
        with pytest.raises(FileNotFoundError):
            builder.load_workflow_config("nonexistent.yaml")

    def test_load_workflow_config_valid(self):
        """测试加载有效的工作流配置"""
        builder = WorkflowBuilder()
        
        # 创建临时配置文件
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "nodes": {
                "start": {
                    "type": "mock_node"
                },
                "analyze": {
                    "type": "mock_node"
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "analyze",
                    "type": "simple"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 注册模拟节点
            builder.node_registry.register_node(MockNode)
            
            # 加载配置
            workflow_config = builder.load_workflow_config(temp_path)
            
            assert workflow_config.name == "test_workflow"
            assert workflow_config.description == "测试工作流"
            assert "analyze" in workflow_config.nodes
            assert len(workflow_config.edges) == 1
            
            # 检查是否缓存了配置
            assert "test_workflow" in builder.workflow_configs
        finally:
            Path(temp_path).unlink()

    def test_load_workflow_config_invalid(self):
        """测试加载无效的工作流配置"""
        builder = WorkflowBuilder()
        
        # 创建无效配置文件（缺少必需字段）
        config_data = {
            "name": "",
            "description": "测试工作流"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="工作流配置验证失败"):
                builder.load_workflow_config(temp_path)
        finally:
            Path(temp_path).unlink()

    @patch('langgraph.graph.StateGraph')
    def test_build_workflow_without_langgraph(self, mock_state_graph):
        """测试在没有LangGraph的情况下构建工作流"""
        # 模拟LangGraph不可用
        mock_state_graph.side_effect = ImportError("LangGraph未安装")
        
        builder = WorkflowBuilder()
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        with pytest.raises(ImportError, match="LangGraph未安装"):
            builder.build_workflow(config)

    @patch('langgraph.graph.StateGraph')
    def test_build_workflow_valid(self, mock_state_graph_class):
        """测试构建有效的工作流"""
        # 模拟LangGraph的StateGraph
        mock_workflow = Mock()
        mock_state_graph_class.return_value = mock_workflow
        
        # 使用独立的节点注册表
        registry = NodeRegistry()
        builder = WorkflowBuilder(registry)
        
        # 注册模拟节点
        builder.node_registry.register_node(MockNode)
        
        # 创建工作流配置
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "start": NodeConfig(type="mock_node"),
                "analyze": NodeConfig(type="mock_node")
            },
            edges=[
                EdgeConfig(
                    from_node="start",
                    to_node="analyze",
                    type=EdgeType.SIMPLE
                )
            ],
            entry_point="start"
        )
        
        # 构建工作流
        result = builder.build_workflow(config)
        
        # 验证调用
        mock_state_graph_class.assert_called_once_with(WorkflowState)
        assert mock_workflow.add_node.call_count == 2  # 应该添加两个节点
        mock_workflow.add_edge.assert_called_once()
        mock_workflow.set_entry_point.assert_called_once_with("start")
        mock_workflow.compile.assert_called_once()
        
        assert result == mock_workflow.compile.return_value

    @patch('langgraph.graph.StateGraph')
    def test_build_workflow_with_conditional_edge(self, mock_state_graph_class):
        """测试构建包含条件边的工作流"""
        # 模拟LangGraph的StateGraph
        mock_workflow = Mock()
        mock_state_graph_class.return_value = mock_workflow
        
        # 使用独立的节点注册表
        registry = NodeRegistry()
        builder = WorkflowBuilder(registry)
        
        # 注册模拟节点
        builder.node_registry.register_node(MockNode)
        
        # 创建工作流配置
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "start": NodeConfig(type="mock_node"),
                "analyze": NodeConfig(type="mock_node"),
                "execute_tool": NodeConfig(type="mock_node")
            },
            edges=[
                EdgeConfig(
                    from_node="start",
                    to_node="analyze",
                    type=EdgeType.SIMPLE
                ),
                EdgeConfig(
                    from_node="analyze",
                    to_node="execute_tool",
                    type=EdgeType.CONDITIONAL,
                    condition="has_tool_calls"
                )
            ],
            entry_point="start"
        )
        
        # 构建工作流
        builder.build_workflow(config)
        
        # 验证调用
        mock_workflow.add_conditional_edges.assert_called_once()

    @patch('langgraph.graph.StateGraph')
    def test_build_workflow_unknown_node_type(self, mock_state_graph_class):
        """测试构建包含未知节点类型的工作流"""
        mock_workflow = Mock()
        mock_state_graph_class.return_value = mock_workflow
        
        # 使用独立的节点注册表
        registry = NodeRegistry()
        builder = WorkflowBuilder(registry)
        
        # 创建工作流配置（包含未注册的节点类型）
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "analyze": NodeConfig(type="unknown_node")
            }
        )
        
        with pytest.raises(ValueError, match="注册节点 'analyze' 失败"):
            builder.build_workflow(config)

    @patch('langgraph.graph.StateGraph')
    def test_build_workflow_conditional_edge_without_condition(self, mock_state_graph_class):
        """测试构建缺少条件的条件边"""
        mock_workflow = Mock()
        mock_state_graph_class.return_value = mock_workflow
        
        # 使用独立的节点注册表
        registry = NodeRegistry()
        builder = WorkflowBuilder(registry)
        
        # 注册模拟节点
        builder.node_registry.register_node(MockNode)
        
        # 创建工作流配置（条件边缺少条件）
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "start": NodeConfig(type="mock_node"),
                "analyze": NodeConfig(type="mock_node"),
                "execute_tool": NodeConfig(type="mock_node")
            },
            edges=[
                EdgeConfig(
                    from_node="start",
                    to_node="analyze",
                    type=EdgeType.SIMPLE
                ),
                EdgeConfig(
                    from_node="analyze",
                    to_node="execute_tool",
                    type=EdgeType.CONDITIONAL,
                    condition=None
                )
            ],
            entry_point="start"
        )
        
        with pytest.raises(ValueError, match="缺少条件表达式"):
            builder.build_workflow(config)

    @patch('langgraph.graph.StateGraph')
    def test_determine_entry_point_from_config(self, mock_state_graph_class):
        """测试从配置确定入口点"""
        mock_workflow = Mock()
        mock_state_graph_class.return_value = mock_workflow
        
        # 使用独立的节点注册表
        registry = NodeRegistry()
        builder = WorkflowBuilder(registry)
        
        # 注册模拟节点
        builder.node_registry.register_node(MockNode)
        
        # 创建工作流配置（指定入口点）
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "analyze": NodeConfig(type="mock_node")
            },
            entry_point="analyze"
        )
        
        builder.build_workflow(config)
        
        mock_workflow.set_entry_point.assert_called_once_with("analyze")

    @patch('langgraph.graph.StateGraph')
    def test_determine_entry_point_auto_detect(self, mock_state_graph_class):
        """测试自动检测入口点"""
        mock_workflow = Mock()
        mock_state_graph_class.return_value = mock_workflow
        
        # 使用独立的节点注册表
        registry = NodeRegistry()
        builder = WorkflowBuilder(registry)
        
        # 注册模拟节点
        builder.node_registry.register_node(MockNode)
        
        # 创建工作流配置（未指定入口点）
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "start": NodeConfig(type="mock_node"),
                "analyze": NodeConfig(type="mock_node"),
                "execute_tool": NodeConfig(type="mock_node")
            },
            edges=[
                EdgeConfig(
                    from_node="start",
                    to_node="analyze",
                    type=EdgeType.SIMPLE
                ),
                EdgeConfig(
                    from_node="analyze",
                    to_node="execute_tool",
                    type=EdgeType.SIMPLE
                )
            ]
        )
        
        builder.build_workflow(config)
        
        # start节点没有入边，应该被选为入口点
        mock_workflow.set_entry_point.assert_called_once_with("start")

    def test_has_tool_call_condition(self):
        """测试has_tool_call条件函数"""
        builder = WorkflowBuilder()
        
        # 测试有工具调用的情况
        state_with_tool_calls = WorkflowState()
        mock_message = Mock()
        mock_message.tool_calls = [{"name": "test_tool"}]
        state_with_tool_calls.messages = [mock_message]
        
        assert builder._has_tool_call_condition(state_with_tool_calls) is True
        
        # 测试没有工具调用的情况
        state_without_tool_calls = WorkflowState()
        mock_message_no_tools = Mock()
        mock_message_no_tools.tool_calls = None
        state_without_tool_calls.messages = [mock_message_no_tools]
        
        assert builder._has_tool_call_condition(state_without_tool_calls) is False

    def test_no_tool_call_condition(self):
        """测试no_tool_call条件函数"""
        builder = WorkflowBuilder()
        
        # 测试有工具调用的情况
        state_with_tool_calls = WorkflowState()
        mock_message = Mock()
        mock_message.tool_calls = [{"name": "test_tool"}]
        state_with_tool_calls.messages = [mock_message]
        
        assert builder._no_tool_call_condition(state_with_tool_calls) is False
        
        # 测试没有工具调用的情况
        state_without_tool_calls = WorkflowState()
        mock_message_no_tools = Mock()
        mock_message_no_tools.tool_calls = None
        state_without_tool_calls.messages = [mock_message_no_tools]
        
        assert builder._no_tool_call_condition(state_without_tool_calls) is True

    def test_has_tool_result_condition(self):
        """测试has_tool_result条件函数"""
        builder = WorkflowBuilder()
        
        # 测试有工具结果的情况
        state_with_results = WorkflowState()
        mock_result = Mock()
        state_with_results.tool_results = [mock_result]
        
        assert builder._has_tool_result_condition(state_with_results) is True
        
        # 测试没有工具结果的情况
        state_without_results = WorkflowState()
        state_without_results.tool_results = []
        
        assert builder._has_tool_result_condition(state_without_results) is False

    def test_max_iterations_reached_condition(self):
        """测试max_iterations_reached条件函数"""
        builder = WorkflowBuilder()
        
        # 测试达到最大迭代次数
        state_max_reached = WorkflowState()
        state_max_reached.iteration_count = 10
        state_max_reached.max_iterations = 10
        
        assert builder._max_iterations_reached_condition(state_max_reached) is True
        
        # 测试未达到最大迭代次数
        state_not_max = WorkflowState()
        state_not_max.iteration_count = 5
        state_not_max.max_iterations = 10
        
        assert builder._max_iterations_reached_condition(state_not_max) is False

    def test_register_condition_function(self):
        """测试注册自定义条件函数"""
        builder = WorkflowBuilder()
        
        def custom_condition(state, params=""):
            return True
        
        builder.register_condition_function("custom", custom_condition)
        
        assert "custom" in builder._condition_functions
        assert builder._condition_functions["custom"] is custom_condition

    def test_list_available_nodes(self):
        """测试列出可用节点类型"""
        builder = WorkflowBuilder()
        
        # 创建一个新的模拟节点类，避免名称冲突
        class NewMockNode(BaseNode):
            @property
            def node_type(self) -> str:
                return "new_mock_node"
            
            def execute(self, state: WorkflowState, config: dict) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict:
                return {"type": "object", "properties": {}}
        
        # 注册节点
        builder.node_registry.register_node(NewMockNode)
        
        nodes = builder.list_available_nodes()
        
        assert "new_mock_node" in nodes

    def test_get_workflow_config(self):
        """测试获取工作流配置"""
        builder = WorkflowBuilder()
        
        # 创建并缓存配置
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        builder.workflow_configs["test_workflow"] = config
        
        retrieved_config = builder.get_workflow_config("test_workflow")
        
        assert retrieved_config is config

    def test_get_workflow_config_nonexistent(self):
        """测试获取不存在的工作流配置"""
        builder = WorkflowBuilder()
        
        config = builder.get_workflow_config("nonexistent")
        
        assert config is None

    def test_clear_cache(self):
        """测试清除缓存"""
        builder = WorkflowBuilder()
        
        # 添加配置到缓存
        builder.workflow_configs["test"] = Mock()
        
        assert len(builder.workflow_configs) == 1
        
        builder.clear_cache()
        
        assert len(builder.workflow_configs) == 0
