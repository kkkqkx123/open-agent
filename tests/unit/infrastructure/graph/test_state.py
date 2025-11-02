"""图状态单元测试"""

import pytest
from typing import Any, List, Optional, Dict
from dataclasses import dataclass

# 导入LangChain消息类型用于状态测试
from langchain_core.messages import HumanMessage as LCHumanMessage, AIMessage as LCAIMessage, ToolMessage as LCToolMessage

from src.infrastructure.graph.state import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    MessageRole,
    BaseGraphState,
    AgentState,
    WorkflowState,
    ReActState,
    PlanExecuteState,
    create_agent_state,
    create_workflow_state,
    create_react_state,
    create_plan_execute_state,
    create_message,
    update_state_with_message,
    update_state_with_tool_result,
    update_state_with_error,
    validate_state,
    serialize_state,
    deserialize_state
)


class TestMessageClasses:
    """消息类测试"""

    def test_base_message(self) -> None:
        """测试基础消息"""
        message = BaseMessage(content="测试内容", type="test")
        assert message.content == "测试内容"
        assert message.type == "test"

    def test_human_message(self) -> None:
        """测试人类消息"""
        message = HumanMessage(content="人类消息")
        assert message.content == "人类消息"
        assert message.type == "human"

    def test_ai_message(self) -> None:
        """测试AI消息"""
        message = AIMessage(content="AI消息")
        assert message.content == "AI消息"
        assert message.type == "ai"

    def test_system_message(self) -> None:
        """测试系统消息"""
        message = SystemMessage(content="系统消息")
        assert message.content == "系统消息"
        assert message.type == "system"

    def test_tool_message(self) -> None:
        """测试工具消息"""
        message = ToolMessage(content="工具消息", tool_call_id="tool_123")
        assert message.content == "工具消息"
        assert message.type == "tool"
        assert message.tool_call_id == "tool_123"

    def test_message_role_constants(self) -> None:
        """测试消息角色常量"""
        assert MessageRole.HUMAN == "human"
        assert MessageRole.AI == "ai"
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.TOOL == "tool"


class TestStateTypeDefinitions:
    """状态类型定义测试"""

    def test_base_graph_state(self) -> None:
        """测试基础图状态"""
        # BaseGraphState是TypedDict的别名，测试其结构
        state: BaseGraphState = {
            "messages": [LCHumanMessage(content="测试")],
            "metadata": {"key": "value"}
        }
        assert "messages" in state
        assert "metadata" in state

    def test_agent_state(self) -> None:
        """测试Agent状态"""
        # AgentState是BaseGraphState的扩展，测试其结构
        state: AgentState = {
            "messages": [LCHumanMessage(content="测试")],
            "input": "输入",
            "output": "输出",
            "tool_calls": [{"name": "tool1"}],
            "tool_results": [{"result": "结果"}],
            "iteration_count": 1,
            "max_iterations": 10,
            "errors": ["错误"],
            "complete": False,
            "metadata": {"key": "value"}
        }
        assert "input" in state
        assert "tool_calls" in state
        assert "iteration_count" in state

    def test_workflow_state(self) -> None:
        """测试工作流状态"""
        # WorkflowState是AgentState的扩展，测试其结构
        state: WorkflowState = {
            "messages": [LCHumanMessage(content="测试")],
            "input": "输入",
            "workflow_id": "workflow_123",
            "step_name": "步骤1",
            "analysis": "分析",
            "context": {"key": "value"},
            "tool_calls": [{"name": "tool1"}],
            "iteration_count": 1,
            "max_iterations": 10,
            "errors": ["错误"],
            "complete": False,
            "metadata": {"key": "value"}
        }
        assert "workflow_id" in state
        assert "analysis" in state
        assert "context" in state

    def test_react_state(self) -> None:
        """测试ReAct状态"""
        # ReActState是WorkflowState的扩展，测试其结构
        state: ReActState = {
            "messages": [LCHumanMessage(content="测试")],
            "input": "输入",
            "workflow_id": "workflow_123",
            "thought": "思考",
            "action": "动作",
            "observation": "观察",
            "steps": [{"step": "步骤1"}],
            "tool_calls": [{"name": "tool1"}],
            "iteration_count": 1,
            "max_iterations": 10,
            "errors": ["错误"],
            "complete": False,
            "metadata": {"key": "value"}
        }
        assert "thought" in state
        assert "action" in state
        assert "observation" in state
        assert "steps" in state

    def test_plan_execute_state(self) -> None:
        """测试计划执行状态"""
        # PlanExecuteState是WorkflowState的扩展，测试其结构
        state: PlanExecuteState = {
            "messages": [LCHumanMessage(content="测试")],
            "input": "输入",
            "workflow_id": "workflow_123",
            "plan": "计划",
            "steps": ["步骤1", "步骤2"],
            "current_step": "当前步骤",
            "step_results": [{"result": "结果"}],
            "tool_calls": [{"name": "tool1"}],
            "iteration_count": 1,
            "max_iterations": 10,
            "errors": ["错误"],
            "complete": False,
            "metadata": {"key": "value"}
        }
        assert "plan" in state
        assert "steps" in state
        assert "step_results" in state


class TestStateFactoryFunctions:
    """状态工厂函数测试"""

    def test_create_agent_state(self) -> None:
        """测试创建Agent状态"""
        state = create_agent_state(
            input_text="测试输入",
            max_iterations=5,
            messages=[LCHumanMessage(content="人类消息")]
        )

        assert isinstance(state, dict)
        assert "input" in state
        assert "max_iterations" in state
        assert "messages" in state
        assert "output" in state
        assert "tool_calls" in state
        assert "tool_results" in state
        assert "iteration_count" in state
        assert "errors" in state
        assert "complete" in state
        assert "metadata" in state
        assert state["input"] == "测试输入"
        assert state["max_iterations"] == 5
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "人类消息"
        assert state["messages"][0].type == "human"
        assert state["output"] is None
        assert state["tool_calls"] == []
        assert state["tool_results"] == []
        assert state["iteration_count"] == 0
        assert state["errors"] == []
        assert state["complete"] is False
        assert state["metadata"] == {}

    def test_create_agent_state_default_messages(self) -> None:
        """测试创建Agent状态（默认消息）"""
        state = create_agent_state(input_text="测试输入")

        assert "messages" in state
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "测试输入"
        assert state["messages"][0].type == "human"

    def test_create_workflow_state(self) -> None:
        """测试创建工作流状态"""
        state = create_workflow_state(
            workflow_id="workflow_123",
            input_text="测试输入",
            max_iterations=5
        )

        assert isinstance(state, dict)
        assert "workflow_id" in state
        assert "input" in state
        assert "max_iterations" in state
        assert "step_name" in state
        assert "analysis" in state
        assert "decision" in state
        assert "context" in state
        assert state["workflow_id"] == "workflow_123"
        assert state["input"] == "测试输入"
        assert state["max_iterations"] == 5
        assert state["step_name"] is None
        assert state["analysis"] is None
        assert state["decision"] is None
        assert state["context"] == {}

    def test_create_react_state(self) -> None:
        """测试创建ReAct状态"""
        state = create_react_state(
            workflow_id="workflow_123",
            input_text="测试输入",
            max_iterations=5
        )

        assert isinstance(state, dict)
        assert "workflow_id" in state
        assert "input" in state
        assert "max_iterations" in state
        assert "thought" in state
        assert "action" in state
        assert "observation" in state
        assert "steps" in state
        assert state["workflow_id"] == "workflow_123"
        assert state["input"] == "测试输入"
        assert state["max_iterations"] == 5
        assert state["thought"] is None
        assert state["action"] is None
        assert state["observation"] is None
        assert state["steps"] == []

    def test_create_plan_execute_state(self) -> None:
        """测试创建计划执行状态"""
        state = create_plan_execute_state(
            workflow_id="workflow_123",
            input_text="测试输入",
            max_iterations=5
        )

        assert isinstance(state, dict)
        assert "workflow_id" in state
        assert "input" in state
        assert "max_iterations" in state
        assert "plan" in state
        assert "steps" in state
        assert "current_step" in state
        assert "step_results" in state
        assert state["workflow_id"] == "workflow_123"
        assert state["input"] == "测试输入"
        assert state["max_iterations"] == 5
        assert state["plan"] is None
        assert state["steps"] == []
        assert state["current_step"] is None
        assert state["step_results"] == []


class TestMessageFactoryFunction:
    """消息工厂函数测试"""

    def test_create_message_human(self) -> None:
        """测试创建人类消息"""
        message = create_message(content="人类消息", role=MessageRole.HUMAN)
        # 现在返回LangChain消息类型
        from langchain_core.messages import HumanMessage as LCHumanMessage
        assert isinstance(message, LCHumanMessage)
        assert message.content == "人类消息"

    def test_create_message_ai(self) -> None:
        """测试创建AI消息"""
        message = create_message(content="AI消息", role=MessageRole.AI)
        # 现在返回LangChain消息类型
        from langchain_core.messages import AIMessage as LCAIMessage
        assert isinstance(message, LCAIMessage)
        assert message.content == "AI消息"

    def test_create_message_system(self) -> None:
        """测试创建系统消息"""
        message = create_message(content="系统消息", role=MessageRole.SYSTEM)
        # 现在返回LangChain消息类型
        from langchain_core.messages import SystemMessage as LCSystemMessage
        assert isinstance(message, LCSystemMessage)
        assert message.content == "系统消息"

    def test_create_message_tool(self) -> None:
        """测试创建工具消息"""
        message = create_message(
            content="工具消息",
            role=MessageRole.TOOL,
            tool_call_id="tool_123"
        )
        # 现在返回LangChain消息类型
        from langchain_core.messages import ToolMessage as LCToolMessage
        assert isinstance(message, LCToolMessage)
        assert message.content == "工具消息"
        assert message.tool_call_id == "tool_123"

    def test_create_message_custom_role(self) -> None:
        """测试创建自定义角色消息"""
        message = create_message(content="自定义消息", role="custom")
        # 现在返回LangChain消息类型
        from langchain_core.messages import BaseMessage as LCBaseMessage
        assert isinstance(message, LCBaseMessage)
        assert message.content == "自定义消息"
        assert message.type == "custom"


class TestStateUpdateFunctions:
    """状态更新函数测试"""

    def test_update_state_with_message(self) -> None:
        """测试用消息更新状态"""
        original_state = {"existing_key": "value"}
        message = LCHumanMessage(content="新消息")

        updated_state = update_state_with_message(original_state, message)
        
        assert "messages" in updated_state
        assert len(updated_state["messages"]) == 1
        assert updated_state["messages"][0].content == "新消息"
        assert updated_state["messages"][0].type == "human"

    def test_update_state_with_tool_result(self) -> None:
        """测试用工具结果更新状态"""
        original_state = {"existing_key": "value"}
        tool_call = {"name": "test_tool", "args": {}}
        result = "工具执行结果"
        
        updated_state = update_state_with_tool_result(original_state, tool_call, result)
        
        assert "tool_results" in updated_state
        assert len(updated_state["tool_results"]) == 1
        assert updated_state["tool_results"][0]["tool_call"] == tool_call
        assert updated_state["tool_results"][0]["result"] == result

    def test_update_state_with_error(self) -> None:
        """测试用错误信息更新状态"""
        original_state = {"existing_key": "value"}
        error = "错误信息"
        
        updated_state = update_state_with_error(original_state, error)
        
        assert "errors" in updated_state
        assert len(updated_state["errors"]) == 1
        assert updated_state["errors"][0] == "错误信息"


class TestStateValidationFunctions:
    """状态验证函数测试"""

    def test_validate_state_base_graph_state_success(self) -> None:
        """测试验证基础图状态成功"""
        state = {
            "messages": [LCHumanMessage(content="测试")],
            "metadata": {"key": "value"}
        }

        errors = validate_state(state, BaseGraphState)
        assert errors == []

    def test_validate_state_base_graph_state_missing_messages(self) -> None:
        """测试验证基础图状态缺少消息"""
        state = {
            "metadata": {"key": "value"}
        }
        
        errors = validate_state(state, BaseGraphState)
        assert len(errors) == 1
        assert "缺少messages字段" in errors

    def test_validate_state_agent_state_success(self) -> None:
        """测试验证Agent状态成功"""
        state = {
            "messages": [LCHumanMessage(content="测试")],
            "input": "输入",
            "max_iterations": 10,
            "metadata": {"key": "value"}
        }

        errors = validate_state(state, AgentState)
        assert errors == []

    def test_validate_state_agent_state_missing_required_fields(self) -> None:
        """测试验证Agent状态缺少必需字段"""
        state = {
            "messages": [LCHumanMessage(content="测试")],
            "metadata": {"key": "value"}
        }

        errors = validate_state(state, AgentState)
        assert len(errors) == 2
        assert "缺少必需字段: input" in errors
        assert "缺少必需字段: max_iterations" in errors

    def test_validate_state_workflow_state_success(self) -> None:
        """测试验证工作流状态成功"""
        state = {
            "messages": [LCHumanMessage(content="测试")],
            "workflow_id": "workflow_123",
            "input": "输入",
            "max_iterations": 10,
            "metadata": {"key": "value"}
        }

        errors = validate_state(state, WorkflowState)
        assert errors == []

    def test_validate_state_workflow_state_missing_required_fields(self) -> None:
        """测试验证工作流状态缺少必需字段"""
        state = {
            "messages": [LCHumanMessage(content="测试")],
            "metadata": {"key": "value"}
        }

        errors = validate_state(state, WorkflowState)
        assert len(errors) == 3
        assert "缺少必需字段: workflow_id" in errors
        assert "缺少必需字段: input" in errors
        assert "缺少必需字段: max_iterations" in errors


class TestStateSerializationFunctions:
    """状态序列化函数测试"""

    def test_serialize_state(self) -> None:
        """测试序列化状态"""
        state = {
            "messages": [
                HumanMessage(content="人类消息"),
                AIMessage(content="AI消息")
            ],
            "input": "输入",
            "metadata": {"key": "value"}
        }
        
        serialized = serialize_state(state)
        
        assert isinstance(serialized, dict)
        assert "messages" in serialized
        assert len(serialized["messages"]) == 2
        assert serialized["messages"][0]["content"] == "人类消息"
        assert serialized["messages"][0]["type"] == "human"
        assert serialized["messages"][1]["content"] == "AI消息"
        assert serialized["messages"][1]["type"] == "ai"
        assert serialized["input"] == "输入"
        assert serialized["metadata"] == {"key": "value"}

    def test_deserialize_state(self) -> None:
        """测试反序列化状态"""
        serialized_state = {
            "messages": [
                {"content": "人类消息", "type": "human", "tool_call_id": ""},
                {"content": "AI消息", "type": "ai", "tool_call_id": ""}
            ],
            "input": "输入",
            "metadata": {"key": "value"}
        }
        
        deserialized = deserialize_state(serialized_state)
        
        assert isinstance(deserialized, dict)
        assert "messages" in deserialized
        assert len(deserialized["messages"]) == 2
        assert isinstance(deserialized["messages"][0], LCHumanMessage)
        assert deserialized["messages"][0].content == "人类消息"
        assert isinstance(deserialized["messages"][1], LCAIMessage)
        assert deserialized["messages"][1].content == "AI消息"
        assert deserialized["input"] == "输入"
        assert deserialized["metadata"] == {"key": "value"}

    def test_serialize_deserialize_roundtrip(self) -> None:
        """测试序列化和反序列化往返"""
        original_state = {
            "messages": [
                HumanMessage(content="人类消息"),
                AIMessage(content="AI消息"),
                ToolMessage(content="工具消息", tool_call_id="tool_123")
            ],
            "input": "输入",
            "metadata": {"key": "value"}
        }
        
        # 序列化
        serialized = serialize_state(original_state)
        
        # 反序列化
        deserialized = deserialize_state(serialized)
        
        # 验证
        assert len(deserialized["messages"]) == 3
        assert isinstance(deserialized["messages"][0], LCHumanMessage)
        assert deserialized["messages"][0].content == "人类消息"
        assert isinstance(deserialized["messages"][1], LCAIMessage)
        assert deserialized["messages"][1].content == "AI消息"
        assert isinstance(deserialized["messages"][2], LCToolMessage)
        assert deserialized["messages"][2].content == "工具消息"
        assert deserialized["messages"][2].tool_call_id == "tool_123"
        assert deserialized["input"] == "输入"
        assert deserialized["metadata"] == {"key": "value"}