"""工作流状态单元测试"""

import pytest
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.workflow import (
    WorkflowState,
    create_workflow_state,
    update_workflow_state_with_analysis,
    update_workflow_state_with_decision,
    update_workflow_state_with_context,
    update_workflow_state_with_custom_field,
    complete_workflow,
    get_workflow_duration,
    get_graph_state,
    has_all_graphs_completed
)


class TestWorkflowStateFunctions:
    """工作流状态函数测试"""

    def test_create_workflow_state_with_defaults(self):
        """测试创建工作流状态（使用默认值）"""
        state = create_workflow_state(
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
        assert state["workflow_config"] == {}
        
        # 验证工作流特定字段
        assert state["current_graph"] == ""
        assert state["current_step"] == ""
        assert state["analysis"] is None
        assert state["decision"] is None
        assert state["context"] == {}
        assert state["start_time"] is not None
        assert state["end_time"] is None
        assert state["graph_states"] == {}
        assert state["custom_fields"] == {}

    def test_create_workflow_state_with_custom_params(self):
        """测试创建工作流状态（使用自定义参数）"""
        workflow_config = {"setting": "value"}
        
        state = create_workflow_state(
            workflow_id="workflow_123",
            workflow_name="测试工作流",
            input_text="测试输入",
            workflow_config=workflow_config,
            max_iterations=5
        )
        
        # 验证自定义字段
        assert state["max_iterations"] == 5
        assert state["workflow_config"] == workflow_config

    def test_update_workflow_state_with_analysis(self):
        """测试用分析结果更新工作流状态"""
        original_state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        analysis = "这是分析结果"
        
        updated_state = update_workflow_state_with_analysis(original_state, analysis)
        
        # 验证更新
        assert updated_state["analysis"] == analysis
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_update_workflow_state_with_decision(self):
        """测试用决策结果更新工作流状态"""
        original_state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        decision = "这是决策结果"
        
        updated_state = update_workflow_state_with_decision(original_state, decision)
        
        # 验证更新
        assert updated_state["decision"] == decision
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_update_workflow_state_with_context(self):
        """测试用上下文信息更新工作流状态"""
        original_state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        context_key = "test_key"
        context_value = "测试值"
        
        updated_state = update_workflow_state_with_context(
            original_state, context_key, context_value
        )
        
        # 验证更新
        assert updated_state["context"][context_key] == context_value
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_update_workflow_state_with_custom_field(self):
        """测试用自定义字段更新工作流状态"""
        original_state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        field_key = "custom_field"
        field_value = "自定义值"
        
        updated_state = update_workflow_state_with_custom_field(
            original_state, field_key, field_value
        )
        
        # 验证更新
        assert updated_state["custom_fields"][field_key] == field_value
        # 验证其他字段未改变
        assert updated_state["workflow_id"] == original_state["workflow_id"]

    def test_complete_workflow(self):
        """测试完成工作流"""
        original_state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        original_state["start_time"] = None  # 确保有开始时间
        
        completed_state = complete_workflow(original_state)
        
        # 验证更新
        assert completed_state["end_time"] is not None
        assert completed_state["complete"] is True
        # 验证其他字段未改变
        assert completed_state["workflow_id"] == original_state["workflow_id"]

    def test_get_workflow_duration_with_end_time(self):
        """测试获取工作流执行时长（有结束时间）"""
        from datetime import datetime, timedelta
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=30)
        
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["start_time"] = start_time
        state["end_time"] = end_time
        
        duration = get_workflow_duration(state)
        
        # 验证时长
        assert duration == 30.0

    def test_get_workflow_duration_without_end_time(self):
        """测试获取工作流执行时长（无结束时间）"""
        from datetime import datetime
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["start_time"] = datetime.now()
        state["end_time"] = None  # 未完成
        
        duration = get_workflow_duration(state)
        
        # 验证时长为None
        assert duration is None

    def test_get_graph_state_exists(self):
        """测试获取图状态（存在）"""
        graph_state = {"messages": [], "input": "图输入"}
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["graph_states"] = {"graph_1": graph_state}
        
        result = get_graph_state(state, "graph_1")
        
        # 验证结果
        assert result == graph_state

    def test_get_graph_state_not_exists(self):
        """测试获取图状态（不存在）"""
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["graph_states"] = {}
        
        result = get_graph_state(state, "nonexistent_graph")
        
        # 验证结果为None
        assert result is None

    def test_has_all_graphs_completed_true(self):
        """测试检查所有图是否完成（真）"""
        completed_graph_state = {"complete": True}
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["graph_states"] = {
            "graph_1": completed_graph_state,
            "graph_2": completed_graph_state
        }
        
        result = has_all_graphs_completed(state, ["graph_1", "graph_2"])
        
        # 验证结果
        assert result is True

    def test_has_all_graphs_completed_false(self):
        """测试检查所有图是否完成（假）"""
        completed_graph_state = {"complete": True}
        incomplete_graph_state = {"complete": False}
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["graph_states"] = {
            "graph_1": completed_graph_state,
            "graph_2": incomplete_graph_state
        }
        
        result = has_all_graphs_completed(state, ["graph_1", "graph_2"])
        
        # 验证结果
        assert result is False

    def test_has_all_graphs_completed_missing_graph(self):
        """测试检查所有图是否完成（缺少图）"""
        completed_graph_state = {"complete": True}
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        state["graph_states"] = {
            "graph_1": completed_graph_state
            # 缺少graph_2
        }
        
        result = has_all_graphs_completed(state, ["graph_1", "graph_2"])
        
        # 验证结果
        assert result is False

    def test_has_all_graphs_completed_empty_list(self):
        """测试检查所有图是否完成（空列表）"""
        state = create_workflow_state(
            "workflow_123", "测试工作流", "测试输入"
        )
        
        result = has_all_graphs_completed(state, [])
        
        # 验证结果
        assert result is True