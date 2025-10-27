"""ReAct状态单元测试"""

import pytest
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.react import (
    ReActState,
    create_react_state,
    update_react_state_with_thought,
    update_react_state_with_action,
    update_react_state_with_observation,
    add_react_step,
    get_current_react_step,
    has_react_reached_max_steps,
    is_react_cycle_complete,
    reset_react_cycle,
    get_react_summary
)


class TestReActStateFunctions:
    """ReAct状态函数测试"""

    def test_create_react_state_with_defaults(self):
        """测试创建ReAct状态（使用默认值）"""
        state = create_react_state(
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入"
        )
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["workflow_id"] == "workflow_123"
        assert state["workflow_name"] == "测试工作流"
        assert state["input"] == "测试输入"
        assert state["max_iterations"] == 10
        assert state["max_steps"] == 10
        
        # 验证ReAct特定字段
        assert state["thought"] is None
        assert state["action"] is None
        assert state["observation"] is None
        assert state["steps"] == []
        assert state["current_step_index"] == 0

    def test_create_react_state_with_custom_params(self):
        """测试创建ReAct状态（使用自定义参数）"""
        state = create_react_state(
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入",
            max_iterations=5,
            max_steps=5
        )
        
        # 验证自定义字段
        assert state["max_iterations"] == 5
        assert state["max_steps"] == 5

    def test_update_react_state_with_thought(self):
        """测试用思考更新ReAct状态"""
        original_state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        thought = "这是思考内容"
        
        updated_state = update_react_state_with_thought(original_state, thought)
        
        # 验证更新
        assert updated_state["thought"] == thought
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_update_react_state_with_action(self):
        """测试用动作更新ReAct状态"""
        original_state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        action = "这是动作内容"
        
        updated_state = update_react_state_with_action(original_state, action)
        
        # 验证更新
        assert updated_state["action"] == action
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_update_react_state_with_observation(self):
        """测试用观察更新ReAct状态"""
        original_state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        observation = "这是观察内容"
        
        updated_state = update_react_state_with_observation(original_state, observation)
        
        # 验证更新
        assert updated_state["observation"] == observation
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_add_react_step_with_all_fields(self):
        """测试添加ReAct步骤（包含所有字段）"""
        original_state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        original_state["current_step_index"] = 0
        
        updated_state = add_react_step(
            original_state,
            thought="思考内容",
            action="动作内容",
            observation="观察内容"
        )
        
        # 验证更新
        assert len(updated_state["steps"]) == 1
        step = updated_state["steps"][0]
        assert step["step_index"] == 1
        assert step["thought"] == "思考内容"
        assert step["action"] == "动作内容"
        assert step["observation"] == "观察内容"
        assert updated_state["current_step_index"] == 1
        assert updated_state["thought"] == "思考内容"
        assert updated_state["action"] == "动作内容"
        assert updated_state["observation"] == "观察内容"

    def test_add_react_step_with_existing_fields(self):
        """测试添加ReAct步骤（使用现有字段）"""
        original_state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        original_state["thought"] = "现有思考"
        original_state["action"] = "现有动作"
        original_state["observation"] = "现有观察"
        original_state["current_step_index"] = 0
        
        updated_state = add_react_step(original_state)
        
        # 验证更新
        assert len(updated_state["steps"]) == 1
        step = updated_state["steps"][0]
        assert step["thought"] == "现有思考"
        assert step["action"] == "现有动作"
        assert step["observation"] == "现有观察"

    def test_get_current_react_step(self):
        """测试获取当前ReAct步骤"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = [{
            "step_index": 1,
            "thought": "思考1",
            "action": "动作1",
            "observation": "观察1"
        }]
        
        current_step = get_current_react_step(state)
        assert current_step == state["steps"][-1]

    def test_get_current_react_step_no_steps(self):
        """测试获取当前ReAct步骤（无步骤）"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = []
        
        current_step = get_current_react_step(state)
        assert current_step is None

    def test_has_react_reached_max_steps_true(self):
        """测试检查ReAct是否达到最大步骤数（真）"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["current_step_index"] = 10
        state["max_steps"] = 10
        
        result = has_react_reached_max_steps(state)
        assert result is True

    def test_has_react_reached_max_steps_false(self):
        """测试检查ReAct是否达到最大步骤数（假）"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["current_step_index"] = 5
        state["max_steps"] = 10
        
        result = has_react_reached_max_steps(state)
        assert result is False

    def test_is_react_cycle_complete_true(self):
        """测试检查ReAct循环是否完成（真）"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["thought"] = "思考内容"
        state["action"] = "动作内容"
        state["observation"] = "观察内容"
        
        result = is_react_cycle_complete(state)
        assert result is True

    def test_is_react_cycle_complete_false(self):
        """测试检查ReAct循环是否完成（假）"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["thought"] = "思考内容"
        state["action"] = "动作内容"
        state["observation"] = None  # 缺少观察
        
        result = is_react_cycle_complete(state)
        assert result is False

    def test_reset_react_cycle(self):
        """测试重置ReAct循环"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["thought"] = "思考内容"
        state["action"] = "动作内容"
        state["observation"] = "观察内容"
        
        reset_state = reset_react_cycle(state)
        
        # 验证重置
        assert reset_state["thought"] is None
        assert reset_state["action"] is None
        assert reset_state["observation"] is None
        # 验证其他字段未改变
        assert reset_state["workflow_id"] == state["workflow_id"]

    def test_get_react_summary_with_steps(self):
        """测试获取ReAct执行摘要（有步骤）"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = [
            {
                "step_index": 1,
                "thought": "思考1",
                "action": "动作1",
                "observation": "观察1"
            },
            {
                "step_index": 2,
                "thought": "思考2",
                "action": "动作2",
                "observation": "观察2"
            }
        ]
        
        summary = get_react_summary(state)
        
        # 验证摘要内容
        assert "ReAct执行摘要" in summary
        assert "共2步" in summary
        assert "步骤 1:" in summary
        assert "思考: 思考1" in summary
        assert "动作: 动作1" in summary
        assert "观察: 观察1" in summary
        assert "步骤 2:" in summary
        assert "思考: 思考2" in summary
        assert "动作: 动作2" in summary
        assert "观察: 观察2" in summary

    def test_get_react_summary_no_steps(self):
        """测试获取ReAct执行摘要（无步骤）"""
        state = create_react_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = []
        
        summary = get_react_summary(state)
        
        # 验证摘要内容
        assert summary == "尚未执行任何步骤"