"""Agent状态管理器单元测试"""

import pytest
from src.domain.agent.state_manager import AgentStateManager
from src.domain.agent.state import AgentState, AgentMessage
from src.domain.tools.base import ToolResult


class TestAgentStateManager:
    """AgentStateManager测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        self.state_manager = AgentStateManager()
    
    def test_create_initial_state(self):
        """测试创建初始状态"""
        config = {
            "name": "test_agent",
            "agent_type": "react",
            "system_prompt": "Test system prompt"
        }

        initial_state = self.state_manager.create_initial_state("test_agent", config, "test_workflow")

        assert isinstance(initial_state, AgentState)
        assert initial_state.agent_id == "test_agent"
        assert initial_state.custom_fields["agent_config"] == config
        assert initial_state.custom_fields["workflow_name"] == "test_workflow"
        assert initial_state.iteration_count == 0
        assert initial_state.max_iterations == 10  # 默认值
        assert len(initial_state.messages) == 0
        assert len(initial_state.tool_results) == 0
        assert len(initial_state.errors) == 0
    
    def test_update_state_with_memory(self):
        """测试更新状态的记忆部分"""
        initial_state = AgentState()

        # 创建一些记忆项
        messages = [
            AgentMessage(content="Hello", role="human"),
            AgentMessage(content="Hi there!", role="ai")
        ]

        updated_state = self.state_manager.update_state_with_memory(initial_state, messages)

        assert len(updated_state.messages) == 2
        assert updated_state.messages[0].content == "Hello"
        assert updated_state.messages[1].content == "Hi there!"
    
    def test_update_state_with_tool_result(self):
        """测试更新状态的工具结果"""
        initial_state = AgentState()
        
        # 创建工具结果
        tool_result = ToolResult(
        tool_name="calculator",
        success=True,
        output="4",
        error=None,
            metadata={"operation": "addition"}
        )
        
        updated_state = self.state_manager.update_state_with_tool_result(initial_state, tool_result)
        
        assert len(updated_state.tool_results) == 1
        assert updated_state.tool_results[0].tool_name == "calculator"
        assert updated_state.tool_results[0].output == "4"
        assert updated_state.tool_results[0].metadata is not None and updated_state.tool_results[0].metadata["operation"] == "addition"
    
    def test_update_state_with_error(self):
        """测试更新状态的错误信息"""
        initial_state = AgentState()
        
        # 创建错误信息
        error_info = {
            "type": "ToolExecutionError",
            "message": "Failed to execute calculator tool",
            "details": {"tool_name": "calculator", "error": "Division by zero"}
        }
        
        updated_state = self.state_manager.update_state_with_error(initial_state, error_info)
        
        assert len(updated_state.errors) == 1
        assert updated_state.errors[0]["type"] == "ToolExecutionError"
        assert updated_state.errors[0]["message"] == "Failed to execute calculator tool"
        assert updated_state.errors[0]["details"]["tool_name"] == "calculator"
    
    def test_update_iteration_count(self):
        """测试更新迭代计数"""
        initial_state = AgentState(iteration_count=3)
        
        updated_state = self.state_manager.update_iteration_count(initial_state)
        
        assert updated_state.iteration_count == 4
    
    def test_is_max_iterations_reached(self):
        """测试是否达到最大迭代次数"""
        # 未达到最大迭代次数
        state = AgentState(iteration_count=5, max_iterations=10)
        assert self.state_manager.is_max_iterations_reached(state) is False
        
        # 达到最大迭代次数
        state = AgentState(iteration_count=10, max_iterations=10)
        assert self.state_manager.is_max_iterations_reached(state) is True
        
        # 超过最大迭代次数
        state = AgentState(iteration_count=15, max_iterations=10)
        assert self.state_manager.is_max_iterations_reached(state) is True
    
    def test_reset_state_for_new_task(self):
        """测试为新任务重置状态"""
        # 创建一个有内容的状态
        initial_state = AgentState(
            agent_id="test_agent",
            current_task="Calculate 2+2"
        )

        # 添加一些内容
        initial_state.messages.append(AgentMessage(content="Calculate 2+2", role="human"))
        initial_state.tool_results.append(ToolResult(tool_name="calculator", success=True, output="4"))
        initial_state.errors.append({"type": "TestError", "message": "Test error"})
        initial_state.iteration_count = 5

        # 重置状态
        reset_state = self.state_manager.reset_state_for_new_task(initial_state)

        # 验证状态被重置
        assert reset_state.agent_id == "test_agent"  # agent_id应该保持不变
        assert reset_state.current_task is None
        assert len(reset_state.messages) == 0
        assert len(reset_state.tool_results) == 0
        assert len(reset_state.errors) == 0
        assert reset_state.iteration_count == 0