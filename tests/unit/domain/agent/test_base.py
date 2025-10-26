"""Agent基类单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.domain.agent import BaseAgent, AgentConfig
from src.application.workflow.state import AgentState
from src.domain.tools.base import ToolResult


class TestBaseAgent:
    """BaseAgent测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        # 创建模拟依赖
        self.mock_llm_client = Mock()
        self.mock_tool_executor = Mock()
        self.mock_event_manager = Mock()
        
        # 创建配置
        config = AgentConfig(
            name="test_agent",
            agent_type="base",
            system_prompt="Test system prompt"
        )
        
        # 创建BaseAgent实例（通过子类实现，因为BaseAgent是抽象类）
        class ConcreteAgent(BaseAgent):
            async def execute(self, state, config):
                return state

            def can_handle(self, state):
                return True

            def get_capabilities(self):
                return {"base_capability": True}
        
        self.base_agent = ConcreteAgent(
            config=config,
            llm_client=self.mock_llm_client,
            tool_executor=self.mock_tool_executor,
            event_manager=self.mock_event_manager
        )
    
    def test_base_agent_initialization(self):
        """测试BaseAgent初始化"""
        assert self.base_agent.config.name == "test_agent"
        assert self.base_agent.llm_client == self.mock_llm_client
        assert self.base_agent.tool_executor == self.mock_tool_executor
        assert self.base_agent.event_manager == self.mock_event_manager
        assert self.base_agent.execution_stats["total_executions"] == 0
        assert self.base_agent.execution_stats["total_errors"] == 0
        assert self.base_agent.execution_stats["average_execution_time"] == 0.0
    
    async def test_execute_with_success(self):
        """测试成功执行"""
        # 准备输入状态
        input_state = AgentState()
        
        # 模拟执行方法
        self.base_agent.execute = AsyncMock(return_value=input_state)
        
        # 执行
        result_state = await self.base_agent.execute(input_state)
        
        # 验证执行统计更新
        assert self.base_agent.execution_stats["total_executions"] == 1
        assert self.base_agent.execution_stats["total_errors"] == 0
    
    async def test_execute_with_error(self):
        """测试执行时发生错误"""
        # 准备输入状态
        input_state = AgentState()
        
        # 模拟执行方法抛出异常
        self.base_agent.execute = AsyncMock(side_effect=Exception("Test error"))
        
        # 执行并捕获异常
        with pytest.raises(Exception, match="Test error"):
            await self.base_agent.execute(input_state)
        
        # 验证执行统计更新
        assert self.base_agent.execution_stats["total_executions"] == 1
        assert self.base_agent.execution_stats["total_errors"] == 1
    
    async def test_execute_with_retry_mechanism(self):
        """测试重试机制"""
        # 创建配置，设置重试次数
        config = AgentConfig(
            name="test_agent",
            agent_type="base",
            system_prompt="Test system prompt",
            retry_count=2
        )
        
        class RetryAgent(BaseAgent):
            def __init__(self, config, llm_client, tool_executor, event_manager=None):
                super().__init__(config, llm_client, tool_executor, event_manager)
                self.call_count = 0

            async def execute(self, state, config):
                self.call_count += 1
                if self.call_count <= 2:  # 前两次失败
                    raise Exception(f"Test error {self.call_count}")
                return state  # 第三次成功

            def can_handle(self, state):
                return True

            def get_capabilities(self):
                return {"retry_capability": True}
        
        retry_agent = RetryAgent(
            config=config,
            llm_client=self.mock_llm_client,
            tool_executor=self.mock_tool_executor,
            event_manager=self.mock_event_manager
        )
        
        # 准备输入状态
        input_state = AgentState()
        
        # 执行（应该成功，因为有重试机制）
        result_state = await retry_agent.execute(input_state, {})  # type: ignore
        
        # 验证重试了3次（2次失败 + 1次成功）
        assert retry_agent.call_count == 3
        assert retry_agent.execution_stats["total_executions"] == 1
        assert retry_agent.execution_stats["total_errors"] == 2  # 前两次错误
    
    async def test_execute_tool_async(self):
        """测试异步工具执行"""
        # 准备工具调用
        tool_call = {
            "name": "calculator",
            "arguments": {"operation": "add", "operands": [2, 2]}
        }
        
        # 模拟工具执行结果
        mock_tool_result = ToolResult(
            success=True,
            output="4",
            error=None,
            tool_name="calculator",
            metadata={}
        )
        self.mock_tool_executor.execute_tool_async = AsyncMock(return_value=mock_tool_result)
        
        # 执行工具
        result = await self.base_agent.execute_tool_async(tool_call)
        
        # 验证工具执行器被调用
        self.mock_tool_executor.execute_tool_async.assert_called_once_with(
            tool_call["name"], 
            tool_call["arguments"]
        )
        
        # 验证结果
        assert isinstance(result, ToolResult)
        assert result.tool_name == "calculator"
        assert result.output == "4"
    
    async def test_execute_tool_async_with_error(self):
        """测试异步工具执行时发生错误"""
        # 准备工具调用
        tool_call = {
            "name": "calculator",
            "arguments": {"operation": "divide", "operands": [2, 0]}
        }
        
        # 模拟工具执行错误
        mock_tool_result = ToolResult(
            success=False,
            output=None,
            error="Division by zero",
            tool_name="calculator",
            metadata={}
        )
        self.mock_tool_executor.execute_tool_async = AsyncMock(return_value=mock_tool_result)
        
        # 执行工具
        result = await self.base_agent.execute_tool_async(tool_call)
        
        # 验证结果包含错误
        assert isinstance(result, ToolResult)
        assert result.tool_name == "calculator"
        assert result.error == "Division by zero"
    
    def test_get_execution_stats(self):
        """测试获取执行统计信息"""
        # 执行几次操作来生成统计数据
        self.base_agent.execution_stats["total_executions"] = 5
        self.base_agent.execution_stats["total_errors"] = 1
        self.base_agent.execution_stats["average_execution_time"] = 0.123
        
        stats = self.base_agent.get_execution_stats()
        
        assert stats["total_executions"] == 5
        assert stats["total_errors"] == 1
        assert stats["success_rate"] == 0.8  # 4/5 = 0.8
        assert stats["average_execution_time"] == 0.123