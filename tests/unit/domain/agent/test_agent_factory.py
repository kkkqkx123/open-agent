"""AgentFactory测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Union
from src.domain.agent.factory import AgentFactory
from src.domain.agent.config import AgentConfig
from src.domain.agent.interfaces import IAgent
from src.domain.agent.state import AgentState
from src.application.workflow.state import WorkflowState
from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.tools.manager import IToolManager


class MockAgent(IAgent):
    """模拟Agent类"""
    
    def __init__(self, config, llm_client, tool_executor, event_manager=None):
        self.config = config
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.event_manager = event_manager

    @property
    def name(self) -> str:
        """Agent名称"""
        return self.config.name

    @property
    def description(self) -> str:
        """Agent描述"""
        return getattr(self.config, 'description', 'Mock Agent')

    async def execute(self, state: Union[AgentState, WorkflowState], config: dict) -> Union[AgentState, WorkflowState]:
        return state
    
    def get_capabilities(self) -> dict:
        return {"name": self.config.name, "type": "mock"}
    
    def validate_state(self, state: AgentState) -> bool:
        return True

    def can_handle(self, state: AgentState) -> bool:
        return True
    
    def get_available_tools(self) -> list:
        return self.config.tools


@pytest.fixture
def mock_llm_factory():
    """模拟LLM工厂"""
    factory = Mock()
    client = Mock(spec=ILLMClient)
    factory.create_client.return_value = client
    return factory


@pytest.fixture
def mock_tool_manager():
    """模拟工具管理器"""
    manager = Mock(spec=IToolManager)
    return manager


@pytest.fixture
def agent_factory(mock_llm_factory, mock_tool_manager):
    """创建AgentFactory实例"""
    return AgentFactory(mock_llm_factory, mock_tool_manager)


def test_agent_factory_init(agent_factory, mock_llm_factory, mock_tool_manager):
    """测试AgentFactory初始化"""
    assert agent_factory.llm_factory == mock_llm_factory
    assert agent_factory.tool_manager == mock_tool_manager
    assert "react" in agent_factory.get_supported_types()
    assert "plan_execute" in agent_factory.get_supported_types()


def test_create_agent_success(agent_factory, mock_llm_factory, mock_tool_manager):
    """测试成功创建Agent"""
    # 注册MockAgent类型
    agent_factory.register_agent_type("mock", MockAgent)
    
    # 创建Agent配置
    agent_config = {
        "agent_type": "mock",
        "name": "test_agent",
        "description": "Test agent",
        "llm": "test_llm",
        "tools": ["tool1", "tool2"]
    }
    
    # 创建Agent
    agent = agent_factory.create_agent(agent_config)
    
    # 验证结果
    assert isinstance(agent, MockAgent)
    assert agent.config.name == "test_agent"
    assert agent.config.llm == "test_llm"
    assert agent.config.tools == ["tool1", "tool2"]
    
    # 验证LLM客户端被正确获取
    mock_llm_factory.create_client.assert_called_once_with({"model_name": "test_llm"})


def test_create_agent_invalid_type(agent_factory):
    """测试创建不支持的Agent类型"""
    agent_config = {
        "agent_type": "unknown_type",
        "name": "test_agent"
    }
    
    with pytest.raises(ValueError, match="不支持的Agent类型"):
        agent_factory.create_agent(agent_config)


def test_create_agent_missing_required_fields(agent_factory):
    """测试缺少必需字段"""
    # 缺少agent_type
    agent_config = {
        "name": "test_agent"
    }
    
    with pytest.raises(ValueError, match="缺少必需字段: agent_type"):
        agent_factory.create_agent(agent_config)
    
    # 缺少name
    agent_config = {
        "agent_type": "react"
    }
    
    with pytest.raises(ValueError, match="缺少必需字段: name"):
        agent_factory.create_agent(agent_config)


def test_register_agent_type(agent_factory):
    """测试注册Agent类型"""
    # 注册新类型
    agent_factory.register_agent_type("custom", MockAgent)
    
    # 验证类型已注册
    assert "custom" in agent_factory.get_supported_types()
    
    # 尝试重复注册
    with pytest.raises(ValueError, match="Agent类型已存在"):
        agent_factory.register_agent_type("custom", MockAgent)


def test_unregister_agent_type(agent_factory):
    """测试注销Agent类型"""
    # 注销现有类型
    agent_factory.unregister_agent_type("react")
    
    # 验证类型已注销
    assert "react" not in agent_factory.get_supported_types()
    
    # 注销不存在的类型应该不会报错
    agent_factory.unregister_agent_type("nonexistent")


def test_create_agent_from_config(agent_factory):
    """测试从AgentConfig对象创建Agent"""
    # 注册MockAgent类型
    agent_factory.register_agent_type("mock", MockAgent)
    
    # 创建AgentConfig对象
    config = AgentConfig(
        agent_type="mock",
        name="test_agent",
        llm="test_llm",
        tools=["tool1"]
    )
    
    # 创建Agent
    agent = agent_factory.create_agent_from_config(config)
    
    # 验证结果
    assert isinstance(agent, MockAgent)
    assert agent.config.name == "test_agent"


def test_get_cache_info(agent_factory):
    """测试获取缓存信息"""
    cache_info = agent_factory.get_cache_info()
    
    assert "cache_size" in cache_info
    assert "cached_agents" in cache_info
    assert cache_info["cache_size"] == 0
    assert cache_info["cached_agents"] == []


def test_clear_cache(agent_factory):
    """测试清除缓存"""
    # 清除缓存应该不会报错
    agent_factory.clear_cache()


@pytest.mark.asyncio
async def test_agent_execution(agent_factory, mock_llm_factory, mock_tool_manager):
    """测试Agent执行"""
    # 注册MockAgent类型
    agent_factory.register_agent_type("mock", MockAgent)
    
    # 创建Agent
    agent_config = {
        "agent_type": "mock",
        "name": "test_agent",
        "llm": "test_llm"
    }
    agent = agent_factory.create_agent(agent_config)
    
    # 创建测试状态
    state = WorkflowState()
    
    # 执行Agent
    result = await agent.execute(state, {})
    
    # 验证结果
    assert result == state