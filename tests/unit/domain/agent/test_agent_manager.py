"""Agent管理器单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.domain.agent import AgentManager, IAgent, AgentConfig
from src.domain.agent.state import AgentState


class TestAgentManager:
    """AgentManager测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        self.mock_llm_client = Mock()
        self.mock_tool_executor = Mock()
        self.agent_manager = AgentManager(self.mock_llm_client, self.mock_tool_executor)
    
    def test_create_agent_with_valid_type(self):
        """测试创建有效类型的Agent"""
        # 创建一个模拟的Agent类
        class MockAgent(IAgent):
            def __init__(self, config, llm_client, tool_executor, event_manager=None):
                self.config = config
                self.llm_client = llm_client
                self.tool_executor = tool_executor
            
            async def execute(self, state, config):
                return state

            def can_handle(self, state):
                return True

            def get_capabilities(self):
                return {}

            def validate_state(self, state):
                return True

            def get_available_tools(self):
                return []
        
        # 注册Agent类型
        self.agent_manager.register_agent_type("mock_agent", MockAgent)
        
        # 创建配置
        config = AgentConfig(
            name="test_agent",
            agent_type="mock_agent",
            system_prompt="Test system prompt"
        )
        
        # 创建Agent
        agent = self.agent_manager.create_agent(config)
        
        # 验证Agent被正确创建
        assert isinstance(agent, MockAgent)
        assert agent.config.name == "test_agent"
    
    def test_create_agent_with_invalid_type_raises_error(self):
        """测试创建无效类型Agent时抛出错误"""
        config = AgentConfig(
            name="test_agent",
            agent_type="invalid_agent_type",
            system_prompt="Test system prompt"
        )
        
        with pytest.raises(ValueError, match="Unknown agent type: invalid_agent_type"):
            self.agent_manager.create_agent(config)
    
    def test_register_agent_type(self):
        """测试注册Agent类型"""
        mock_agent_class = Mock(spec=IAgent)

        self.agent_manager.register_agent_type("test_type", mock_agent_class)  # type: ignore

        assert self.agent_manager.agent_types["test_type"] == mock_agent_class
    
    async def test_execute_agent(self):
        """测试执行Agent"""
        # 创建模拟Agent
        mock_agent = Mock(spec=IAgent)
        mock_agent.execute = AsyncMock(return_value=AgentState())
        
        # 注册Agent
        self.agent_manager.register_agent("test_agent", mock_agent)
        
        # 准备输入状态
        input_state = AgentState()
        
        # 执行Agent
        result = await self.agent_manager.execute_agent("test_agent", input_state)  # type: ignore
        
        # 验证Agent被执行
        mock_agent.execute.assert_called_once_with(input_state)
        assert result is not None
    
    def test_execute_nonexistent_agent_raises_error(self):
        """测试执行不存在的Agent时抛出错误"""
        input_state = AgentState()
        
        with pytest.raises(ValueError, match="Agent not found: nonexistent_agent"):
            import asyncio
            # 使用asyncio.run来运行异步方法
            asyncio.run(self.agent_manager.execute_agent("nonexistent_agent", input_state))  # type: ignore
    
    def test_register_agent(self):
        """测试注册Agent实例"""
        mock_agent = Mock(spec=IAgent)
        
        self.agent_manager.register_agent("test_agent", mock_agent)
        
        assert self.agent_manager.agents["test_agent"] is mock_agent