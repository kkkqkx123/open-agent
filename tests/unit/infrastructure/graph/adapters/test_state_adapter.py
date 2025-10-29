"""状态适配器测试用例"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.domain.agent.state import AgentState as DomainAgentState, AgentMessage as DomainAgentMessage, AgentStatus
from src.infrastructure.graph.adapters.state_adapter import GraphAgentState
from src.infrastructure.graph.adapters.state_adapter import StateAdapter
from src.domain.tools.interfaces import ToolResult
from src.infrastructure.graph.state import LCBaseMessage, LCHumanMessage, LCAIMessage


class TestStateAdapter:
    """状态适配器测试类"""
    
    def test_to_graph_state_basic_conversion(self):
        """测试基础状态转换"""
        adapter = StateAdapter()
        
        # 创建域层状态
        domain_state = DomainAgentState()
        domain_state.agent_id = "test-agent"
        domain_state.agent_type = "react"
        domain_state.current_task = "测试任务"
        domain_state.max_iterations = 5
        domain_state.iteration_count = 2
        domain_state.status = AgentStatus.RUNNING
        
        # 添加消息
        domain_state.add_message(DomainAgentMessage(
            content="用户消息",
            role="user",
            timestamp=datetime.now()
        ))
        domain_state.add_message(DomainAgentMessage(
            content="助手回复",
            role="assistant",
            timestamp=datetime.now()
        ))
        
        # 转换到图状态
        graph_state = adapter.to_graph_state(domain_state)
        
        # 验证转换结果
        assert graph_state["agent_id"] == "test-agent"
        assert graph_state["agent_config"]["agent_type"] == "react"
        assert graph_state["input"] == "测试任务"
        assert graph_state["max_iterations"] == 5
        assert graph_state["iteration_count"] == 2
        assert graph_state["complete"] is False
        assert len(graph_state["messages"]) == 2
        assert graph_state["messages"][0].content == "用户消息"
        assert graph_state["messages"][1].content == "助手回复"
    
    def test_from_graph_state_basic_conversion(self):
        """测试从图状态转换回域状态"""
        adapter = StateAdapter()
        
        # 创建图状态
        graph_state: GraphAgentState = {
            "agent_id": "test-agent",
            "agent_config": {"agent_type": "react"},
            "input": "测试任务",
            "output": "测试输出",
            "messages": [],
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 3,
            "max_iterations": 10,
            "errors": [],
            "complete": True,
            "execution_result": {
                "status": "completed",
                "start_time": "2024-01-01T00:00:00",
                "last_update_time": "2024-01-01T00:01:00",
                "execution_duration": 60.0,
                "custom_fields": {"key": "value"}
            }
        }
        
        # 转换回域状态
        domain_state = adapter.from_graph_state(graph_state)
        
        # 验证转换结果
        assert domain_state.agent_id == "test-agent"
        assert domain_state.agent_type == "react"
        assert domain_state.current_task == "测试任务"
        assert domain_state.max_iterations == 10
        assert domain_state.iteration_count == 3
        assert domain_state.status == AgentStatus.COMPLETED
        assert domain_state.custom_fields == {"key": "value"}
    
    def test_message_conversion(self):
        """测试消息转换"""
        adapter = StateAdapter()
        
        # 创建域层消息
        domain_messages = [
            DomainAgentMessage(content="用户消息", role="user"),
            DomainAgentMessage(content="系统消息", role="system"),
            DomainAgentMessage(content="助手消息", role="assistant"),
            DomainAgentMessage(content="工具消息", role="tool", metadata={"tool_call_id": "123"})
        ]
        
        # 转换为图消息
        graph_messages = adapter._convert_messages_to_graph(domain_messages)
        
        # 验证消息类型
        assert len(graph_messages) == 4
        assert graph_messages[0].type == "human"
        assert graph_messages[1].type == "system"
        assert graph_messages[2].type == "ai"
        assert graph_messages[3].type == "tool"
        
        # 转换回域消息
        converted_back = adapter._convert_messages_from_graph(graph_messages)
        
        # 验证转换一致性
        assert len(converted_back) == 4
        assert converted_back[0].role == "user"
        assert converted_back[1].role == "system"
        assert converted_back[2].role == "assistant"
        assert converted_back[3].role == "tool"
        assert converted_back[3].metadata.get("tool_call_id") == "123"
    def test_tool_results_conversion(self):
        """测试工具结果转换"""
        adapter = StateAdapter()
        
        # 创建域层工具结果
        tool_results = [
            ToolResult(success=True, output="42", tool_name="calculator"),
            ToolResult(success=False, error="搜索失败", tool_name="search")
        ]
        
        # 转换为图格式
        graph_results = adapter._convert_tool_results(tool_results)
        
        # 验证转换结果
        assert len(graph_results) == 2
        assert graph_results[0]["tool_name"] == "calculator"
        assert graph_results[0]["success"] is True
        assert graph_results[0]["output"] == "42"
        assert graph_results[1]["tool_name"] == "search"
        assert graph_results[1]["success"] is False
        assert graph_results[1]["error"] == "搜索失败"
        
        # 转换回域格式
        converted_back = adapter._convert_tool_results_from_graph(graph_results)
        
        # 验证转换一致性
        assert len(converted_back) == 2
        assert converted_back[0].tool_name == "calculator"
        assert converted_back[0].success is True
        assert converted_back[0].output == "42"
        assert converted_back[1].tool_name == "search"
        assert converted_back[1].success is False
        assert converted_back[1].error == "搜索失败"
        assert converted_back[1].error == "搜索失败"
    
    def test_get_last_assistant_message(self):
        """测试获取最后一条助手消息"""
        adapter = StateAdapter()
        
        # 创建消息列表
        messages = [
            DomainAgentMessage(content="用户消息1", role="user"),
            DomainAgentMessage(content="助手消息1", role="assistant"),
            DomainAgentMessage(content="用户消息2", role="user"),
            DomainAgentMessage(content="助手消息2", role="assistant"),
        ]
        
        # 获取最后一条助手消息
        last_assistant = adapter._get_last_assistant_message(messages)
        
        # 验证结果
        assert last_assistant == "助手消息2"
    
    def test_empty_state_conversion(self):
        """测试空状态转换"""
        adapter = StateAdapter()
        
        # 创建空域状态
        empty_domain = DomainAgentState()
        
        # 转换为图状态
        graph_state = adapter.to_graph_state(empty_domain)
        
        # 验证基础字段
        assert graph_state["agent_id"] == ""
        assert graph_state["input"] == ""
        assert graph_state["iteration_count"] == 0
        assert graph_state["complete"] is False
        
        # 转换回域状态
        converted_back = adapter.from_graph_state(graph_state)
        
        # 验证一致性
        assert converted_back.agent_id == ""
        assert converted_back.agent_type == ""
        assert converted_back.current_task == ""
        assert converted_back.iteration_count == 0
        assert converted_back.status == AgentStatus.RUNNING


if __name__ == "__main__":
    pytest.main([__file__])