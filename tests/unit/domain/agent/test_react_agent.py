"""ReAct Agent单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.domain.agent import ReActAgent, AgentConfig
from src.domain.agent.state import AgentState
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
            current_task="Calculate 2+2"
        )
        
        # 模拟LLM响应 - 推理步骤
        mock_reasoning_response = Mock()
        mock_reasoning_response.content = "I need to use the calculator tool to add 2 and 2."
        
        # 模拟LLM响应 - 行动决策（工具调用）
        mock_action_response = Mock()
        mock_action_response.content = '{"action": "tool_call", "tool_call": "calculator[2, 2]"}'
        
        # 设置LLM客户端的响应
        self.mock_llm_client.generate_async = AsyncMock(side_effect=[
            mock_reasoning_response, 
            mock_action_response
        ])
        
        # 模拟工具执行结果
        mock_tool_result = ToolResult(
            success=True,
            output="4",
            error=None,
            tool_name="calculator",
            metadata={}
        )
        self.mock_tool_executor.execute_async = AsyncMock(return_value=mock_tool_result)

        # 执行Agent
        result_state = await self.react_agent.execute(input_state, {"max_iterations": 1})

        # 验证LLM被调用
        assert self.mock_llm_client.generate_async.called
        assert self.mock_llm_client.generate_async.call_count == 2
        assert self.mock_tool_executor.execute_async.called
        
        # 验证状态更新
        assert len(result_state.messages) == 2  # 推理和观察
        assert result_state.iteration_count == 1
        assert "Thought: I need to use the calculator tool to add 2 and 2." in result_state.messages[0].content
        assert "Action: calculator[2, 2]" in result_state.messages[1].content
        assert "Observation: 4" in result_state.messages[1].content
    
    async def test_execute_with_final_answer(self):
        """测试执行包含最终答案的场景"""
        # 准备输入状态
        input_state = AgentState(
            current_task="What is 2+2?"
        )
        
        # 模拟LLM响应 - 推理步骤
        mock_reasoning_response = Mock()
        mock_reasoning_response.content = "I need to calculate 2+2."
        
        # 模拟LLM响应 - 行动决策（最终答案）
        mock_action_response = Mock()
        mock_action_response.content = '{"action": "final_answer", "answer": "The result of 2+2 is 4."}'
        
        # 设置LLM客户端的响应
        self.mock_llm_client.generate_async = AsyncMock(side_effect=[
            mock_reasoning_response, 
            mock_action_response
        ])

        # 执行Agent
        result_state = await self.react_agent.execute(input_state, {"max_iterations": 1})

        # 验证LLM被调用
        assert self.mock_llm_client.generate_async.called
        assert self.mock_llm_client.generate_async.call_count == 2
        
        # 验证状态更新
        assert len(result_state.messages) == 2  # 推理和最终答案
        assert "Thought: I need to calculate 2+2." in result_state.messages[0].content
        assert "The result of 2+2 is 4." in result_state.messages[1].content
    
    async def test_execute_with_tool_error(self):
        """测试执行时工具出错的场景"""
        # 准备输入状态
        input_state = AgentState(
            current_task="Calculate 2/0"
        )
        
        # 模拟LLM响应 - 推理步骤
        mock_reasoning_response = Mock()
        mock_reasoning_response.content = "I need to use the calculator tool to divide 2 by 0."
        
        # 模拟LLM响应 - 行动决策（工具调用）
        mock_action_response = Mock()
        mock_action_response.content = '{"action": "tool_call", "tool_call": "calculator[2, 0]"}'
        
        # 设置LLM客户端的响应
        self.mock_llm_client.generate_async = AsyncMock(side_effect=[
            mock_reasoning_response, 
            mock_action_response
        ])

        # 模拟工具执行错误
        mock_tool_result = ToolResult(
            success=False,
            output=None,
            error="Division by zero error",
            tool_name="calculator",
            metadata={}
        )
        self.mock_tool_executor.execute_async = AsyncMock(return_value=mock_tool_result)

        # 执行Agent
        result_state = await self.react_agent.execute(input_state, {"max_iterations": 1})

        # 验证工具被调用
        assert self.mock_tool_executor.execute_async.called
        
        # 验证状态更新包含错误信息 - 检查状态中的tool_results列表
        assert len(result_state.tool_results) > 0
        assert result_state.tool_results[-1].tool_name == "calculator"
        assert result_state.tool_results[-1].success is False
        assert result_state.tool_results[-1].error == "Division by zero error"
        
        # 也验证errors列表，因为我们的实现可能同时添加了错误信息
        assert len(result_state.errors) > 0
        assert "tool_execution_error" in [error["type"] for error in result_state.errors if "tool" in error.get("type", "")]
    
    def test_can_handle_returns_true(self):
        """测试can_handle方法返回True"""
        state = AgentState(current_task="Test task")
        assert self.react_agent.can_handle(state) is True
    
    def test_get_capabilities(self):
        """测试获取Agent能力列表"""
        capabilities = self.react_agent.get_capabilities()
        assert "react_algorithm" in capabilities
        assert capabilities["react_algorithm"] is True
        assert "reasoning" in capabilities["supported_tasks"]
        assert "tool_execution" in capabilities["supported_tasks"]