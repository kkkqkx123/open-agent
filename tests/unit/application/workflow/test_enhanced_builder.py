"""WorkflowBuilder测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.application.workflow.builder import WorkflowBuilder, AgentNodeExecutor
from src.domain.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from src.domain.workflow.state import WorkflowState, BaseMessage, MessageRole
from src.domain.agent.interfaces import IAgent, IAgentFactory
from src.application.workflow.templates.react_template import ReActWorkflowTemplate


class MockAgent(IAgent):
    """模拟Agent类"""
    
    def __init__(self, config, llm_client, tool_executor, event_manager=None):
        self.config = config
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.event_manager = event_manager
    
    async def execute(self, state: WorkflowState, config: dict) -> WorkflowState:
        # 模拟执行逻辑
        state.add_message(BaseMessage(
            content=f"Agent {self.config.name} 执行完成",
            role=MessageRole.AI
        ))
        return state
    
    def get_capabilities(self) -> dict:
        return {"name": self.config.name, "type": "mock"}
    
    def validate_state(self, state: WorkflowState) -> bool:
        return True
    
    def can_handle(self, state: WorkflowState) -> bool:
        return True
    
    def get_available_tools(self) -> list:
        return self.config.tools


@pytest.fixture
def mock_agent_factory():
    """模拟Agent工厂"""
    factory = Mock(spec=IAgentFactory)
    
    def create_agent(config):
        return MockAgent(
            config=config,
            llm_client=Mock(),
            tool_executor=Mock(),
            event_manager=Mock()
        )
    
    factory.create_agent.side_effect = create_agent
    return factory


@pytest.fixture
def enhanced_builder(mock_agent_factory):
    """创建WorkflowBuilder实例"""
    return WorkflowBuilder(agent_factory=mock_agent_factory)


def test_enhanced_builder_init(enhanced_builder):
    """测试WorkflowBuilder初始化"""
    assert enhanced_builder.agent_factory is not None
    assert enhanced_builder.node_registry is not None
    assert isinstance(enhanced_builder.workflow_templates, dict)
    assert isinstance(enhanced_builder._condition_functions, dict)
    assert isinstance(enhanced_builder._node_executors, dict)


def test_build_from_config_dict(enhanced_builder):
    """测试从配置字典构建工作流"""
    config_dict = {
        "name": "test_workflow",
        "description": "测试工作流",
        "nodes": {
            "test_node": {
                "type": "agent_node",
                "config": {
                    "agent_config": {
                        "agent_type": "react",
                        "name": "test_agent",
                        "llm": "test_llm",
                        "tools": ["tool1"]
                    }
                }
            }
        },
        "edges": [],
        "entry_point": "test_node"
    }
    
    # 构建工作流
    workflow = enhanced_builder.build_from_config(config_dict)
    
    # 验证结果
    assert workflow is not None
    assert "test_node" in enhanced_builder._node_executors


def test_build_from_config_object(enhanced_builder):
    """测试从WorkflowConfig对象构建工作流"""
    config = WorkflowConfig(
        name="test_workflow",
        description="测试工作流",
        nodes={
            "test_node": NodeConfig(
                type="agent_node",
                config={
                    "agent_config": {
                        "agent_type": "react",
                        "name": "test_agent",
                        "llm": "test_llm"
                    }
                }
            )
        },
        edges=[],
        entry_point="test_node"
    )
    
    # 构建工作流
    workflow = enhanced_builder.build_from_config(config)
    
    # 验证结果
    assert workflow is not None


def test_build_from_template(enhanced_builder):
    """测试从模板构建工作流"""
    # 注册测试模板
    test_template = ReActWorkflowTemplate()
    enhanced_builder.register_template("test_react", test_template)
    
    # 从模板构建工作流
    config = {
        "llm_client": "test_llm",
        "max_iterations": 5,
        "tools": ["calculator", "search"]
    }
    
    workflow = enhanced_builder.build_from_template("test_react", config)
    
    # 验证结果
    assert workflow is not None


def test_register_agent_node(enhanced_builder, mock_agent_factory):
    """测试注册Agent节点"""
    agent_config = {
        "agent_type": "react",
        "name": "test_agent",
        "llm": "test_llm",
        "tools": ["tool1"]
    }
    
    # 注册Agent节点
    enhanced_builder.register_agent_node("test_agent_node", agent_config)
    
    # 验证节点已注册
    assert "test_agent_node" in enhanced_builder._node_executors
    assert isinstance(enhanced_builder._node_executors["test_agent_node"], AgentNodeExecutor)


def test_register_condition_function(enhanced_builder):
    """测试注册条件函数"""
    def custom_condition(state):
        return True
    
    # 注册条件函数
    enhanced_builder.register_condition_function("custom", custom_condition)
    
    # 验证函数已注册
    assert "custom" in enhanced_builder._condition_functions
    assert enhanced_builder._condition_functions["custom"] == custom_condition


def test_builtin_conditions(enhanced_builder):
    """测试内置条件函数"""
    # 测试has_tool_call条件
    state = WorkflowState()
    state.add_message(BaseMessage(
        content="需要调用工具",
        role=MessageRole.AI
    ))
    
    has_tool_call = enhanced_builder._has_tool_call_condition(state)
    assert isinstance(has_tool_call, bool)
    
    # 测试no_tool_call条件
    no_tool_call = enhanced_builder._no_tool_call_condition(state)
    assert isinstance(no_tool_call, bool)


def test_template_integration(enhanced_builder):
    """测试模板集成"""
    # 检查是否自动加载了模板
    templates = enhanced_builder.list_available_templates()
    
    # 应该包含内置模板
    assert "react" in templates
    assert "enhanced_react" in templates
    assert "plan_execute" in templates
    assert "collaborative_plan_execute" in templates


def test_get_template_info(enhanced_builder):
    """测试获取模板信息"""
    info = enhanced_builder.get_template_info("react")
    
    assert info is not None
    assert "name" in info
    assert "description" in info
    assert "parameters" in info
    assert info["name"] == "react"


def test_agent_node_executor():
    """测试Agent节点执行器"""
    # 创建模拟Agent
    agent_config = {
        "agent_type": "react",
        "name": "test_agent",
        "llm": "test_llm"
    }
    agent = MockAgent(
        config=agent_config,
        llm_client=Mock(),
        tool_executor=Mock(),
        event_manager=Mock()
    )
    
    # 创建执行器
    executor = AgentNodeExecutor(agent)
    
    # 测试执行
    state = WorkflowState()
    result_state = executor.execute(state, {})
    
    # 验证结果
    assert result_state is not None
    assert len(result_state.messages) > 0
    assert "test_agent 执行完成" in result_state.messages[-1].content


def test_error_handling(enhanced_builder):
    """测试错误处理"""
    # 测试无效配置
    with pytest.raises(ValueError):
        enhanced_builder.build_from_config("invalid_config")
    
    # 测试不存在的模板
    with pytest.raises(ValueError):
        enhanced_builder.build_from_template("nonexistent_template", {})
    
    # 测试无效Agent配置
    with pytest.raises(ValueError):
        enhanced_builder.register_agent_node("test", "invalid_config")


def test_config_validation(enhanced_builder):
    """测试配置验证"""
    # 创建无效配置（缺少必需字段）
    invalid_config = {
        "description": "测试工作流"
        # 缺少name字段
    }
    
    with pytest.raises(ValueError):
        enhanced_builder.build_from_config(invalid_config)


@pytest.mark.asyncio
async def test_workflow_execution(enhanced_builder):
    """测试工作流执行"""
    # 创建简单的工作流配置
    config = {
        "name": "test_execution",
        "description": "测试执行",
        "nodes": {
            "start": {
                "type": "agent_node",
                "config": {
                    "agent_config": {
                        "agent_type": "react",
                        "name": "start_agent",
                        "llm": "test_llm"
                    }
                }
            }
        },
        "edges": [],
        "entry_point": "start"
    }
    
    # 构建工作流
    workflow = enhanced_builder.build_from_config(config)
    
    # 创建初始状态
    initial_state = WorkflowState()
    initial_state.add_message(BaseMessage(
        content="测试消息",
        role=MessageRole.HUMAN
    ))
    
    # 执行工作流（这里只是模拟，实际执行需要LangGraph）
    assert workflow is not None
    assert initial_state is not None