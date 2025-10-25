"""Plan-Execute Agent单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.domain.agent import PlanExecuteAgent, AgentConfig
from src.domain.prompts.agent_state import AgentState
from src.domain.tools.base import ToolResult


class TestPlanExecuteAgent:
    """PlanExecuteAgent测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        self.mock_llm_client = Mock()
        self.mock_tool_executor = Mock()
        self.mock_event_manager = Mock()
        
        # 创建配置
        config = AgentConfig(
            name="test_plan_execute_agent",
            agent_type="plan_execute",
            system_prompt="Test system prompt for Plan-Execute agent"
        )
        
        self.plan_execute_agent = PlanExecuteAgent(
            config=config,
            llm_client=self.mock_llm_client,
            tool_executor=self.mock_tool_executor,
            event_manager=self.mock_event_manager
        )
    
    async def test_execute_with_plan_generation(self):
        """测试执行包含计划生成的场景"""
        # 准备输入状态
        input_state = AgentState(
            current_task="Write a short story about a robot learning to paint",
            memory=[]
        )
        
        # 模拟LLM响应 - 计划生成
        mock_plan_response = Mock()
        mock_plan_response.content = """
Plan:
1. Think about the theme of the story
2. Create main characters
3. Develop plot outline
4. Write the story
5. Review and refine
"""
        self.mock_llm_client.generate_response_async = AsyncMock(return_value=mock_plan_response)
        
        # 执行Agent
        result_state = await self.plan_execute_agent.execute(input_state)
        
        # 验证LLM被调用
        assert self.mock_llm_client.generate_response_async.called
        
        # 验证状态更新
        assert result_state.context.get("current_plan") is not None
        assert len(result_state.task_history) > 0
    
    async def test_execute_with_plan_execution(self):
        """测试执行计划步骤的场景"""
        # 准备输入状态，包含已有计划
        input_state = AgentState(
            current_task="Write a short story about a robot learning to paint",
            memory=[],
            context={
                "current_plan": [
                    "Think about the theme of the story",
                    "Create main characters",
                    "Develop plot outline"
                ],
                "current_step_index": 0
            }
        )
        
        # 模拟LLM响应 - 执行步骤
        mock_step_response = Mock()
        mock_step_response.content = "The theme explores creativity and self-expression in artificial beings."
        self.mock_llm_client.generate_response_async = AsyncMock(return_value=mock_step_response)
        
        # 执行Agent
        result_state = await self.plan_execute_agent.execute(input_state)
        
        # 验证状态更新
        assert result_state.context.get("current_step_index") == 1
        assert len(result_state.memory) > 0
    
    async def test_execute_with_tool_in_step(self):
        """测试在计划步骤中使用工具的场景"""
        # 准备输入状态
        input_state = AgentState(
            current_task="Calculate the area of a circle with radius 5",
            memory=[],
            context={
                "current_plan": [
                    "Use calculator to compute π * r^2 where r = 5",
                    "Report the result"
                ],
                "current_step_index": 0
            }
        )
        
        # 模拟LLM响应 - 需要使用工具
        mock_step_response = Mock()
        mock_step_response.content = "Action: calculator[{'operation': 'multiply', 'operands': ['3.14159', '25']}]"
        self.mock_llm_client.generate_response_async = AsyncMock(return_value=mock_step_response)
        
        # 模拟工具执行结果
        mock_tool_result = ToolResult(
            tool_name="calculator",
            result="78.54",
            error=None,
            metadata={}
        )
        self.mock_tool_executor.execute_tool_async = AsyncMock(return_value=mock_tool_result)
        
        # 执行Agent
        result_state = await self.plan_execute_agent.execute(input_state)
        
        # 验证工具被调用
        assert self.mock_tool_executor.execute_tool_async.called
        
        # 验证状态更新
        assert result_state.context.get("current_step_index") == 1
        assert len(result_state.tool_results) > 0
    
    async def test_execute_plan_completion(self):
        """测试计划完成的场景"""
        # 准备输入状态，已经是最后一个步骤
        input_state = AgentState(
            current_task="Summarize the findings",
            memory=[],
            context={
                "current_plan": [
                    "Summarize the findings"
                ],
                "current_step_index": 0
            }
        )
        
        # 模拟LLM响应 - 最终总结
        mock_final_response = Mock()
        mock_final_response.content = "Final Answer: The project was completed successfully with all objectives met."
        self.mock_llm_client.generate_response_async = AsyncMock(return_value=mock_final_response)
        
        # 执行Agent
        result_state = await self.plan_execute_agent.execute(input_state)
        
        # 验证状态更新
        assert result_state.context.get("current_plan") is None  # 计划完成应清除
        assert "Final Answer" in result_state.memory[-1].content
    
    def test_can_handle_returns_true(self):
        """测试can_handle方法返回True"""
        state = AgentState()
        assert self.plan_execute_agent.can_handle(state) is True
    
    def test_get_capabilities(self):
        """测试获取Agent能力列表"""
        capabilities = self.plan_execute_agent.get_capabilities()
        assert "plan_execute_algorithm" in capabilities
        assert "planning" in capabilities
        assert "step_execution" in capabilities