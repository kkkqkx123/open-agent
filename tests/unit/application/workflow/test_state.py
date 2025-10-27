"""工作流状态测试

测试工作流状态定义和相关功能。
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.application.workflow.state import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
    MessageRole, ToolResult, WorkflowStatus,
    BaseWorkflowState, AgentState, WorkflowState, ReActState, PlanExecuteState,
    create_agent_state, create_workflow_state, create_react_state, 
    create_plan_execute_state, create_message, adapt_langchain_message
)


class TestMessageClasses(unittest.TestCase):
    """测试消息类"""
    
    def test_base_message(self):
        """测试基础消息"""
        message = BaseMessage(content="test content", type="base")
        self.assertEqual(message.content, "test content")
        self.assertEqual(message.type, "base")
        
        # 测试默认类型
        message = BaseMessage(content="test content")
        self.assertEqual(message.type, "base")
    
    def test_human_message(self):
        """测试人类消息"""
        message = HumanMessage(content="human message")
        self.assertEqual(message.content, "human message")
        self.assertEqual(message.type, "human")
    
    def test_ai_message(self):
        """测试AI消息"""
        message = AIMessage(content="ai message")
        self.assertEqual(message.content, "ai message")
        self.assertEqual(message.type, "ai")
    
    def test_system_message(self):
        """测试系统消息"""
        message = SystemMessage(content="system message")
        self.assertEqual(message.content, "system message")
        self.assertEqual(message.type, "system")
    
    def test_tool_message(self):
        """测试工具消息"""
        message = ToolMessage(content="tool result", tool_call_id="call_123")
        self.assertEqual(message.content, "tool result")
        self.assertEqual(message.type, "tool")
        self.assertEqual(message.tool_call_id, "call_123")
        
        # 测试默认工具调用ID
        message = ToolMessage(content="tool result")
        self.assertEqual(message.tool_call_id, "")


class TestMessageRole(unittest.TestCase):
    """测试消息角色常量"""
    
    def test_message_role_constants(self):
        """测试消息角色常量值"""
        self.assertEqual(MessageRole.HUMAN, "human")
        self.assertEqual(MessageRole.AI, "ai")
        self.assertEqual(MessageRole.SYSTEM, "system")
        self.assertEqual(MessageRole.TOOL, "tool")


class TestToolResult(unittest.TestCase):
    """测试工具执行结果"""
    
    def test_tool_result_success(self):
        """测试成功的工具结果"""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            output="tool output"
        )
        
        self.assertEqual(result.tool_name, "test_tool")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "tool output")
        self.assertIsNone(result.error)
    
    def test_tool_result_failure(self):
        """测试失败的工具结果"""
        result = ToolResult(
            tool_name="test_tool",
            success=False,
            error="tool error"
        )
        
        self.assertEqual(result.tool_name, "test_tool")
        self.assertFalse(result.success)
        self.assertIsNone(result.output)
        self.assertEqual(result.error, "tool error")


class TestWorkflowStatus(unittest.TestCase):
    """测试工作流状态枚举"""
    
    def test_workflow_status_constants(self):
        """测试工作流状态常量值"""
        self.assertEqual(WorkflowStatus.NOT_STARTED, "not_started")
        self.assertEqual(WorkflowStatus.RUNNING, "running")
        self.assertEqual(WorkflowStatus.PAUSED, "paused")
        self.assertEqual(WorkflowStatus.COMPLETED, "completed")
        self.assertEqual(WorkflowStatus.FAILED, "failed")
        self.assertEqual(WorkflowStatus.CANCELLED, "cancelled")


class TestStateTypes(unittest.TestCase):
    """测试状态类型定义"""
    
    def test_base_workflow_state_structure(self):
        """测试基础工作流状态结构"""
        # 验证类型定义存在
        self.assertTrue(hasattr(BaseWorkflowState, '__annotations__'))
        self.assertIn('messages', BaseWorkflowState.__annotations__)
        self.assertIn('metadata', BaseWorkflowState.__annotations__)
    
    def test_agent_state_structure(self):
        """测试Agent状态结构"""
        # 验证类型定义存在
        self.assertTrue(hasattr(AgentState, '__annotations__'))
        
        # 验证包含基础状态字段
        self.assertIn('messages', AgentState.__annotations__)
        self.assertIn('metadata', AgentState.__annotations__)
        
        # 验证包含Agent特定字段
        self.assertIn('input', AgentState.__annotations__)
        self.assertIn('output', AgentState.__annotations__)
        self.assertIn('tool_calls', AgentState.__annotations__)
        self.assertIn('tool_results', AgentState.__annotations__)
        self.assertIn('iteration_count', AgentState.__annotations__)
        self.assertIn('max_iterations', AgentState.__annotations__)
        self.assertIn('errors', AgentState.__annotations__)
        self.assertIn('complete', AgentState.__annotations__)
    
    def test_workflow_state_structure(self):
        """测试工作流状态结构"""
        # 验证类型定义存在
        self.assertTrue(hasattr(WorkflowState, '__annotations__'))
        
        # 验证包含Agent状态字段
        self.assertIn('input', WorkflowState.__annotations__)
        self.assertIn('output', WorkflowState.__annotations__)
        
        # 验证包含工作流特定字段
        self.assertIn('workflow_name', WorkflowState.__annotations__)
        self.assertIn('current_step', WorkflowState.__annotations__)
        self.assertIn('analysis', WorkflowState.__annotations__)
        self.assertIn('decision', WorkflowState.__annotations__)
        self.assertIn('context', WorkflowState.__annotations__)
        self.assertIn('start_time', WorkflowState.__annotations__)
        self.assertIn('workflow_id', WorkflowState.__annotations__)
        self.assertIn('custom_fields', WorkflowState.__annotations__)
    
    def test_react_state_structure(self):
        """测试ReAct状态结构"""
        # 验证类型定义存在
        self.assertTrue(hasattr(ReActState, '__annotations__'))
        
        # 验证包含工作流状态字段
        self.assertIn('workflow_name', ReActState.__annotations__)
        
        # 验证包含ReAct特定字段
        self.assertIn('thought', ReActState.__annotations__)
        self.assertIn('action', ReActState.__annotations__)
        self.assertIn('observation', ReActState.__annotations__)
        self.assertIn('steps', ReActState.__annotations__)
    
    def test_plan_execute_state_structure(self):
        """测试计划执行状态结构"""
        # 验证类型定义存在
        self.assertTrue(hasattr(PlanExecuteState, '__annotations__'))
        
        # 验证包含工作流状态字段
        self.assertIn('workflow_name', PlanExecuteState.__annotations__)
        
        # 验证包含计划执行特定字段
        self.assertIn('plan', PlanExecuteState.__annotations__)
        self.assertIn('steps', PlanExecuteState.__annotations__)
        self.assertIn('step_results', PlanExecuteState.__annotations__)


class TestStateFactoryFunctions(unittest.TestCase):
    """测试状态工厂函数"""
    
    def test_create_agent_state(self):
        """测试创建Agent状态"""
        state = create_agent_state("test input", max_iterations=5)
        
        # 验证基本字段
        self.assertEqual(state["input"], "test input")
        self.assertEqual(state["max_iterations"], 5)
        self.assertIsNone(state["output"])
        
        # 验证列表字段初始化
        self.assertEqual(len(state["messages"]), 1)  # 默认包含人类消息
        self.assertEqual(state["messages"][0].content, "test input")
        self.assertEqual(state["messages"][0].type, "human")
        self.assertEqual(state["tool_calls"], [])
        self.assertEqual(state["tool_results"], [])
        self.assertEqual(state["errors"], [])
        
        # 验证计数和标志
        self.assertEqual(state["iteration_count"], 0)
        self.assertFalse(state["complete"])
        
        # 验证元数据
        self.assertEqual(state["metadata"], {})
    
    def test_create_agent_state_with_messages(self):
        """测试使用自定义消息创建Agent状态"""
        custom_messages = [
            SystemMessage(content="system message"),
            HumanMessage(content="human message")
        ]
        
        state = create_agent_state(
            "test input", 
            max_iterations=10,
            messages=custom_messages
        )
        
        # 验证使用自定义消息
        self.assertEqual(len(state["messages"]), 2)
        self.assertEqual(state["messages"][0].content, "system message")
        self.assertEqual(state["messages"][1].content, "human message")
    
    def test_create_workflow_state(self):
        """测试创建工作流状态"""
        with patch('src.application.workflow.state.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            state = create_workflow_state("test_workflow", "test input", max_iterations=8)
            
            # 验证基本字段
            self.assertEqual(state["workflow_name"], "test_workflow")
            self.assertEqual(state["input"], "test input")
            self.assertEqual(state["max_iterations"], 8)
            
            # 验证工作流特定字段
            self.assertIsNone(state["current_step"])
            self.assertIsNone(state["analysis"])
            self.assertIsNone(state["decision"])
            self.assertEqual(state["context"], {})
            self.assertEqual(state["start_time"], mock_now)
            self.assertIsNone(state["workflow_id"])
            self.assertEqual(state["custom_fields"], {})
    
    def test_create_react_state(self):
        """测试创建ReAct状态"""
        state = create_react_state("test_workflow", "test input", max_iterations=12)
        
        # 验证基本字段
        self.assertEqual(state["workflow_name"], "test_workflow")
        self.assertEqual(state["input"], "test input")
        self.assertEqual(state["max_iterations"], 12)
        
        # 验证ReAct特定字段
        self.assertIsNone(state["thought"])
        self.assertIsNone(state["action"])
        self.assertIsNone(state["observation"])
        self.assertEqual(state["steps"], [])
    
    def test_create_plan_execute_state(self):
        """测试创建计划执行状态"""
        state = create_plan_execute_state("test_workflow", "test input", max_iterations=15)
        
        # 验证基本字段
        self.assertEqual(state["workflow_name"], "test_workflow")
        self.assertEqual(state["input"], "test input")
        self.assertEqual(state["max_iterations"], 15)
        
        # 验证计划执行特定字段
        self.assertIsNone(state["plan"])
        self.assertEqual(state["steps"], [])
        self.assertEqual(state["step_results"], [])


class TestMessageCreationFunctions(unittest.TestCase):
    """测试消息创建函数"""
    
    def test_create_message(self):
        """测试创建消息"""
        # 测试各种角色
        human_msg = create_message("human content", MessageRole.HUMAN)
        self.assertIsInstance(human_msg, HumanMessage)
        self.assertEqual(human_msg.content, "human content")
        
        ai_msg = create_message("ai content", MessageRole.AI)
        self.assertIsInstance(ai_msg, AIMessage)
        self.assertEqual(ai_msg.content, "ai content")
        
        system_msg = create_message("system content", MessageRole.SYSTEM)
        self.assertIsInstance(system_msg, SystemMessage)
        self.assertEqual(system_msg.content, "system content")
        
        tool_msg = create_message("tool content", MessageRole.TOOL, tool_call_id="call_123")
        self.assertIsInstance(tool_msg, ToolMessage)
        self.assertEqual(tool_msg.content, "tool content")
        self.assertEqual(tool_msg.tool_call_id, "call_123")  # type: ignore
        
        # 测试未知角色
        unknown_msg = create_message("unknown content", "unknown")
        self.assertIsInstance(unknown_msg, BaseMessage)
        self.assertEqual(unknown_msg.content, "unknown content")
        self.assertEqual(unknown_msg.type, "unknown")
    
    def test_adapt_langchain_message(self):
        """测试适配LangChain消息"""
        # 创建模拟的LangChain消息
        mock_lc_message = Mock()
        mock_lc_message.content = "test content"
        mock_lc_message.type = "human"
        
        # 适配消息
        adapted_msg = adapt_langchain_message(mock_lc_message)
        
        # 验证结果
        self.assertIsInstance(adapted_msg, HumanMessage)
        self.assertEqual(adapted_msg.content, "test content")
        
        # 测试AI消息
        mock_lc_message.type = "ai"
        adapted_msg = adapt_langchain_message(mock_lc_message)
        self.assertIsInstance(adapted_msg, AIMessage)
        
        # 测试系统消息
        mock_lc_message.type = "system"
        adapted_msg = adapt_langchain_message(mock_lc_message)
        self.assertIsInstance(adapted_msg, SystemMessage)
        
        # 测试工具消息
        mock_lc_message.type = "tool"
        mock_lc_message.tool_call_id = "call_123"
        adapted_msg = adapt_langchain_message(mock_lc_message)
        self.assertIsInstance(adapted_msg, ToolMessage)
        self.assertEqual(adapted_msg.tool_call_id, "call_123")  # type: ignore
        
        # 测试未知类型
        mock_lc_message.type = "unknown"
        adapted_msg = adapt_langchain_message(mock_lc_message)
        self.assertIsInstance(adapted_msg, BaseMessage)
        self.assertEqual(adapted_msg.type, "unknown")
    
    def test_adapt_langchain_message_without_attributes(self):
        """测试适配没有属性的LangChain消息"""
        # 创建没有content和type属性的消息
        mock_lc_message = Mock(spec=[])
        
        # 适配消息
        adapted_msg = adapt_langchain_message(mock_lc_message)
        
        # 验证结果
        self.assertIsInstance(adapted_msg, BaseMessage)
        self.assertEqual(adapted_msg.content, str(mock_lc_message))
        self.assertEqual(adapted_msg.type, "base")


class TestLangChainFallback(unittest.TestCase):
    """测试LangChain后备实现"""
    
    @patch('src.application.workflow.state.logger')
    def test_langchain_not_available(self, mock_logger):
        """测试LangChain不可用时的后备实现"""
        # 模拟导入错误
        with patch.dict('sys.modules', {'langchain_core.messages': None}):
            # 重新导入模块以触发后备实现
            import importlib
            import src.application.workflow.state
            importlib.reload(src.application.workflow.state)
            
            # 验证警告日志
            mock_logger.warning.assert_called_with("LangChain not available, using fallback message types")
            
            # 验证后备消息类型可用
            from src.application.workflow.state import (
                LCBaseMessage, LCHumanMessage,
                LCAIMessage, LCSystemMessage, LCToolMessage
            )
            
            # 测试后备消息类型
            base_msg = LCBaseMessage(content="content", type="base")  # type: ignore
            self.assertEqual(base_msg.content, "content")
            self.assertEqual(base_msg.type, "base")
            
            human_msg = LCHumanMessage(content="human content")  # type: ignore
            self.assertEqual(human_msg.content, "human content")
            self.assertEqual(human_msg.type, "human")
            
            ai_msg = LCAIMessage(content="ai content")  # type: ignore
            self.assertEqual(ai_msg.content, "ai content")
            self.assertEqual(ai_msg.type, "ai")
            
            system_msg = LCSystemMessage(content="system content")  # type: ignore
            self.assertEqual(system_msg.content, "system content")
            self.assertEqual(system_msg.type, "system")
            
            tool_msg = LCToolMessage(content="tool content", tool_call_id="call_123")  # type: ignore
            self.assertEqual(tool_msg.content, "tool content")
            self.assertEqual(tool_msg.type, "tool")
            self.assertEqual(tool_msg.tool_call_id, "call_123")


if __name__ == '__main__':
    unittest.main()