"""图构建器单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Any, Dict, Optional
from pathlib import Path
import tempfile
import yaml

from src.infrastructure.graph.builder import (
    INodeExecutor,
    AgentNodeExecutor,
    GraphBuilder,
    get_workflow_builder
)
from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.state import WorkflowState
from src.infrastructure.graph.registry import NodeRegistry
from src.domain.agent.interfaces import IAgent, IAgentFactory


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


class TestAgentNodeExecutor:
    """Agent节点执行器测试"""
    
    @pytest.fixture
    def mock_agent(self) -> Mock:
        """模拟Agent"""
        agent = Mock(spec=IAgent)
        return agent
    
    @pytest.fixture
    def executor(self, mock_agent: Mock) -> AgentNodeExecutor:
        """创建Agent节点执行器实例"""
        return AgentNodeExecutor(mock_agent)
    
    @pytest.fixture
    def sample_state(self) -> dict[str, Any]:
        """示例状态"""
        return {
            "messages": [{"role": "user", "content": "测试消息"}],
            "input": "测试输入",
            "output": None,
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False
        }
    
    @pytest.fixture
    def sample_config(self) -> dict[str, Any]:
        """示例配置"""
        return {
            "agent_id": "test_agent",
            "max_iterations": 5
        }
    
    def test_init(self, mock_agent: Mock) -> None:
        """测试初始化"""
        executor = AgentNodeExecutor(mock_agent)
        assert executor.agent == mock_agent
    
    @patch('src.infrastructure.graph.builder.asyncio.run')
    def test_execute_with_new_event_loop(self, mock_run: Mock, executor: AgentNodeExecutor, sample_state: dict[str, Any], sample_config: dict[str, Any]) -> None:
        """测试在新事件循环中执行"""
        # 配置模拟
        mock_run.return_value = sample_state
        
        # 模拟没有运行的事件循环
        with patch('src.infrastructure.graph.builder.asyncio.get_running_loop', side_effect=RuntimeError):
            result = executor.execute(sample_state, sample_config)  # type: ignore
        
        # 验证
        assert result == sample_state
        mock_run.assert_called_once()
    
    @patch('src.infrastructure.graph.builder.asyncio.new_event_loop')
    @patch('src.infrastructure.graph.builder.asyncio.set_event_loop')
    @patch('src.infrastructure.graph.builder.asyncio.run')
    def test_execute_in_main_thread(self, mock_run: Mock, mock_set_loop: Mock, mock_new_loop: Mock, executor: AgentNodeExecutor, sample_state: dict[str, Any], sample_config: dict[str, Any]) -> None:
        """测试在主线程中执行"""
        # 配置模拟
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_run.return_value = sample_state
        
        # 模拟在主线程中，但没有运行的事件循环
        with patch('src.infrastructure.graph.builder.threading.current_thread') as mock_thread:
            mock_thread.return_value = Mock()
            with patch('src.infrastructure.graph.builder.threading.main_thread', mock_thread.return_value):
                with patch('src.infrastructure.graph.builder.asyncio.get_running_loop', side_effect=RuntimeError):
                    result = executor.execute(sample_state, sample_config)  # type: ignore  # type: ignore
        
        # 验证
        assert result == sample_state
        mock_run.assert_called_once()
    
    @patch('src.infrastructure.graph.builder.concurrent.futures.ThreadPoolExecutor')
    @patch('src.infrastructure.graph.builder.asyncio.run')
    def test_execute_in_non_main_thread(self, mock_run: Mock, mock_executor: Mock, executor: AgentNodeExecutor, sample_state: dict[str, Any], sample_config: dict[str, Any]) -> None:
        """测试在非主线程中执行"""
        # 配置模拟
        mock_run.return_value = sample_state
        mock_thread = Mock()
        mock_future = Mock()
        mock_future.result.return_value = sample_state
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
        
        # 模拟在非主线程中
        with patch('src.infrastructure.graph.builder.threading.current_thread', return_value=mock_thread):
            with patch('src.infrastructure.graph.builder.threading.main_thread', return_value=Mock()):
                with patch('src.infrastructure.graph.builder.asyncio.get_running_loop', return_value=Mock()):
                    result = executor.execute(sample_state, sample_config)  # type: ignore  # type: ignore
        
        # 验证
        assert result == sample_state


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
        
        state_config = GraphStateConfig(
            name="TestState",
            fields={
                "messages": StateFieldConfig(type="List[str]"),
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
    
    @patch('src.infrastructure.graph.builder.LANGGRAPH_AVAILABLE', True)
    def test_build_graph_success(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试成功构建图"""
        # 模拟状态类
        mock_state_class = Mock()
        sample_config.get_state_class = Mock(return_value=mock_state_class)  # type: ignore
        
        # 执行
        result = builder.build_graph(sample_config)
        
        # 验证
        # 由于实际返回的是 CompiledStateGraph 对象，我们验证它不为 None 即可
        assert result is not None
        # 由于 StateGraph 是在方法内部导入的，我们无法直接 mock，所以只验证结果不为 None
    
    @patch('src.infrastructure.graph.builder.LANGGRAPH_AVAILABLE', False)
    def test_build_graph_langgraph_unavailable(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试LangGraph不可用时构建图"""
        result = builder.build_graph(sample_config)
        assert result is None
    
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
        builder._add_nodes(mock_builder, sample_config)
        
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
        builder._add_nodes(mock_builder, sample_config)
        
        # 验证没有调用add_node
        mock_builder.add_node.assert_not_called()
    
    @patch('src.infrastructure.graph.builder.LANGGRAPH_AVAILABLE', True)
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
    
    @patch('src.infrastructure.graph.builder.LANGGRAPH_AVAILABLE', True)
    def test_add_edges_to_end(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试添加到END节点的边"""
        # 修改配置，添加到END的边
        sample_config.edges[0].to_node = "__end__"
        
        # 创建模拟构建器
        mock_builder = Mock()
        
        # 执行
        builder._add_edges(mock_builder, sample_config)
        
        # 验证
        from src.infrastructure.graph.builder import END
        mock_builder.add_edge.assert_called_once_with(sample_config.edges[0].from_node, END)
    
    @patch('src.infrastructure.graph.builder.LANGGRAPH_AVAILABLE', True)
    def test_add_conditional_edges(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试添加条件边"""
        # 修改配置为条件边
        sample_config.edges[0].type = EdgeType.CONDITIONAL
        sample_config.edges[0].condition = "test_condition"
        
        # 创建模拟构建器
        mock_builder = Mock()
        
        # 模拟条件函数
        mock_condition_func = Mock()
        builder._get_condition_function = Mock(return_value=mock_condition_func)  # type: ignore
        
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
        result = builder._get_node_function(node_config)
        
        # 验证
        assert result == mock_node_instance.execute
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
        mock_template.get_node_function.return_value = Mock()
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
    
    def test_build_from_yaml(self, builder: GraphBuilder) -> None:
        """测试从YAML文件构建图"""
        # 创建临时YAML文件
        config_data = {
            "name": "test_graph",
            "description": "测试图",
            "state_schema": {
                "name": "TestState",
                "fields": {
                    "messages": {"type": "List[str]"}
                }
            },
            "nodes": {
                "start": {
                    "function": "llm_node",
                    "config": {"model": "gpt-3.5-turbo"}
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "end",
                    "type": "simple"
                }
            ],
            "entry_point": "start"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 模拟build_graph方法
            builder.build_graph = Mock(return_value=Mock())  # type: ignore
            
            # 执行
            result = builder.build_from_yaml(temp_path)
            
            # 验证
            assert result is not None
            builder.build_graph.assert_called_once()
            
            # 验证配置对象
            call_args = builder.build_graph.call_args[0][0]
            assert isinstance(call_args, GraphConfig)
            assert call_args.name == "test_graph"
            
        finally:
            # 清理临时文件
            Path(temp_path).unlink()
    
    def test_validate_config(self, builder: GraphBuilder, sample_config: GraphConfig) -> None:
        """测试验证配置"""
        # 配置验证返回空列表
        sample_config.validate = Mock(return_value=[])  # type: ignore
        
        # 执行
        result = builder.validate_config(sample_config)
        
        # 验证
        assert result == []
        sample_config.validate.assert_called_once()
    
    def test_load_workflow_config(self, builder: GraphBuilder) -> None:
        """测试加载工作流配置"""
        # 创建临时YAML文件
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "state_schema": {
                "name": "WorkflowState",
                "fields": {}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 执行
            result = builder.load_workflow_config(temp_path)
            
            # 验证
            assert isinstance(result, GraphConfig)
            assert result.name == "test_workflow"
            
        finally:
            # 清理临时文件
            Path(temp_path).unlink()


class TestGetWorkflowBuilder:
    """测试工作流构建器工厂函数"""
    
    def test_get_workflow_builder(self) -> None:
        """测试获取工作流构建器"""
        # 执行
        result = get_workflow_builder()
        
        # 验证
        assert isinstance(result, GraphBuilder)
    
    def test_get_workflow_builder_with_args(self) -> None:
        """测试带参数获取工作流构建器"""
        # 创建模拟注册表
        mock_registry = Mock(spec=NodeRegistry)
        
        # 执行
        result = get_workflow_builder(node_registry=mock_registry)
        
        # 验证
        assert isinstance(result, GraphBuilder)
        assert result.node_registry == mock_registry