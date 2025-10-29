"""TUI状态管理器单元测试

测试统一状态序列化/反序列化功能。
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.presentation.tui.state_manager import StateManager
from src.application.sessions.manager import ISessionManager
from src.domain.agent.state import AgentState
from src.infrastructure.graph.states.base import HumanMessage


class TestStateManager:
    """StateManager测试类"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """模拟会话管理器"""
        manager = Mock(spec=ISessionManager)
        manager.create_session.return_value = "test_session_id"
        manager.restore_session.return_value = (Mock(), AgentState())
        manager.save_session.return_value = True
        manager.delete_session.return_value = True
        return manager
    
    @pytest.fixture
    def state_manager(self, mock_session_manager):
        """创建StateManager实例"""
        return StateManager(session_manager=mock_session_manager)
    
    @pytest.fixture
    def state_manager_no_session(self):
        """创建没有会话管理器的StateManager实例"""
        return StateManager(session_manager=None)
    
    def test_init_with_session_manager(self, mock_session_manager):
        """测试带会话管理器的初始化"""
        manager = StateManager(session_manager=mock_session_manager)
        
        assert manager.session_manager == mock_session_manager
        assert manager.session_id is None
        assert manager.current_state is None
        assert manager.current_workflow is None
        assert manager.message_history == []
        assert manager.input_buffer == ""
        assert manager._user_message_hooks == []
        assert manager._assistant_message_hooks == []
        assert manager._tool_call_hooks == []
        assert manager._show_session_dialog is False
        assert manager._show_agent_dialog is False
        assert manager.current_subview is None
    
    def test_init_without_session_manager(self):
        """测试不带会话管理器的初始化"""
        manager = StateManager(session_manager=None)
        
        assert manager.session_manager is None
        assert manager.session_id is None
        assert manager.current_state is None
        assert manager.current_workflow is None
        assert manager.message_history == []
        assert manager.input_buffer == ""
    
    def test_add_user_message_hook(self, state_manager):
        """测试添加用户消息钩子"""
        hook = Mock()
        state_manager.add_user_message_hook(hook)
        
        assert hook in state_manager._user_message_hooks
    
    def test_add_assistant_message_hook(self, state_manager):
        """测试添加助手消息钩子"""
        hook = Mock()
        state_manager.add_assistant_message_hook(hook)
        
        assert hook in state_manager._assistant_message_hooks
    
    def test_add_tool_call_hook(self, state_manager):
        """测试添加工具调用钩子"""
        hook = Mock()
        state_manager.add_tool_call_hook(hook)
        
        assert hook in state_manager._tool_call_hooks
    
    def test_create_session_success(self, state_manager, mock_session_manager):
        """测试成功创建会话"""
        workflow_config = "test_workflow.yaml"
        agent_config = "test_agent.yaml"
        
        result = state_manager.create_session(workflow_config, agent_config)
        
        assert result is True
        assert state_manager.session_id == "test_session_id"
        assert state_manager.current_state is not None
        assert state_manager.current_workflow is not None
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "system"
        assert "test_session_id" in state_manager.message_history[0]["content"]
        
        # 验证会话管理器调用
        mock_session_manager.create_session.assert_called_once_with(
            workflow_config_path=workflow_config,
            agent_config={}
        )
        mock_session_manager.restore_session.assert_called_once_with("test_session_id")
    
    def test_create_session_without_agent_config(self, state_manager, mock_session_manager):
        """测试不指定代理配置创建会话"""
        workflow_config = "test_workflow.yaml"
        
        result = state_manager.create_session(workflow_config)
        
        assert result is True
        
        # 验证会话管理器调用
        mock_session_manager.create_session.assert_called_once_with(
            workflow_config_path=workflow_config,
            agent_config=None
        )
    
    def test_create_session_no_manager(self, state_manager_no_session):
        """测试没有会话管理器时创建会话"""
        workflow_config = "test_workflow.yaml"
        
        result = state_manager_no_session.create_session(workflow_config)
        
        assert result is False
        assert state_manager_no_session.session_id is None
        assert state_manager_no_session.current_state is None
        assert state_manager_no_session.current_workflow is None
    
    def test_create_session_exception(self, state_manager, mock_session_manager):
        """测试创建会话时发生异常"""
        mock_session_manager.create_session.side_effect = Exception("Test error")
        
        result = state_manager.create_session("test_workflow.yaml")
        
        assert result is False
        assert state_manager.session_id is None
        assert state_manager.current_state is None
        assert state_manager.current_workflow is None
    
    def test_load_session_success(self, state_manager, mock_session_manager):
        """测试成功加载会话"""
        session_id = "test_session_id"
        
        result = state_manager.load_session(session_id)
        
        assert result is True
        assert state_manager.session_id == session_id
        assert state_manager.current_state is not None
        assert state_manager.current_workflow is not None
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "system"
        assert session_id in state_manager.message_history[0]["content"]
        
        # 验证会话管理器调用
        mock_session_manager.restore_session.assert_called_once_with(session_id)
    
    def test_load_session_no_manager(self, state_manager_no_session):
        """测试没有会话管理器时加载会话"""
        session_id = "test_session_id"
        
        result = state_manager_no_session.load_session(session_id)
        
        assert result is False
        assert state_manager_no_session.session_id is None
    
    def test_load_session_exception(self, state_manager, mock_session_manager):
        """测试加载会话时发生异常"""
        mock_session_manager.restore_session.side_effect = Exception("Test error")
        
        result = state_manager.load_session("test_session_id")
        
        assert result is False
        assert state_manager.session_id is None
    
    def test_save_session_success(self, state_manager, mock_session_manager):
        """测试成功保存会话"""
        # 设置会话状态
        state_manager.session_id = "test_session_id"
        state_manager.current_state = AgentState()
        state_manager.current_workflow = Mock()
        
        result = state_manager.save_session()
        
        assert result is True
        
        # 验证会话管理器调用
        mock_session_manager.save_session.assert_called_once_with(
            "test_session_id", state_manager.current_workflow, state_manager.current_state
        )
    
    def test_save_session_no_manager(self, state_manager_no_session):
        """测试没有会话管理器时保存会话"""
        state_manager_no_session.session_id = "test_session_id"
        state_manager_no_session.current_state = AgentState()
        state_manager_no_session.current_workflow = Mock()
        
        result = state_manager_no_session.save_session()
        
        assert result is False
    
    def test_save_session_missing_data(self, state_manager):
        """测试保存会话时缺少必要数据"""
        # 缺少session_id
        state_manager.current_state = AgentState()
        state_manager.current_workflow = Mock()
        
        result = state_manager.save_session()
        assert result is False
        
        # 缺少current_state
        state_manager.session_id = "test_session_id"
        state_manager.current_state = None
        
        result = state_manager.save_session()
        assert result is False
    
    def test_save_session_exception(self, state_manager, mock_session_manager):
        """测试保存会话时发生异常"""
        state_manager.session_id = "test_session_id"
        state_manager.current_state = AgentState()
        state_manager.current_workflow = Mock()
        
        mock_session_manager.save_session.side_effect = Exception("Test error")
        
        result = state_manager.save_session()
        
        assert result is False
    
    def test_delete_session_success(self, state_manager, mock_session_manager):
        """测试成功删除会话"""
        session_id = "test_session_id"
        
        result = state_manager.delete_session(session_id)
        
        assert result is True
        
        # 验证会话管理器调用
        mock_session_manager.delete_session.assert_called_once_with(session_id)
    
    def test_delete_session_current_session(self, state_manager, mock_session_manager):
        """测试删除当前会话"""
        session_id = "test_session_id"
        state_manager.session_id = session_id
        state_manager.current_state = AgentState()
        state_manager.current_workflow = Mock()
        state_manager.message_history = [{"type": "test"}]
        
        result = state_manager.delete_session(session_id)
        
        assert result is True
        assert state_manager.session_id is None
        assert state_manager.current_state is None
        assert state_manager.current_workflow is None
        assert state_manager.message_history == []
    
    def test_delete_session_no_manager(self, state_manager_no_session):
        """测试没有会话管理器时删除会话"""
        session_id = "test_session_id"
        
        result = state_manager_no_session.delete_session(session_id)
        
        assert result is False
    
    def test_delete_session_exception(self, state_manager, mock_session_manager):
        """测试删除会话时发生异常"""
        mock_session_manager.delete_session.side_effect = Exception("Test error")
        
        result = state_manager.delete_session("test_session_id")
        
        assert result is False
    
    def test_create_new_session(self, state_manager):
        """测试创建新会话（重置状态）"""
        # 设置一些状态
        state_manager.session_id = "old_session_id"
        state_manager.current_state = Mock()
        state_manager.current_workflow = Mock()
        state_manager.message_history = [{"type": "test"}]
        state_manager.input_buffer = "test_input"
        
        state_manager.create_new_session()
        
        assert state_manager.session_id is None
        assert isinstance(state_manager.current_state, AgentState)
        assert state_manager.current_workflow is None
        assert state_manager.message_history == []
        assert state_manager.input_buffer == ""
    
    def test_add_user_message(self, state_manager):
        """测试添加用户消息"""
        content = "Test user message"
        hook = Mock()
        state_manager.add_user_message_hook(hook)
        
        # 设置当前状态
        state_manager.current_state = AgentState()
        
        state_manager.add_user_message(content)
        
        # 验证消息历史
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "user"
        assert state_manager.message_history[0]["content"] == content
        
        # 验证钩子调用
        hook.assert_called_once_with(content)
        
        # 验证状态更新
        assert len(state_manager.current_state.get("messages", [])) > 0
    
    def test_add_user_message_no_state(self, state_manager):
        """测试没有当前状态时添加用户消息"""
        content = "Test user message"
        hook = Mock()
        state_manager.add_user_message_hook(hook)
        
        state_manager.add_user_message(content)
        
        # 验证消息历史
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "user"
        assert state_manager.message_history[0]["content"] == content
        
        # 验证钩子调用
        hook.assert_called_once_with(content)
    
    def test_add_user_message_hook_exception(self, state_manager):
        """测试用户消息钩子异常"""
        content = "Test user message"
        hook = Mock(side_effect=Exception("Hook error"))
        state_manager.add_user_message_hook(hook)
        
        # 不应该抛出异常
        state_manager.add_user_message(content)
        
        # 验证消息历史仍然添加
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "user"
        assert state_manager.message_history[0]["content"] == content
    
    def test_add_assistant_message(self, state_manager):
        """测试添加助手消息"""
        content = "Test assistant message"
        hook = Mock()
        state_manager.add_assistant_message_hook(hook)
        
        state_manager.add_assistant_message(content)
        
        # 验证消息历史
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "assistant"
        assert state_manager.message_history[0]["content"] == content
        
        # 验证钩子调用
        hook.assert_called_once_with(content)
    
    def test_add_assistant_message_hook_exception(self, state_manager):
        """测试助手消息钩子异常"""
        content = "Test assistant message"
        hook = Mock(side_effect=Exception("Hook error"))
        state_manager.add_assistant_message_hook(hook)
        
        # 不应该抛出异常
        state_manager.add_assistant_message(content)
        
        # 验证消息历史仍然添加
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "assistant"
        assert state_manager.message_history[0]["content"] == content
    
    def test_add_tool_call(self, state_manager):
        """测试添加工具调用记录"""
        tool_name = "test_tool"
        tool_input = {"param": "value"}
        tool_output = {"result": "success"}
        hook = Mock()
        state_manager.add_tool_call_hook(hook)
        
        state_manager.add_tool_call(tool_name, tool_input, tool_output)
        
        # 验证消息历史
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "tool_call"
        assert state_manager.message_history[0]["tool_name"] == tool_name
        assert state_manager.message_history[0]["tool_input"] == tool_input
        assert state_manager.message_history[0]["tool_output"] == tool_output
        
        # 验证钩子调用
        hook.assert_called_once_with(tool_name, tool_input, tool_output)
    
    def test_add_tool_call_no_output(self, state_manager):
        """测试添加工具调用记录（无输出）"""
        tool_name = "test_tool"
        tool_input = {"param": "value"}
        
        state_manager.add_tool_call(tool_name, tool_input)
        
        # 验证消息历史
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "tool_call"
        assert state_manager.message_history[0]["tool_name"] == tool_name
        assert state_manager.message_history[0]["tool_input"] == tool_input
        assert state_manager.message_history[0]["tool_output"] is None
    
    def test_add_tool_call_hook_exception(self, state_manager):
        """测试工具调用钩子异常"""
        tool_name = "test_tool"
        tool_input = {"param": "value"}
        hook = Mock(side_effect=Exception("Hook error"))
        state_manager.add_tool_call_hook(hook)
        
        # 不应该抛出异常
        state_manager.add_tool_call(tool_name, tool_input)
        
        # 验证消息历史仍然添加
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "tool_call"
        assert state_manager.message_history[0]["tool_name"] == tool_name
        assert state_manager.message_history[0]["tool_input"] == tool_input
    
    def test_add_system_message(self, state_manager):
        """测试添加系统消息"""
        content = "Test system message"
        
        state_manager.add_system_message(content)
        
        # 验证消息历史
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "system"
        assert state_manager.message_history[0]["content"] == content
    
    def test_set_input_buffer(self, state_manager):
        """测试设置输入缓冲区"""
        text = "Test input"
        
        state_manager.set_input_buffer(text)
        
        assert state_manager.input_buffer == text
    
    def test_clear_input_buffer(self, state_manager):
        """测试清空输入缓冲区"""
        state_manager.input_buffer = "Test input"
        
        state_manager.clear_input_buffer()
        
        assert state_manager.input_buffer == ""
    
    def test_clear_message_history(self, state_manager):
        """测试清空消息历史"""
        state_manager.message_history = [{"type": "test"}]
        
        state_manager.clear_message_history()
        
        assert state_manager.message_history == []
    
    def test_switch_to_subview_valid(self, state_manager):
        """测试切换到有效子界面"""
        result = state_manager.switch_to_subview("analytics")
        
        assert result is True
        assert state_manager.current_subview == "analytics"
    
    def test_switch_to_subview_invalid(self, state_manager):
        """测试切换到无效子界面"""
        result = state_manager.switch_to_subview("invalid")
        
        assert result is False
        assert state_manager.current_subview is None
    
    def test_return_to_main_view(self, state_manager):
        """测试返回主界面"""
        state_manager.current_subview = "analytics"
        
        state_manager.return_to_main_view()
        
        assert state_manager.current_subview is None
    
    def test_set_show_session_dialog(self, state_manager):
        """测试显示/隐藏会话对话框"""
        # 测试显示
        state_manager.set_show_session_dialog(True)
        assert state_manager.show_session_dialog is True
        
        # 测试隐藏
        state_manager.set_show_session_dialog(False)
        assert state_manager.show_session_dialog is False
    
    def test_set_show_agent_dialog(self, state_manager):
        """测试显示/隐藏Agent对话框"""
        # 测试显示
        state_manager.set_show_agent_dialog(True)
        assert state_manager.show_agent_dialog is True
        
        # 测试隐藏
        state_manager.set_show_agent_dialog(False)
        assert state_manager.show_agent_dialog is False
    
    def test_get_performance_data_no_state(self, state_manager):
        """测试获取性能数据（无状态）"""
        data = state_manager.get_performance_data()
        
        assert data == {}
    
    def test_get_performance_data_with_state(self, state_manager):
        """测试获取性能数据（有状态）"""
        state_manager.current_state = AgentState()
        state_manager.current_state.total_requests = 100
        state_manager.current_state.avg_response_time = 0.5
        state_manager.current_state.success_rate = 95.0
        state_manager.current_state.error_count = 5
        state_manager.current_state.tokens_used = 1000
        state_manager.current_state.cost_estimate = 0.1
        
        data = state_manager.get_performance_data()
        
        assert data["total_requests"] == 100
        assert data["avg_response_time"] == 0.5
        assert data["success_rate"] == 95.0
        assert data["error_count"] == 5
        assert data["tokens_used"] == 1000
        assert data["cost_estimate"] == 0.1
    
    def test_get_system_metrics_no_state(self, state_manager):
        """测试获取系统指标（无状态）"""
        data = state_manager.get_system_metrics()
        
        assert data == {}
    
    def test_get_system_metrics_with_state(self, state_manager):
        """测试获取系统指标（有状态）"""
        state_manager.current_state = AgentState()
        state_manager.current_state.cpu_usage = 50.0
        state_manager.current_state.memory_usage = 60.0
        state_manager.current_state.disk_usage = 70.0
        state_manager.current_state.network_io = 80.0
        
        data = state_manager.get_system_metrics()
        
        assert data["cpu_usage"] == 50.0
        assert data["memory_usage"] == 60.0
        assert data["disk_usage"] == 70.0
        assert data["network_io"] == 80.0
    
    def test_get_workflow_data_no_state(self, state_manager):
        """测试获取工作流数据（无状态）"""
        data = state_manager.get_workflow_data()
        
        assert data == {}
    
    def test_get_workflow_data_with_state(self, state_manager):
        """测试获取工作流数据（有状态）"""
        state_manager.current_state = AgentState()
        state_manager.current_state.workflow_nodes = ["node1", "node2"]
        state_manager.current_state.workflow_edges = [("node1", "node2")]
        state_manager.current_state.current_step = "node2"
        state_manager.current_state.execution_path = ["node1", "node2"]
        state_manager.current_state.node_states = {"node1": "completed", "node2": "running"}
        
        data = state_manager.get_workflow_data()
        
        assert data["nodes"] == ["node1", "node2"]
        assert data["edges"] == [("node1", "node2")]
        assert data["current_node"] == "node2"
        assert data["execution_path"] == ["node1", "node2"]
        assert data["node_states"] == {"node1": "completed", "node2": "running"}
    
    def test_get_studio_status_no_state(self, state_manager):
        """测试获取Studio状态（无状态）"""
        data = state_manager.get_studio_status()
        
        assert data == {}
    
    def test_get_studio_status_with_state(self, state_manager):
        """测试获取Studio状态（有状态）"""
        state_manager.current_state = AgentState()
        state_manager.current_state.studio_running = True
        state_manager.current_state.studio_port = 8080
        state_manager.current_state.studio_url = "http://localhost:8080"
        state_manager.current_state.studio_start_time = "2023-01-01T00:00:00"
        state_manager.current_state.studio_clients = 5
        
        data = state_manager.get_studio_status()
        
        assert data["running"] is True
        assert data["port"] == 8080
        assert data["url"] == "http://localhost:8080"
        assert data["start_time"] == "2023-01-01T00:00:00"
        assert data["version"] == "1.0.0"
        assert data["connected_clients"] == 5
    
    def test_get_errors_no_state(self, state_manager):
        """测试获取错误列表（无状态）"""
        errors = state_manager.get_errors()
        
        assert errors == []
    
    def test_get_errors_no_errors_attribute(self, state_manager):
        """测试获取错误列表（无errors属性）"""
        state_manager.current_state = AgentState()
        # 不设置errors属性
        
        errors = state_manager.get_errors()
        
        assert errors == []
    
    def test_get_errors_with_errors(self, state_manager):
        """测试获取错误列表（有错误）"""
        state_manager.current_state = AgentState()
        state_manager.current_state.errors = ["Error 1", "Error 2"]
        
        errors = state_manager.get_errors()
        
        assert len(errors) == 2
        assert errors[0] == "Error 1"
        assert errors[1] == "Error 2"
    
    def test_get_errors_none_errors(self, state_manager):
        """测试获取错误列表（errors为None）"""
        state_manager.current_state = AgentState()
        state_manager.current_state.errors = None
        
        errors = state_manager.get_errors()
        
        assert errors == []