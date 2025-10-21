"""TUI状态管理器单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Optional, Dict, Any, List

from src.presentation.tui.state_manager import StateManager
from src.session.manager import ISessionManager
from src.prompts.agent_state import AgentState


class TestStateManager:
    """测试状态管理器类"""
    
    def test_state_manager_init(self):
        """测试状态管理器初始化"""
        manager = StateManager()
        
        assert manager.session_manager is None
        assert manager.session_id is None
        assert manager.current_state is None
        assert manager.current_workflow is None
        assert manager.message_history == []
        assert manager.input_buffer == ""
        assert manager.show_session_dialog is False
        assert manager.show_agent_dialog is False
        assert manager.current_subview is None
    
    def test_state_manager_init_with_session_manager(self):
        """测试使用会话管理器初始化状态管理器"""
        mock_session_manager = Mock(spec=ISessionManager)
        manager = StateManager(session_manager=mock_session_manager)
        
        assert manager.session_manager == mock_session_manager
    
    def test_create_session_without_session_manager(self):
        """测试没有会话管理器时创建会话"""
        manager = StateManager()
        
        result = manager.create_session("workflow_config")
        
        assert result is False
    
    def test_create_session_success(self):
        """测试成功创建会话"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.create_session.return_value = "session_123"
        mock_session_manager.restore_session.return_value = (Mock(), Mock())
        
        manager = StateManager(session_manager=mock_session_manager)
        
        result = manager.create_session("workflow_config")
        
        assert result is True
        assert manager.session_id == "session_123"
        assert manager.current_workflow is not None
        assert manager.current_state is not None
        assert len(manager.message_history) == 1
        assert manager.message_history[0]["type"] == "system"
        assert "session_123"[:8] in manager.message_history[0]["content"]
    
    def test_create_session_failure(self):
        """测试创建会话失败"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.create_session.side_effect = Exception("Creation failed")
        
        manager = StateManager(session_manager=mock_session_manager)
        
        result = manager.create_session("workflow_config")
        
        assert result is False
    
    def test_load_session_without_session_manager(self):
        """测试没有会话管理器时加载会话"""
        manager = StateManager()
        
        result = manager.load_session("session_123")
        
        assert result is False
    
    def test_load_session_success(self):
        """测试成功加载会话"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_workflow = Mock()
        mock_state = Mock()
        mock_session_manager.restore_session.return_value = (mock_workflow, mock_state)
        
        manager = StateManager(session_manager=mock_session_manager)
        
        result = manager.load_session("session_123")
        
        assert result is True
        assert manager.session_id == "session_123"
        assert manager.current_workflow == mock_workflow
        assert manager.current_state == mock_state
        assert len(manager.message_history) == 1
        assert manager.message_history[0]["type"] == "system"
        assert "session_123"[:8] in manager.message_history[0]["content"]
    
    def test_load_session_failure(self):
        """测试加载会话失败"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.restore_session.side_effect = Exception("Load failed")
        
        manager = StateManager(session_manager=mock_session_manager)
        
        result = manager.load_session("session_123")
        
        assert result is False
    
    def test_save_session_without_session_id(self):
        """测试没有会话ID时保存会话"""
        manager = StateManager()
        
        result = manager.save_session()
        
        assert result is False
    
    def test_save_session_without_current_state(self):
        """测试没有当前状态时保存会话"""
        manager = StateManager()
        manager.session_id = "session_123"
        
        result = manager.save_session()
        
        assert result is False
    
    def test_save_session_without_session_manager(self):
        """测试没有会话管理器时保存会话"""
        manager = StateManager()
        manager.session_id = "session_123"
        manager.current_state = Mock()
        
        result = manager.save_session()
        
        assert result is False
    
    def test_save_session_success(self):
        """测试成功保存会话"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.save_session.return_value = True
        
        manager = StateManager(session_manager=mock_session_manager)
        manager.session_id = "session_123"
        manager.current_workflow = Mock()
        manager.current_state = Mock()
        
        result = manager.save_session()
        
        assert result is True
        mock_session_manager.save_session.assert_called_once_with(
            "session_123", manager.current_workflow, manager.current_state
        )
    
    def test_save_session_failure(self):
        """测试保存会话失败"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.save_session.side_effect = Exception("Save failed")
        
        manager = StateManager(session_manager=mock_session_manager)
        manager.session_id = "session_123"
        manager.current_workflow = Mock()
        manager.current_state = Mock()
        
        result = manager.save_session()
        
        assert result is False
    
    def test_delete_session_without_session_manager(self):
        """测试没有会话管理器时删除会话"""
        manager = StateManager()
        
        result = manager.delete_session("session_123")
        
        assert result is False
    
    def test_delete_session_success(self):
        """测试成功删除会话"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.delete_session.return_value = True
        
        manager = StateManager(session_manager=mock_session_manager)
        manager.session_id = "session_123"
        
        result = manager.delete_session("session_123")
        
        assert result is True
        assert manager.session_id is None
        assert manager.current_state is None
        assert manager.current_workflow is None
        assert manager.message_history == []
    
    def test_delete_session_not_current(self):
        """测试删除非当前会话"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.delete_session.return_value = True
        
        manager = StateManager(session_manager=mock_session_manager)
        manager.session_id = "session_456"  # 不同的会话ID
        
        result = manager.delete_session("session_123")
        
        assert result is True
        assert manager.session_id == "session_456"  # 当前会话未改变
    
    def test_delete_session_failure(self):
        """测试删除会话失败"""
        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.delete_session.return_value = False
        
        manager = StateManager(session_manager=mock_session_manager)
        
        result = manager.delete_session("session_123")
        
        assert result is False
    
    def test_create_new_session(self):
        """测试创建新会话（重置状态）"""
        manager = StateManager()
        manager.session_id = "old_session"
        manager.current_state = Mock()
        manager.current_workflow = Mock()
        manager.message_history = [{"type": "user", "content": "test"}]
        manager.input_buffer = "test input"
        
        manager.create_new_session()
        
        assert manager.session_id is None
        assert manager.current_state is not None # 应该是新的AgentState实例
        assert manager.current_workflow is None
        assert manager.message_history == []
        assert manager.input_buffer == ""
    
    def test_add_user_message(self):
        """测试添加用户消息"""
        manager = StateManager()
        mock_state = Mock()
        manager.current_state = mock_state
        
        manager.add_user_message("Hello, world!")
        
        assert len(manager.message_history) == 1
        assert manager.message_history[0]["type"] == "user"
        assert manager.message_history[0]["content"] == "Hello, world!"
        
        # 验证状态中的消息也被添加
        assert mock_state.add_message.called
    
    def test_add_user_message_with_human_message_error(self):
        """测试添加用户消息时HumanMessage不可用"""
        manager = StateManager()
        mock_state = Mock()
        manager.current_state = mock_state
        
        # 模拟add_message方法抛出异常
        mock_state.add_message.side_effect = [Exception(), None]
        
        manager.add_user_message("Hello, world!")
        
        # 验证即使第一次调用失败，也会尝试其他方式添加消息
        assert len(manager.message_history) == 1
        assert manager.message_history[0]["type"] == "user"
        assert manager.message_history[0]["content"] == "Hello, world!"
    
    def test_add_assistant_message(self):
        """测试添加助手消息"""
        manager = StateManager()
        
        manager.add_assistant_message("Hi there!")
        
        assert len(manager.message_history) == 1
        assert manager.message_history[0]["type"] == "assistant"
        assert manager.message_history[0]["content"] == "Hi there!"
    
    def test_add_system_message(self):
        """测试添加系统消息"""
        manager = StateManager()
        
        manager.add_system_message("System message")
        
        assert len(manager.message_history) == 1
        assert manager.message_history[0]["type"] == "system"
        assert manager.message_history[0]["content"] == "System message"
    
    def test_set_input_buffer(self):
        """测试设置输入缓冲区"""
        manager = StateManager()
        
        manager.set_input_buffer("test input")
        
        assert manager.input_buffer == "test input"
    
    def test_clear_input_buffer(self):
        """测试清空输入缓冲区"""
        manager = StateManager()
        manager.input_buffer = "test input"
        
        manager.clear_input_buffer()
        
        assert manager.input_buffer == ""
    
    def test_clear_message_history(self):
        """测试清空消息历史"""
        manager = StateManager()
        manager.message_history = [
            {"type": "user", "content": "Hello"},
            {"type": "assistant", "content": "Hi"}
        ]
        
        manager.clear_message_history()
        
        assert manager.message_history == []
    
    def test_switch_to_subview(self):
        """测试切换到子界面"""
        manager = StateManager()
        
        # 测试有效的子界面
        result = manager.switch_to_subview("analytics")
        assert result is True
        assert manager.current_subview == "analytics"
        
        result = manager.switch_to_subview("visualization")
        assert result is True
        assert manager.current_subview == "visualization"
        
        result = manager.switch_to_subview("system")
        assert result is True
        assert manager.current_subview == "system"
        
        result = manager.switch_to_subview("errors")
        assert result is True
        assert manager.current_subview == "errors"
        
        # 测试无效的子界面
        result = manager.switch_to_subview("invalid")
        assert result is False
        assert manager.current_subview == "errors"  # 保持原值
    
    def test_return_to_main_view(self):
        """测试返回主界面"""
        manager = StateManager()
        manager.current_subview = "analytics"
        
        manager.return_to_main_view()
        
        assert manager.current_subview is None
    
    def test_set_show_session_dialog(self):
        """测试设置会话对话框显示状态"""
        manager = StateManager()
        
        manager.set_show_session_dialog(True)
        assert manager.show_session_dialog is True
        
        manager.set_show_session_dialog(False)
        assert manager.show_session_dialog is False
    
    def test_set_show_agent_dialog(self):
        """测试设置Agent对话框显示状态"""
        manager = StateManager()
        
        manager.set_show_agent_dialog(True)
        assert manager.show_agent_dialog is True
        
        manager.set_show_agent_dialog(False)
        assert manager.show_agent_dialog is False
    
    def test_get_performance_data_with_state(self):
        """测试获取性能数据（有状态）"""
        manager = StateManager()
        mock_state = Mock()
        
        # 设置状态属性
        mock_state.total_requests = 10
        mock_state.avg_response_time = 200.0
        mock_state.success_rate = 95.0
        mock_state.error_count = 1
        mock_state.tokens_used = 500
        mock_state.cost_estimate = 0.05
        
        manager.current_state = mock_state
        
        performance_data = manager.get_performance_data()
        
        assert performance_data["total_requests"] == 10
        assert performance_data["avg_response_time"] == 200.0
        assert performance_data["success_rate"] == 95.0
        assert performance_data["error_count"] == 1
        assert performance_data["tokens_used"] == 500
        assert performance_data["cost_estimate"] == 0.05
    
    def test_get_performance_data_without_state(self):
        """测试获取性能数据（无状态）"""
        manager = StateManager()
        
        performance_data = manager.get_performance_data()
        
        assert performance_data == {}
    
    def test_get_system_metrics_with_state(self):
        """测试获取系统指标（有状态）"""
        manager = StateManager()
        mock_state = Mock()
        
        # 设置状态属性
        mock_state.cpu_usage = 50.0
        mock_state.memory_usage = 60.0
        mock_state.disk_usage = 70.0
        mock_state.network_io = 80.0
        
        manager.current_state = mock_state
        
        metrics_data = manager.get_system_metrics()
        
        assert metrics_data["cpu_usage"] == 50.0
        assert metrics_data["memory_usage"] == 60.0
        assert metrics_data["disk_usage"] == 70.0
        assert metrics_data["network_io"] == 80.0
    
    def test_get_system_metrics_without_state(self):
        """测试获取系统指标（无状态）"""
        manager = StateManager()
        
        metrics_data = manager.get_system_metrics()
        
        assert metrics_data == {}
    
    def test_get_workflow_data_with_state(self):
        """测试获取工作流数据（有状态）"""
        manager = StateManager()
        mock_state = Mock()
        
        # 设置状态属性
        mock_state.workflow_nodes = ["node1", "node2"]
        mock_state.workflow_edges = ["edge1", "edge2"]
        mock_state.current_step = "node1"
        mock_state.execution_path = ["node1"]
        mock_state.node_states = {"node1": "running"}
        
        manager.current_state = mock_state
        
        workflow_data = manager.get_workflow_data()
        
        assert workflow_data["nodes"] == ["node1", "node2"]
        assert workflow_data["edges"] == ["edge1", "edge2"]
        assert workflow_data["current_node"] == "node1"
        assert workflow_data["execution_path"] == ["node1"]
        assert workflow_data["node_states"] == {"node1": "running"}
    
    def test_get_workflow_data_without_state(self):
        """测试获取工作流数据（无状态）"""
        manager = StateManager()
        
        workflow_data = manager.get_workflow_data()
        
        assert workflow_data == {}
    
    def test_get_studio_status_with_state(self):
        """测试获取Studio状态（有状态）"""
        manager = StateManager()
        mock_state = Mock()
        
        # 设置状态属性
        mock_state.studio_running = True
        mock_state.studio_port = 8080
        mock_state.studio_url = "http://localhost:8080"
        mock_state.studio_start_time = "2023-01-01"
        mock_state.studio_clients = 2
        
        manager.current_state = mock_state
        
        studio_status = manager.get_studio_status()
        
        assert studio_status["running"] is True
        assert studio_status["port"] == 8080
        assert studio_status["url"] == "http://localhost:8080"
        assert studio_status["start_time"] == "2023-01-01"
        assert studio_status["version"] == "1.0.0"
        assert studio_status["connected_clients"] == 2
    
    def test_get_studio_status_without_state(self):
        """测试获取Studio状态（无状态）"""
        manager = StateManager()
        
        studio_status = manager.get_studio_status()
        
        assert studio_status == {}
    
    def test_get_errors_with_state(self):
        """测试获取错误列表（有状态）"""
        manager = StateManager()
        mock_state = Mock()
        
        # 设置状态属性
        mock_state.errors = [{"error_id": "1", "message": "Error 1"}]
        
        manager.current_state = mock_state
        
        errors = manager.get_errors()
        
        assert errors == [{"error_id": "1", "message": "Error 1"}]
    
    def test_get_errors_without_state(self):
        """测试获取错误列表（无状态）"""
        manager = StateManager()
        
        errors = manager.get_errors()
        
        assert errors == []
    
    def test_get_errors_without_errors_attr(self):
        """测试获取错误列表（无errors属性）"""
        manager = StateManager()
        mock_state = Mock()
        # 不设置errors属性
        type(mock_state).errors = None  # 设置为None而不是完全不设置
        
        manager.current_state = mock_state
        
        errors = manager.get_errors()
        
        assert errors == []
    
    def test_get_errors_with_none_errors(self):
        """测试获取错误列表（errors为None）"""
        manager = StateManager()
        mock_state = Mock()
        mock_state.errors = None
        
        manager.current_state = mock_state
        
        errors = manager.get_errors()
        
        assert errors == []