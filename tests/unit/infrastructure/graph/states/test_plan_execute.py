"""计划执行状态单元测试"""

import pytest
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.plan_execute import (
    PlanExecuteState,
    create_plan_execute_state,
    update_plan_execute_state_with_plan,
    update_plan_execute_state_with_current_step,
    add_step_result,
    get_next_step,
    get_current_step_info,
    has_plan_execute_reached_max_steps,
    is_plan_complete,
    is_execution_complete,
    get_plan_execute_progress,
    get_plan_execute_summary
)


class TestPlanExecuteStateFunctions:
    """计划执行状态函数测试"""

    def test_create_plan_execute_state_with_defaults(self):
        """测试创建计划执行状态（使用默认值）"""
        state = create_plan_execute_state(
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
        
        # 验证计划执行特定字段
        assert state["plan"] is None
        assert state["steps"] == []
        assert state["step_results"] == []
        assert state["current_step_index"] == 0
        assert state["plan_complete"] is False
        assert state["execution_complete"] is False

    def test_create_plan_execute_state_with_custom_params(self):
        """测试创建计划执行状态（使用自定义参数）"""
        state = create_plan_execute_state(
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入",
            max_iterations=5,
            max_steps=5
        )
        
        # 验证自定义字段
        assert state["max_iterations"] == 5
        assert state["max_steps"] == 5

    def test_update_plan_execute_state_with_plan(self):
        """测试用计划更新计划执行状态"""
        original_state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        plan = "这是执行计划"
        steps = ["步骤1", "步骤2", "步骤3"]
        
        updated_state = update_plan_execute_state_with_plan(original_state, plan, steps)
        
        # 验证更新
        assert updated_state["plan"] == plan
        assert updated_state["steps"] == steps
        assert updated_state["plan_complete"] is True
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_update_plan_execute_state_with_current_step(self):
        """测试用当前步骤更新计划执行状态"""
        original_state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        current_step = "执行步骤1"
        
        updated_state = update_plan_execute_state_with_current_step(original_state, current_step)
        
        # 验证更新
        assert updated_state["current_step"] == current_step
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_add_step_result_success(self):
        """测试添加步骤结果（成功）"""
        original_state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        original_state["steps"] = ["步骤1", "步骤2"]
        original_state["current_step_index"] = 0
        
        updated_state = add_step_result(
            original_state, 
            "步骤1", 
            "执行结果", 
            success=True
        )
        
        # 验证更新
        assert len(updated_state["step_results"]) == 1
        assert updated_state["step_results"][0]["step"] == "步骤1"
        assert updated_state["step_results"][0]["result"] == "执行结果"
        assert updated_state["step_results"][0]["success"] is True
        assert updated_state["current_step_index"] == 1
        # 验证未完成（还有步骤2未执行）
        assert updated_state["execution_complete"] is False

    def test_add_step_result_failure(self):
        """测试添加步骤结果（失败）"""
        original_state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        original_state["steps"] = ["步骤1"]
        original_state["current_step_index"] = 0
        
        updated_state = add_step_result(
            original_state, 
            "步骤1", 
            None, 
            success=False,
            error="执行错误"
        )
        
        # 验证更新
        assert len(updated_state["step_results"]) == 1
        assert updated_state["step_results"][0]["success"] is False
        assert updated_state["step_results"][0]["error"] == "执行错误"
        assert updated_state["current_step_index"] == 1
        # 验证已完成（没有更多步骤）
        assert updated_state["execution_complete"] is True

    def test_add_step_result_all_steps_completed(self):
        """测试添加步骤结果（所有步骤完成）"""
        original_state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        original_state["steps"] = ["步骤1"]
        original_state["current_step_index"] = 0
        
        updated_state = add_step_result(
            original_state, 
            "步骤1", 
            "执行结果", 
            success=True
        )
        
        # 验证已完成
        assert updated_state["current_step_index"] == 1
        assert updated_state["execution_complete"] is True
        assert updated_state["complete"] is True

    def test_get_next_step(self):
        """测试获取下一个步骤"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = ["步骤1", "步骤2", "步骤3"]
        state["current_step_index"] = 1  # 下一个要执行步骤2
        
        next_step = get_next_step(state)
        assert next_step == "步骤2"

    def test_get_next_step_no_more_steps(self):
        """测试获取下一个步骤（没有更多步骤）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = ["步骤1", "步骤2"]
        state["current_step_index"] = 2  # 已经执行完所有步骤
        
        next_step = get_next_step(state)
        assert next_step is None

    def test_get_current_step_info(self):
        """测试获取当前步骤信息"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = ["步骤1"]
        state["current_step_index"] = 1
        state["step_results"] = [{
            "step_index": 1,
            "step": "步骤1",
            "result": "执行结果",
            "success": True,
            "error": None
        }]
        
        step_info = get_current_step_info(state)
        assert step_info == state["step_results"][-1]

    def test_get_current_step_info_no_results(self):
        """测试获取当前步骤信息（无结果）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["step_results"] = []
        
        step_info = get_current_step_info(state)
        assert step_info is None

    def test_has_plan_execute_reached_max_steps_true(self):
        """测试检查计划执行是否达到最大步骤数（真）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["current_step_index"] = 10
        state["max_steps"] = 10
        
        result = has_plan_execute_reached_max_steps(state)
        assert result is True

    def test_has_plan_execute_reached_max_steps_false(self):
        """测试检查计划执行是否达到最大步骤数（假）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["current_step_index"] = 5
        state["max_steps"] = 10
        
        result = has_plan_execute_reached_max_steps(state)
        assert result is False

    def test_is_plan_complete_true(self):
        """测试检查计划是否完成（真）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["plan_complete"] = True
        
        result = is_plan_complete(state)
        assert result is True

    def test_is_plan_complete_false(self):
        """测试检查计划是否完成（假）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["plan_complete"] = False
        
        result = is_plan_complete(state)
        assert result is False

    def test_is_execution_complete_true(self):
        """测试检查执行是否完成（真）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["execution_complete"] = True
        
        result = is_execution_complete(state)
        assert result is True

    def test_is_execution_complete_false(self):
        """测试检查执行是否完成（假）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["execution_complete"] = False
        
        result = is_execution_complete(state)
        assert result is False

    def test_get_plan_execute_progress(self):
        """测试获取计划执行进度"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = ["步骤1", "步骤2", "步骤3"]
        state["step_results"] = [
            {"step": "步骤1", "success": True},
            {"step": "步骤2", "success": True}
        ]
        state["current_step_index"] = 2
        
        progress = get_plan_execute_progress(state)
        
        # 验证进度信息
        assert progress["total_steps"] == 3
        assert progress["completed_steps"] == 2
        assert progress["current_step_index"] == 2
        assert progress["progress_percentage"] == pytest.approx(66.67, 0.01)
        assert progress["next_step"] == "步骤3"
        assert progress["is_complete"] is False

    def test_get_plan_execute_progress_complete(self):
        """测试获取计划执行进度（已完成）"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["steps"] = ["步骤1", "步骤2"]
        state["step_results"] = [
            {"step": "步骤1", "success": True},
            {"step": "步骤2", "success": True}
        ]
        state["current_step_index"] = 2
        state["execution_complete"] = True
        
        progress = get_plan_execute_progress(state)
        
        # 验证进度信息
        assert progress["total_steps"] == 2
        assert progress["completed_steps"] == 2
        assert progress["progress_percentage"] == 100.0
        assert progress["next_step"] is None
        assert progress["is_complete"] is True

    def test_get_plan_execute_summary(self):
        """测试获取计划执行摘要"""
        state = create_plan_execute_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["plan"] = "执行计划内容"
        state["steps"] = ["步骤1", "步骤2"]
        state["step_results"] = [
            {"step": "步骤1", "success": True, "error": None},
            {"step": "步骤2", "success": False, "error": "执行失败"}
        ]
        
        summary = get_plan_execute_summary(state)
        
        # 验证摘要内容
        assert "计划执行摘要" in summary
        assert "执行计划内容" in summary
        assert "总步骤数: 2" in summary
        assert "已完成步骤: 2" in summary
        assert "1. 步骤1 ✓" in summary
        assert "2. 步骤2 ✗" in summary
        assert "错误: 执行失败" in summary