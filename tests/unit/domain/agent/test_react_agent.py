"""ReAct Agent单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.domain.agent import ReActAgent, AgentConfig
from src.domain.prompts.agent_state import AgentState
from src.domain.tools.base import ToolResult


class TestReActAgent:
    """ReActAgent测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        self.mock_llm_client = Mock()
        self.mock_tool_executor = Mock()
        self.mock_event_manager = Mock()
        
        # 创建配置
        config = AgentConfig(
            name="test_react_agent",
            agent_type="react",
            system_prompt="Test system prompt for ReAct agent"
        )
        
        self.react_agent = ReActAgent(
            config=config,
            llm_client=self.mock_llm_client,
            tool_executor=self.mock_tool_executor,
            event_manager=self.mock_event_manager
        )
    
    async def test_execute_with_reasoning_and_action(self):
        """测试执行包含推理和行动的场景"""
        # 准备输入状态
        input_state = AgentState(
            current_task="Calculate 2+2",
            memory=[]
        )
        
        # 模拟LLM响应 - 推理步骤
        mock_reasoning_response = Mock()
        mock_reasoning_response.content = "I need to use the calculator tool to add 2 and 2."
        self.mock_llm_client.generate_response_async = AsyncMock(return_value=mock_reasoning_response)
        
        # 模拟工具执行结果
        mock_tool_result = ToolResult(
        success=True,
        output="4",
        error=None,
        tool_name="calculator",
            metadata={}
        )
        self.mock_tool_executor.execute_tool_async = AsyncMock(return_value=mock_tool_result)
        
        # 执行Agent
        result_state = await self.react_agent.execute(input_state)
        
        # 验证LLM被调用
        assert self.mock_llm_client.generate_response_async.called
        assert self.mock_tool_executor.execute_tool_async.called
        
        # 验证状态更新
        assert len(result_state.memory) > 0
        assert result_state.iteration_count == 1
    
    async def test_execute_with_final_answer(self):
        """测试执行包含最终答案的场景"""
        # 准备输入状态
        input_state = AgentState(
            current_task="What is 2+2?",
            memory=[]
        )
        
        # 模拟LLM响应 - 最终答案
        mock_final_response = Mock()
        mock_final_response.content = "Final Answer: The result of 2+2 is 4."
        self.mock_llm_client.generate_response_async = AsyncMock(return_value=mock_final_response)
        
        # 执行Agent
        result_state = await self.react_agent.execute(input_state)
        
        # 验证LLM被调用
        assert self.mock_llm_client.generate_response_async.called
        
        # 验证状态更新
        assert len(result_state.memory) > 0
        assert "Final Answer" in result_state.memory[-1].content
    
    async def test_execute_with_tool_error(self):
        """测试执行时工具出错的场景"""
        # 准备输入状态
        input_state = AgentState(
            current_task="Calculate 2/0",
            memory=[]
        )
        
        # 模拟LLM响应
        mock_reasoning_response = Mock()
        mock_reasoning_response.content = "I need to use the calculator tool to divide 2 by 0."
        self.mock_llm_client.generate_response_async = AsyncMock(return_value=mock_reasoning_response)
        
        # 模拟工具执行错误
        mock_tool_result = ToolResult(
        success=False,
        output=None,
        error="Division by zero error",
        tool_name="calculator",
            metadata={}
        )
        self.mock_tool_executor.execute_tool_async = AsyncMock(return_value=mock_tool_result)
        
        # 执行Agent
        result_state = await self.react_agent.execute(input_state)
        
        # 验证状态更新包含错误信息
        assert len(result_state.errors) > 0
        assert "Division by zero error" in str(result_state.errors[-1])
    
    def test_can_handle_returns_true(self):
        """测试can_handle方法返回True"""
        state = AgentState()
        assert self.react_agent.can_handle(state) is True
    
    def test_get_capabilities(self):
        """测试获取Agent能力列表"""
        capabilities = self.react_agent.get_capabilities()
        assert "react_algorithm" in capabilities
        assert "reasoning" in capabilities
        assert "tool_execution" in capabilities