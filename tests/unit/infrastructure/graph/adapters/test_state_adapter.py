"""状态适配器测试用例"""

import pytest
import warnings
from datetime import datetime
from typing import Dict, Any

from src.infrastructure.graph.states import WorkflowState, create_workflow_state
from src.infrastructure.graph.adapters.state_adapter import WorkflowStateAdapter, GraphAgentState  # GraphAgentState 保持向后兼容
from src.infrastructure.graph.adapters.state_adapter import StateAdapter
from src.infrastructure.graph.states.base import LCHumanMessage, LCAIMessage, LCSystemMessage, LCToolMessage


class TestStateAdapter:
    """状态适配器测试类"""
    
    def test_to_graph_state_basic_conversion(self):
        """测试基础状态转换"""
        adapter = StateAdapter()
        
        # 创建工作流状态适配器
        adapter_state = WorkflowStateAdapter()
        adapter_state.workflow_id = "test-workflow"
        adapter_state.workflow_type = "react"
        adapter_state.current_task = "测试任务"
        adapter_state.max_iterations = 5
        adapter_state.iteration_count = 2
        
        # 添加消息
        adapter_state.messages.append(LCHumanMessage(content="用户消息"))
        adapter_state.messages.append(LCAIMessage(content="助手回复"))
        
        # 转换到图状态
        graph_state = adapter.to_graph_state(adapter_state)
        
        # 验证转换结果
        assert graph_state["workflow_id"] == "test-workflow"
        assert graph_state["workflow_type"] == "react"
        assert graph_state["current_task"] == "测试任务"
        assert graph_state["max_iterations"] == 5
        assert graph_state["iteration_count"] == 2
        assert len(graph_state["messages"]) == 2
        assert graph_state["messages"][0].content == "用户消息"
        assert graph_state["messages"][1].content == "助手回复"
    
    def test_from_graph_state_basic_conversion(self):
        """测试从图状态转换回适配器状态"""
        adapter = StateAdapter()
        
        # 创建图状态
        graph_state: WorkflowState = {
            "workflow_id": "test-workflow",
            "workflow_type": "react",
            "current_task": "测试任务",
            "messages": [],
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 3,
            "max_iterations": 10,
            "errors": [],
            "complete": True,
            "custom_fields": {"key": "value"}
        }
        
        # 转换回适配器状态
        adapter_state = adapter.from_graph_state(graph_state)
        
        # 验证转换结果
        assert adapter_state.workflow_id == "test-workflow"
        assert adapter_state.workflow_type == "react"
        assert adapter_state.current_task == "测试任务"
        assert adapter_state.max_iterations == 10
        assert adapter_state.iteration_count == 3
        assert adapter_state.custom_fields == {"key": "value"}
    
    def test_message_conversion(self):
        """测试消息转换"""
        adapter = StateAdapter()
        
        # 创建不同格式的消息
        messages = [
            LCHumanMessage(content="用户消息"),
            LCSystemMessage(content="系统消息"),
            LCAIMessage(content="助手消息"),
            LCToolMessage(content="工具消息", tool_call_id="123")
        ]
        
        # 测试消息转换函数
        converted_messages = adapter._convert_messages_to_langchain(messages)
        
        # 验证消息类型和内容
        assert len(converted_messages) == 4
        assert converted_messages[0].content == "用户消息"
        assert converted_messages[1].content == "系统消息"
        assert converted_messages[2].content == "助手消息"
        assert converted_messages[3].content == "工具消息"
        
        # 测试从字典格式转换
        dict_messages = [
            {"content": "字典用户消息", "role": "human"},
            {"content": "字典助手消息", "role": "ai"},
            {"content": "字典工具消息", "role": "tool", "tool_call_id": "456"}
        ]
        
        converted_dict_messages = adapter._convert_messages_from_langchain(dict_messages)
        
        # 验证字典消息转换
        assert len(converted_dict_messages) == 3
        assert converted_dict_messages[0].content == "字典用户消息"
        assert converted_dict_messages[1].content == "字典助手消息"
        assert converted_dict_messages[2].content == "字典工具消息"
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 测试 GraphAgentState 别名
        adapter_state = GraphAgentState()
        adapter_state.workflow_id = "test-workflow"
        
        # 验证别名正常工作
        assert isinstance(adapter_state, WorkflowStateAdapter)
        assert adapter_state.workflow_id == "test-workflow"
        
        # 测试旧属性名的废弃警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # 设置旧属性名应该触发警告
            adapter_state.agent_id = "old-workflow"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "agent_id is deprecated" in str(w[0].message)
            
            # 验证值被正确映射
            assert adapter_state.workflow_id == "old-workflow"
            
            # 获取旧属性名也应该触发警告
            old_id = adapter_state.agent_id
            assert len(w) == 2
            assert old_id == "old-workflow"
    
    def test_field_mapping(self):
        """测试字段映射功能"""
        adapter = StateAdapter()
        
        # 测试包含旧字段名的状态字典
        old_state_dict = {
            "agent_id": "old-agent-id",
            "agent_type": "old-agent-type",
            "current_task": "测试任务",
            "max_iterations": 15,
            "messages": []
        }
        
        # 转换应该正确映射字段
        adapter_state = adapter._dict_to_adapter_state(old_state_dict)
        
        assert adapter_state.workflow_id == "old-agent-id"
        assert adapter_state.workflow_type == "old-agent-type"
        assert adapter_state.current_task == "测试任务"
        assert adapter_state.max_iterations == 15
    
    def test_empty_state_conversion(self):
        """测试空状态转换"""
        adapter = StateAdapter()
        
        # 创建空适配器状态
        empty_adapter_state = WorkflowStateAdapter()
        
        # 转换为图状态
        graph_state = adapter.to_graph_state(empty_adapter_state)
        
        # 验证基础字段
        assert graph_state["workflow_id"] == ""
        assert graph_state["workflow_type"] == ""
        assert graph_state["iteration_count"] == 0
        
        # 转换回适配器状态
        converted_back = adapter.from_graph_state(graph_state)
        
        # 验证一致性
        assert converted_back.workflow_id == ""
        assert converted_back.workflow_type == ""
        assert converted_back.iteration_count == 0
    
    def test_workflow_state_integration(self):
        """测试与 WorkflowState 的集成"""
        adapter = StateAdapter()
        
        # 创建标准的 WorkflowState
        workflow_state = create_workflow_state(
            workflow_id="integration-test",
            workflow_name="Integration Test Workflow",
            input_text="测试输入",
            max_iterations=8
        )
        
        # 转换为适配器状态
        adapter_state = adapter.from_graph_state(workflow_state)
        
        # 验证转换结果
        assert adapter_state.workflow_id == "integration-test"
        assert adapter_state.max_iterations == 8
        assert len(adapter_state.messages) == 1  # 应该包含输入消息
        
        # 转换回 WorkflowState
        converted_back = adapter.to_graph_state(adapter_state)
        
        # 验证往返转换的一致性
        assert converted_back["workflow_id"] == "integration-test"
        assert converted_back["max_iterations"] == 8
    
    def test_error_handling(self):
        """测试错误处理"""
        adapter = StateAdapter()
        
        # 测试无效输入的处理
        invalid_state = {
            "invalid_field": "invalid_value"
        }
        
        # 应该能够处理无效输入而不崩溃
        adapter_state = adapter.from_graph_state(invalid_state)
        assert adapter_state.workflow_id == ""
        assert adapter_state.workflow_type == ""
    
    def test_custom_fields_preservation(self):
        """测试自定义字段的保留"""
        adapter = StateAdapter()
        
        # 创建包含自定义字段的状态
        adapter_state = WorkflowStateAdapter()
        adapter_state.workflow_id = "custom-test"
        adapter_state.custom_fields = {
            "user_preference": "dark_mode",
            "debug_mode": True,
            "timeout": 30
        }
        adapter_state.context = {
            "session_id": "sess_123",
            "user_role": "admin"
        }
        
        # 转换为图状态
        graph_state = adapter.to_graph_state(adapter_state)
        
        # 验证自定义字段被保留
        assert graph_state["custom_fields"]["user_preference"] == "dark_mode"
        assert graph_state["custom_fields"]["debug_mode"] is True
        assert graph_state["custom_fields"]["timeout"] == 30
        assert graph_state["context"]["session_id"] == "sess_123"
        assert graph_state["context"]["user_role"] == "admin"
        
        # 转换回适配器状态
        converted_back = adapter.from_graph_state(graph_state)
        
        # 验证自定义字段的一致性
        assert converted_back.custom_fields["user_preference"] == "dark_mode"
        assert converted_back.context["session_id"] == "sess_123"


if __name__ == "__main__":
    pytest.main([__file__])