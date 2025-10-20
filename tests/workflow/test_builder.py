"""工作流构建器测试

测试工作流构建器的功能，包括工作流加载、构建和执行。
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typing import List, Dict, Any

from src.workflow.builder import WorkflowBuilder
from src.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from src.workflow.registry import NodeRegistry, BaseNode, NodeExecutionResult
from src.prompts.agent_state import AgentState


class MockNode(BaseNode):
    """模拟节点类"""
    
    def __init__(self, node_type: str = "mock_node"):
        self._node_type = node_type
    
    @property
    def node_type(self) -> str:
        return self._node_type
    
    def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
        """模拟执行"""
        return NodeExecutionResult(
            state=state,
            next_node=None,
            metadata={"mock": True}
        )
    
    def get_config_schema(self) -> dict:
        """获取配置模式"""
        return {
            "type": "object",
            "properties": {
                "mock_param": {"type": "string"}
            }
        }


class TestWorkflowBuilder:
    """工作流构建器测试类"""

    def setup_method(self) -> None:
        """测试前设置"""
        self.registry = NodeRegistry()
        self.registry.register_node(MockNode)
        self.builder = WorkflowBuilder(self.registry)

    def test_builder_initialization(self) -> None:
        """测试构建器初始化"""
        builder = WorkflowBuilder()
        assert builder.node_registry is not None
        assert isinstance(builder.workflow_configs, dict)
        assert isinstance(builder._condition_functions, dict)

    def test_load_workflow_config(self, tmp_path: Path) -> None:
        """测试加载工作流配置"""
        # 创建测试配置文件
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0",
            "nodes": {
                "analyze": {
                    "type": "mock_node",
                    "config": {"mock_param": "test_value"}
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
        
        config_file = tmp_path / "test_workflow.yaml"
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置
        config = self.builder.load_workflow_config(str(config_file))
        
        assert config.name == "test_workflow"
        assert config.description == "测试工作流"
        assert "analyze" in config.nodes
        assert config.nodes["analyze"].type == "mock_node"
        assert len(config.edges) == 1

    def test_load_workflow_config_file_not_found(self) -> None:
        """测试加载不存在的配置文件"""
        with pytest.raises(FileNotFoundError):
            self.builder.load_workflow_config("nonexistent.yaml")

    def test_load_workflow_config_invalid_yaml(self, tmp_path: Path) -> None:
        """测试加载无效YAML配置文件"""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content:")
        
        with pytest.raises(Exception):
            self.builder.load_workflow_config(str(config_file))

    def test_build_workflow(self) -> None:
        """测试构建工作流"""
        # 创建测试配置
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        config.nodes["analyze"] = NodeConfig(
            type="mock_node",
            config={"mock_param": "test_value"}
        )
        
        config.edges.append(EdgeConfig(
            from_node="start",
            to_node="analyze",
            type=EdgeType.SIMPLE
        ))
        
        # 构建工作流
        with patch('src.workflow.builder.StateGraph') as mock_state_graph:
            mock_workflow = Mock()
            mock_state_graph.return_value = mock_workflow
            
            result = self.builder.build_workflow(config)
            
            # 验证StateGraph被正确创建
            mock_state_graph.assert_called_once_with(AgentState)
            
            # 验证节点被添加
            mock_workflow.add_node.assert_called()
            
            # 验证边被添加
            mock_workflow.add_edge.assert_called()
            
            # 验证入口点被设置
            mock_workflow.set_entry_point.assert_called()
            
            # 验证工作流被编译
            mock_workflow.compile.assert_called_once()
            
            assert result is not None

    def test_build_workflow_with_conditional_edge(self) -> None:
        """测试构建带条件边的工作流"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        config.nodes["analyze"] = NodeConfig(
            type="mock_node",
            config={}
        )
        
        config.nodes["execute_tool"] = NodeConfig(
            type="mock_node",
            config={}
        )
        
        config.edges.append(EdgeConfig(
            from_node="analyze",
            to_node="execute_tool",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls"
        ))
        
        with patch('src.workflow.builder.StateGraph') as mock_state_graph:
            mock_workflow = Mock()
            mock_state_graph.return_value = mock_workflow
            
            self.builder.build_workflow(config)
            
            # 验证条件边被添加
            mock_workflow.add_conditional_edges.assert_called()

    def test_register_nodes(self) -> None:
        """测试节点注册"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        config.nodes["analyze"] = NodeConfig(
            type="mock_node",
            config={}
        )
        
        with patch('src.workflow.builder.StateGraph') as mock_state_graph:
            mock_workflow = Mock()
            mock_state_graph.return_value = mock_workflow
            
            self.builder._register_nodes(mock_workflow, config)
            
            # 验证节点被添加
            mock_workflow.add_node.assert_called_once()

    def test_register_nodes_unknown_type(self) -> None:
        """测试注册未知类型的节点"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        config.nodes["unknown"] = NodeConfig(
            type="unknown_node",
            config={}
        )
        
        with patch('src.workflow.builder.StateGraph') as mock_state_graph:
            mock_workflow = Mock()
            mock_state_graph.return_value = mock_workflow
            
            with pytest.raises(ValueError, match="注册节点 'unknown' 失败"):
                self.builder._register_nodes(mock_workflow, config)

    def test_add_simple_edge(self) -> None:
        """测试添加简单边"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        edge_config = EdgeConfig(
            from_node="start",
            to_node="analyze",
            type=EdgeType.SIMPLE
        )
        
        with patch('src.workflow.builder.StateGraph') as mock_state_graph:
            mock_workflow = Mock()
            mock_state_graph.return_value = mock_workflow
            
            self.builder._add_simple_edge(mock_workflow, edge_config)
            
            # 验证边被添加
            mock_workflow.add_edge.assert_called_once_with("start", "analyze")

    def test_add_conditional_edge(self) -> None:
        """测试添加条件边"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        edge_config = EdgeConfig(
            from_node="analyze",
            to_node="execute_tool",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls"
        )
        
        with patch('src.workflow.builder.StateGraph') as mock_state_graph:
            mock_workflow = Mock()
            mock_state_graph.return_value = mock_workflow
            
            self.builder._add_conditional_edge(mock_workflow, edge_config)
            
            # 验证条件边被添加
            mock_workflow.add_conditional_edges.assert_called_once()

    def test_add_conditional_edge_no_condition(self) -> None:
        """测试添加没有条件的条件边"""
        edge_config = EdgeConfig(
            from_node="analyze",
            to_node="execute_tool",
            type=EdgeType.CONDITIONAL
        )
        
        with patch('src.workflow.builder.StateGraph') as mock_state_graph:
            mock_workflow = Mock()
            mock_state_graph.return_value = mock_workflow
            
            with pytest.raises(ValueError, match="缺少条件表达式"):
                self.builder._add_conditional_edge(mock_workflow, edge_config)

    def test_create_condition_function_builtin(self) -> None:
        """测试创建内置条件函数"""
        # 测试内置条件
        func = self.builder._create_condition_function("has_tool_calls")
        assert callable(func)
        
        func = self.builder._create_condition_function("no_tool_calls")
        assert callable(func)
        
        func = self.builder._create_condition_function("max_iterations_reached")
        assert callable(func)

    def test_create_condition_function_custom(self) -> None:
        """测试创建自定义条件函数"""
        func = self.builder._create_condition_function("len(state.messages) > 5")
        assert callable(func)
        
        # 测试自定义条件执行
        state = AgentState()
        for i in range(10):
            state.add_message(f"Message {i}")
        
        result = func(state)
        assert result is True

    def test_create_condition_function_with_params(self) -> None:
        """测试创建带参数的条件函数"""
        func = self.builder._create_condition_function("message_contains:test")
        assert callable(func)
        
        # 测试带参数的条件执行
        state = AgentState()
        from src.prompts.agent_state import HumanMessage
        state.add_message(HumanMessage(content="This is a test message"))
        
        result = func(state)
        assert result is True

    def test_determine_entry_point(self) -> None:
        """测试确定入口点"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        # 测试配置中指定了入口点
        config.entry_point = "custom_entry"
        entry_point = self.builder._determine_entry_point(config)
        assert entry_point == "custom_entry"
        
        # 测试没有指定入口点，自动确定
        config.entry_point = None
        config.nodes["node1"] = NodeConfig(type="mock_node", config={})
        config.nodes["node2"] = NodeConfig(type="mock_node", config={})
        
        # 添加边，使node1成为入口点
        config.edges.append(EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.SIMPLE
        ))
        
        entry_point = self.builder._determine_entry_point(config)
        assert entry_point == "node1"

    def test_has_tool_call_condition(self) -> None:
        """测试工具调用条件"""
        state = AgentState()
        
        # 测试没有工具调用
        result = self.builder._has_tool_call_condition(state)
        assert result is False
        
        # 测试有工具调用
        # 创建模拟消息对象，具有tool_calls属性
        class MockMessage:
            def __init__(self, content: str):
                self.content = content
                self.tool_calls: List[Dict[str, Any]] = []

        message = MockMessage("Test message")
        message.tool_calls = [{"name": "test_tool", "args": {}}]  # type: ignore
        state.add_message(message)
        
        result = self.builder._has_tool_call_condition(state)
        assert result is True

    def test_max_iterations_reached_condition(self) -> None:
        """测试最大迭代次数条件"""
        state = AgentState()
        state.max_iterations = 5
        state.iteration_count = 3
        
        # 测试未达到最大迭代次数
        result = self.builder._max_iterations_reached_condition(state)
        assert result is False
        
        # 测试达到最大迭代次数
        state.iteration_count = 5
        result = self.builder._max_iterations_reached_condition(state)
        assert result is True

    def test_register_condition_function(self) -> None:
        """测试注册自定义条件函数"""
        def custom_condition(state: AgentState) -> bool:
            return len(state.messages) > 10
        
        self.builder.register_condition_function("custom", custom_condition)
        
        assert "custom" in self.builder._condition_functions
        assert self.builder._condition_functions["custom"] is custom_condition

    def test_list_available_nodes(self) -> None:
        """测试列出可用节点"""
        nodes = self.builder.list_available_nodes()
        assert "mock_node" in nodes

    def test_get_workflow_config(self) -> None:
        """测试获取工作流配置"""
        # 首先加载一个配置
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        self.builder.workflow_configs["test_workflow"] = config
        
        # 获取配置
        retrieved_config = self.builder.get_workflow_config("test_workflow")
        assert retrieved_config is not None
        assert retrieved_config.name == "test_workflow"
        
        # 获取不存在的配置
        nonexistent_config = self.builder.get_workflow_config("nonexistent")
        assert nonexistent_config is None

    def test_clear_cache(self) -> None:
        """测试清除缓存"""
        # 添加一些配置到缓存
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        self.builder.workflow_configs["test_workflow"] = config
        
        # 清除缓存
        self.builder.clear_cache()
        
        # 验证缓存已清除
        assert len(self.builder.workflow_configs) == 0