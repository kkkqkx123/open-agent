"""Agent状态单元测试"""

import pytest
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.agent import (
    AgentState,
    create_agent_state,
    update_agent_state_with_tool_call,
    update_agent_state_with_tool_result,
    update_agent_state_with_output,
    update_agent_state_with_error,
    increment_agent_iteration,
    is_agent_complete,
    has_agent_reached_max_iterations
)
from src.infrastructure.graph.states.base import BaseMessage, HumanMessage, AIMessage


class TestAgentStateFunctions:
    """Agent状态函数测试"""

    def test_create_agent_state_with_defaults(self):
        """测试创建Agent状态（使用默认值）"""
        state = create_agent_state(
            input_text="测试输入",
            agent_id="test_agent"
        )
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["input"] == "测试输入"
        assert state["agent_id"] == "test_agent"
        assert state["max_iterations"] == 10
        assert state["output"] is None
        assert state["tool_calls"] == []
        assert state["tool_results"] == []
        assert state["iteration_count"] == 0
        assert state["errors"] == []
        assert state["complete"] is False
        assert state["agent_config"] == {}
        assert state["execution_result"] is None
        
        # 验证消息字段
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == "测试输入"

    def test_create_agent_state_with_custom_params(self):
        """测试创建Agent状态（使用自定义参数）"""
        agent_config = {"model": "gpt-3.5-turbo", "temperature": 0.7}
        messages = [HumanMessage(content="自定义消息")]
        
        state = create_agent_state(
            input_text="测试输入",
            agent_id="test_agent",
            agent_config=agent_config,
            max_iterations=5,
            messages=messages
        )
        
        # 验证自定义字段
        assert state["max_iterations"] == 5
        assert state["agent_config"] == agent_config
        assert state["messages"] == messages

    def test_update_agent_state_with_tool_call(self):
        """测试用工具调用更新Agent状态"""
        original_state = create_agent_state("测试输入", "test_agent")
        tool_call = {"name": "test_tool", "arguments": {"param": "value"}}
        
        updated_state = update_agent_state_with_tool_call(original_state, tool_call)
        
        # 验证更新
        assert len(updated_state["tool_calls"]) == 1
        assert updated_state["tool_calls"][0] == tool_call
        # 验证其他字段未改变
        assert updated_state["input"] == original_state["input"]
        assert updated_state["agent_id"] == original_state["agent_id"]

    def test_update_agent_state_with_tool_result(self):
        """测试用工具结果更新Agent状态"""
        original_state = create_agent_state("测试输入", "test_agent")
        tool_result = {"result": "工具执行结果", "success": True}
        
        updated_state = update_agent_state_with_tool_result(original_state, tool_result)
        
        # 验证更新
        assert len(updated_state["tool_results"]) == 1
        assert updated_state["tool_results"][0] == tool_result
        # 验证其他字段未改变
        assert updated_state["input"] == original_state["input"]
        assert updated_state["agent_id"] == original_state["agent_id"]

    def test_update_agent_state_with_output(self):
        """测试用输出更新Agent状态"""
        original_state = create_agent_state("测试输入", "test_agent")
        output = "AI生成的响应"
        
        updated_state = update_agent_state_with_output(original_state, output)
        
        # 验证更新
        assert updated_state["output"] == output
        assert updated_state["complete"] is True
        # 验证消息更新
        assert len(updated_state["messages"]) == 2
        assert isinstance(updated_state["messages"][1], AIMessage)
        assert updated_state["messages"][1].content == output

    def test_update_agent_state_with_error(self):
        """测试用错误更新Agent状态"""
        original_state = create_agent_state("测试输入", "test_agent")
        error = "执行错误"
        
        updated_state = update_agent_state_with_error(original_state, error)
        
        # 验证更新
        assert len(updated_state["errors"]) == 1
        assert updated_state["errors"][0] == error
        # 验证其他字段未改变
        assert updated_state["input"] == original_state["input"]
        assert updated_state["agent_id"] == original_state["agent_id"]

    def test_increment_agent_iteration(self):
        """测试增加Agent迭代次数"""
        original_state = create_agent_state("测试输入", "test_agent")
        original_state["iteration_count"] = 3
        original_state["max_iterations"] = 5
        
        updated_state = increment_agent_iteration(original_state)
        
        # 验证更新
        assert updated_state["iteration_count"] == 4
        assert updated_state["complete"] is False
        # 验证其他字段未改变
        assert updated_state["input"] == original_state["input"]
        assert updated_state["agent_id"] == original_state["agent_id"]

    def test_increment_agent_iteration_reach_max(self):
        """测试增加Agent迭代次数达到最大值"""
        original_state = create_agent_state("测试输入", "test_agent")
        original_state["iteration_count"] = 9
        original_state["max_iterations"] = 10
        
        updated_state = increment_agent_iteration(original_state)
        
        # 验证更新
        assert updated_state["iteration_count"] == 10
        assert updated_state["complete"] is True

    def test_is_agent_complete_true(self):
        """测试检查Agent是否完成（真）"""
        state = create_agent_state("测试输入", "test_agent")
        state["complete"] = True
        
        result = is_agent_complete(state)
        assert result is True

    def test_is_agent_complete_false(self):
        """测试检查Agent是否完成（假）"""
        state = create_agent_state("测试输入", "test_agent")
        state["complete"] = False
        
        result = is_agent_complete(state)
        assert result is False

    def test_has_agent_reached_max_iterations_true(self):
        """测试检查Agent是否达到最大迭代次数（真）"""
        state = create_agent_state("测试输入", "test_agent")
        state["iteration_count"] = 10
        state["max_iterations"] = 10
        
        result = has_agent_reached_max_iterations(state)
        assert result is True

    def test_has_agent_reached_max_iterations_false(self):
        """测试检查Agent是否达到最大迭代次数（假）"""
        state = create_agent_state("测试输入", "test_agent")
        state["iteration_count"] = 5
        state["max_iterations"] = 10
        
        result = has_agent_reached_max_iterations(state)
        assert result is False