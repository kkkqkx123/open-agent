"""Agent执行节点单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.application.workflow.nodes.agent_execution_node import agent_execution_node
from src.domain.prompts.agent_state import AgentState
from src.domain.agent import IAgentManager


class TestAgentExecutionNode:
    """Agent执行节点测试类"""
    
    @patch('src.application.workflow.nodes.agent_execution_node.get_service')
    async def test_agent_execution_node_success(self, mock_get_service):
        """测试Agent执行节点成功执行"""
        # 创建模拟的AgentManager
        mock_agent_manager = Mock(spec=IAgentManager)
        mock_agent_manager.execute_agent = AsyncMock(return_value=AgentState())
        
        # 配置get_service返回模拟的AgentManager
        mock_get_service.return_value = mock_agent_manager
        
        # 准备输入状态
        input_state = AgentState(
            context={
                "current_agent_id": "test_agent"
            }
        )
        
        # 执行节点
        result_state = await agent_execution_node(input_state)
        
        # 验证AgentManager被调用
        mock_get_service.assert_called_once_with(IAgentManager)
        mock_agent_manager.execute_agent.assert_called_once_with("test_agent", input_state)
        
        # 验证返回状态
        assert isinstance(result_state, AgentState)
    
    @patch('src.application.workflow.nodes.agent_execution_node.get_service')
    async def test_agent_execution_node_with_default_agent(self, mock_get_service):
        """测试使用默认Agent的执行节点"""
        # 创建模拟的AgentManager
        mock_agent_manager = Mock(spec=IAgentManager)
        mock_agent_manager.execute_agent = AsyncMock(return_value=AgentState())
        
        # 配置get_service返回模拟的AgentManager
        mock_get_service.return_value = mock_agent_manager
        
        # 准备输入状态（没有指定Agent ID）
        input_state = AgentState(
            context={}
        )
        
        # 执行节点
        result_state = await agent_execution_node(input_state)
        
        # 验证使用默认Agent ID
        mock_agent_manager.execute_agent.assert_called_once_with("default_agent", input_state)
    
    @patch('src.application.workflow.nodes.agent_execution_node.get_service')
    async def test_agent_execution_node_with_agent_manager_error(self, mock_get_service):
        """测试AgentManager执行错误时的处理"""
        # 创建模拟的AgentManager
        mock_agent_manager = Mock(spec=IAgentManager)
        mock_agent_manager.execute_agent = AsyncMock(side_effect=Exception("Agent execution failed"))
        
        # 配置get_service返回模拟的AgentManager
        mock_get_service.return_value = mock_agent_manager
        
        # 准备输入状态
        input_state = AgentState(
            context={
                "current_agent_id": "test_agent"
            }
        )
        
        # 执行节点并捕获异常
        with pytest.raises(Exception, match="Agent execution failed"):
            await agent_execution_node(input_state)
        
        # 验证AgentManager被调用
        mock_get_service.assert_called_once_with(IAgentManager)
        mock_agent_manager.execute_agent.assert_called_once_with("test_agent", input_state)
    
    @patch('src.application.workflow.nodes.agent_execution_node.get_service')
    async def test_agent_execution_node_with_empty_context(self, mock_get_service):
        """测试上下文为空时的处理"""
        # 创建模拟的AgentManager
        mock_agent_manager = Mock(spec=IAgentManager)
        mock_agent_manager.execute_agent = AsyncMock(return_value=AgentState())
        
        # 配置get_service返回模拟的AgentManager
        mock_get_service.return_value = mock_agent_manager
        
        # 准备输入状态（上下文为None）
        input_state = AgentState()
        input_state.context = None
        
        # 执行节点
        result_state = await agent_execution_node(input_state)
        
        # 验证使用默认Agent ID
        mock_agent_manager.execute_agent.assert_called_once_with("default_agent", input_state)
    
    @patch('src.application.workflow.nodes.agent_execution_node.get_service')
    async def test_agent_execution_node_returns_updated_state(self, mock_get_service):
        """测试节点返回更新后的状态"""
        # 创建模拟的AgentManager
        mock_agent_manager = Mock(spec=IAgentManager)
        
        # 创建一个更新后的状态
        updated_state = AgentState(
            agent_id="test_agent",
            current_task="Calculate 2+2",
            memory=[]
        )
        mock_agent_manager.execute_agent = AsyncMock(return_value=updated_state)
        
        # 配置get_service返回模拟的AgentManager
        mock_get_service.return_value = mock_agent_manager
        
        # 准备输入状态
        input_state = AgentState(
            context={
                "current_agent_id": "test_agent"
            }
        )
        
        # 执行节点
        result_state = await agent_execution_node(input_state)
        
        # 验证返回的是更新后的状态
        assert result_state.agent_id == "test_agent"
        assert result_state.current_task == "Calculate 2+2"
        assert result_state is updated_state  # 应该是同一个对象引用