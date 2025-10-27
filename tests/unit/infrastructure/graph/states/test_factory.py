"""状态工厂单元测试"""

import pytest
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.factory import StateFactory
from src.infrastructure.graph.states.base import BaseMessage, HumanMessage, AIMessage
from src.infrastructure.graph.states.agent import AgentState
from src.infrastructure.graph.states.workflow import WorkflowState
from src.infrastructure.graph.states.react import ReActState
from src.infrastructure.graph.states.plan_execute import PlanExecuteState


class TestStateFactory:
    """状态工厂测试"""

    def test_create_base_state_with_defaults(self):
        """测试创建基础状态（使用默认值）"""
        state = StateFactory.create_base_state()
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["messages"] == []
        assert state["metadata"] == {}
        assert state["execution_context"] == {}
        assert state["current_step"] == "start"

    def test_create_base_state_with_custom_params(self):
        """测试创建基础状态（使用自定义参数）"""
        messages = [HumanMessage(content="测试消息")]
        metadata = {"key": "value"}
        execution_context = {"context_key": "context_value"}
        current_step = "test_step"
        
        state = StateFactory.create_base_state(
            messages=messages,
            metadata=metadata,
            execution_context=execution_context,
            current_step=current_step
        )
        
        # 验证自定义字段
        assert state["messages"] == messages
        assert state["metadata"] == metadata
        assert state["execution_context"] == execution_context
        assert state["current_step"] == current_step

    def test_create_agent_state(self):
        """测试创建Agent状态"""
        state = StateFactory.create_agent_state(
            input_text="测试输入",
            agent_id="test_agent",
            agent_config={"model": "gpt-3.5-turbo"},
            max_iterations=5
        )
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["input"] == "测试输入"
        assert state["agent_id"] == "test_agent"
        assert state["agent_config"] == {"model": "gpt-3.5-turbo"}
        assert state["max_iterations"] == 5
        assert state["output"] is None
        assert state["tool_calls"] == []
        assert state["tool_results"] == []
        assert state["iteration_count"] == 0
        assert state["errors"] == []
        assert state["complete"] is False

    def test_create_workflow_state(self):
        """测试创建工作流状态"""
        state = StateFactory.create_workflow_state(
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入",
            workflow_config={"setting": "value"},
            max_iterations=5
        )
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["workflow_id"] == "workflow_123"
        assert state["workflow_name"] == "测试工作流"
        assert state["input"] == "测试输入"
        assert state["workflow_config"] == {"setting": "value"}
        assert state["max_iterations"] == 5

    def test_create_react_state(self):
        """测试创建ReAct状态"""
        state = StateFactory.create_react_state(
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入",
            max_iterations=5,
            max_steps=10
        )
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["workflow_id"] == "workflow_123"
        assert state["workflow_name"] == "测试工作流"
        assert state["input"] == "测试输入"
        assert state["max_iterations"] == 5
        assert state["max_steps"] == 10
        assert state["thought"] is None
        assert state["action"] is None
        assert state["observation"] is None
        assert state["steps"] == []

    def test_create_plan_execute_state(self):
        """测试创建计划执行状态"""
        state = StateFactory.create_plan_execute_state(
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入",
            max_iterations=5,
            max_steps=10
        )
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["workflow_id"] == "workflow_123"
        assert state["workflow_name"] == "测试工作流"
        assert state["input"] == "测试输入"
        assert state["max_iterations"] == 5
        assert state["max_steps"] == 10
        assert state["plan"] is None
        assert state["steps"] == []
        assert state["step_results"] == []
        assert state["current_step_index"] == 0
        assert state["plan_complete"] is False
        assert state["execution_complete"] is False

    def test_create_state_by_type_base(self):
        """测试按类型创建基础状态"""
        state = StateFactory.create_state_by_type("base")
        assert isinstance(state, dict)
        assert state["messages"] == []
        assert state["current_step"] == "start"

    def test_create_state_by_type_agent(self):
        """测试按类型创建Agent状态"""
        state = StateFactory.create_state_by_type(
            "agent",
            input_text="测试输入",
            agent_id="test_agent"
        )
        assert isinstance(state, dict)
        assert state["input"] == "测试输入"
        assert state["agent_id"] == "test_agent"

    def test_create_state_by_type_workflow(self):
        """测试按类型创建工作流状态"""
        state = StateFactory.create_state_by_type(
            "workflow",
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入"
        )
        assert isinstance(state, dict)
        assert state["workflow_id"] == "workflow_123"
        assert state["workflow_name"] == "测试工作流"
        assert state["input"] == "测试输入"

    def test_create_state_by_type_react(self):
        """测试按类型创建ReAct状态"""
        state = StateFactory.create_state_by_type(
            "react",
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入"
        )
        assert isinstance(state, dict)
        assert state["workflow_id"] == "workflow_123"
        assert state["workflow_name"] == "测试工作流"
        assert state["input"] == "测试输入"

    def test_create_state_by_type_plan_execute(self):
        """测试按类型创建计划执行状态"""
        state = StateFactory.create_state_by_type(
            "plan_execute",
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入"
        )
        assert isinstance(state, dict)
        assert state["workflow_id"] == "workflow_123"
        assert state["workflow_name"] == "测试工作流"
        assert state["input"] == "测试输入"

    def test_create_state_by_type_invalid(self):
        """测试按类型创建状态（无效类型）"""
        with pytest.raises(ValueError, match="不支持的状态类型: invalid"):
            StateFactory.create_state_by_type("invalid")

    def test_create_message_human(self):
        """测试创建人类消息"""
        message = StateFactory.create_message(content="人类消息", role="human")
        assert isinstance(message, HumanMessage)
        assert message.content == "人类消息"

    def test_create_message_ai(self):
        """测试创建AI消息"""
        message = StateFactory.create_message(content="AI消息", role="ai")
        assert isinstance(message, AIMessage)
        assert message.content == "AI消息"

    def test_create_initial_messages(self):
        """测试创建初始消息列表"""
        messages = StateFactory.create_initial_messages(
            input_text="用户输入",
            system_prompt="系统提示"
        )
        
        assert len(messages) == 2
        assert isinstance(messages[0], BaseMessage)
        assert messages[0].type == "system"
        assert messages[0].content == "系统提示"
        assert isinstance(messages[1], BaseMessage)
        assert messages[1].type == "human"
        assert messages[1].content == "用户输入"

    def test_create_initial_messages_without_system_prompt(self):
        """测试创建初始消息列表（无系统提示）"""
        messages = StateFactory.create_initial_messages(input_text="用户输入")
        
        assert len(messages) == 1
        assert isinstance(messages[0], BaseMessage)
        assert messages[0].type == "human"
        assert messages[0].content == "用户输入"

    def test_clone_state(self):
        """测试克隆状态"""
        original_state = {
            "messages": [HumanMessage(content="消息1"), AIMessage(content="消息2")],
            "tool_calls": [{"name": "tool1"}],
            "metadata": {"key": "value"}
        }
        
        cloned_state = StateFactory.clone_state(original_state)
        
        # 验证克隆状态
        assert cloned_state == original_state
        assert cloned_state is not original_state  # 确保是不同的对象
        assert cloned_state["messages"] is not original_state["messages"]  # 确保列表被复制
        assert cloned_state["tool_calls"] is not original_state["tool_calls"]  # 确保列表被复制

    def test_merge_states(self):
        """测试合并状态"""
        base_state = {
            "messages": [HumanMessage(content="基础消息")],
            "tool_calls": [{"name": "base_tool"}],
            "metadata": {"base_key": "base_value"}
        }
        
        update_state = {
            "messages": [AIMessage(content="更新消息")],
            "tool_calls": [{"name": "update_tool"}],
            "new_field": "新字段值"
        }
        
        merged_state = StateFactory.merge_states(base_state, update_state)
        
        # 验证合并结果
        assert len(merged_state["messages"]) == 2
        assert merged_state["messages"][0].content == "基础消息"
        assert merged_state["messages"][1].content == "更新消息"
        assert len(merged_state["tool_calls"]) == 2
        assert merged_state["tool_calls"][0]["name"] == "base_tool"
        assert merged_state["tool_calls"][1]["name"] == "update_tool"
        assert merged_state["new_field"] == "新字段值"

    def test_validate_state_base_success(self):
        """测试验证基础状态成功"""
        state = {"messages": [HumanMessage(content="测试消息")]}
        errors = StateFactory.validate_state(state, dict)
        assert errors == []

    def test_validate_state_base_missing_messages(self):
        """测试验证基础状态缺少消息"""
        state = {"metadata": {"key": "value"}}
        errors = StateFactory.validate_state(state, dict)
        assert len(errors) == 1
        assert "缺少messages字段" in errors

    def test_validate_state_agent_success(self):
        """测试验证Agent状态成功"""
        state = {
            "messages": [HumanMessage(content="测试消息")],
            "input": "输入",
            "agent_id": "agent_123",
            "max_iterations": 10
        }
        errors = StateFactory.validate_state(state, AgentState)
        assert errors == []

    def test_validate_state_agent_missing_required_fields(self):
        """测试验证Agent状态缺少必需字段"""
        state = {"messages": [HumanMessage(content="测试消息")]}
        errors = StateFactory.validate_state(state, AgentState)
        assert len(errors) == 3
        assert "缺少必需字段: input" in errors
        assert "缺少必需字段: agent_id" in errors
        assert "缺少必需字段: max_iterations" in errors

    def test_validate_state_workflow_success(self):
        """测试验证工作流状态成功"""
        state = {
            "messages": [HumanMessage(content="测试消息")],
            "workflow_id": "workflow_123",
            "workflow_name": "测试工作流",
            "input": "输入",
            "max_iterations": 10
        }
        errors = StateFactory.validate_state(state, WorkflowState)
        assert errors == []

    def test_validate_state_workflow_missing_required_fields(self):
        """测试验证工作流状态缺少必需字段"""
        state = {"messages": [HumanMessage(content="测试消息")]}
        errors = StateFactory.validate_state(state, WorkflowState)
        assert len(errors) == 5
        assert "缺少必需字段: workflow_id" in errors
        assert "缺少必需字段: workflow_name" in errors
        assert "缺少必需字段: input" in errors
        assert "缺少必需字段: max_iterations" in errors

    def test_validate_state_react_success(self):
        """测试验证ReAct状态成功"""
        state = {
            "messages": [HumanMessage(content="测试消息")],
            "workflow_id": "workflow_123",
            "workflow_name": "测试工作流",
            "input": "输入",
            "max_iterations": 10,
            "max_steps": 5
        }
        errors = StateFactory.validate_state(state, ReActState)
        assert errors == []

    def test_validate_state_react_missing_required_fields(self):
        """测试验证ReAct状态缺少必需字段"""
        state = {"messages": [HumanMessage(content="测试消息")]}
        errors = StateFactory.validate_state(state, ReActState)
        assert len(errors) == 6
        assert "缺少必需字段: workflow_id" in errors
        assert "缺少必需字段: workflow_name" in errors
        assert "缺少必需字段: input" in errors
        assert "缺少必需字段: max_iterations" in errors
        assert "缺少必需字段: max_steps" in errors

    def test_validate_state_plan_execute_success(self):
        """测试验证计划执行状态成功"""
        state = {
            "messages": [HumanMessage(content="测试消息")],
            "workflow_id": "workflow_123",
            "workflow_name": "测试工作流",
            "input": "输入",
            "max_iterations": 10,
            "max_steps": 5
        }
        errors = StateFactory.validate_state(state, PlanExecuteState)
        assert errors == []

    def test_validate_state_plan_execute_missing_required_fields(self):
        """测试验证计划执行状态缺少必需字段"""
        state = {"messages": [HumanMessage(content="测试消息")]}
        errors = StateFactory.validate_state(state, PlanExecuteState)
        assert len(errors) == 6
        assert "缺少必需字段: workflow_id" in errors
        assert "缺少必需字段: workflow_name" in errors
        assert "缺少必需字段: input" in errors
        assert "缺少必需字段: max_iterations" in errors
        assert "缺少必需字段: max_steps" in errors