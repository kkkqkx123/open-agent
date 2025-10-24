"""TUI应用集成测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.presentation.tui.app import TUIApp
from src.presentation.tui.config import TUIConfig


class TestTUIAppIntegration:
    """TUI应用集成测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock(spec=TUIConfig)
        config.theme.primary_color = "blue"
        config.behavior.refresh_rate = 10
        return config
    
    @pytest.fixture
    def tui_app(self, mock_config):
        """创建TUI应用实例"""
        with patch('src.presentation.tui.app.get_tui_config', return_value=mock_config):
            with patch('src.presentation.tui.app.get_global_container'):
                app = TUIApp()
                return app
    
    def test_app_initialization(self, tui_app):
        """测试应用初始化"""
        assert tui_app.config is not None
        assert tui_app.layout_manager is not None
        assert tui_app.current_subview is None
        assert tui_app.analytics_view is not None
        assert tui_app.visualization_view is not None
        assert tui_app.system_view is not None
        assert tui_app.errors_view is not None
    
    def test_subview_navigation(self, tui_app):
        """测试子界面导航"""
        # 测试切换到分析监控子界面
        tui_app.switch_to_subview("analytics")
        assert tui_app.current_subview == "analytics"
        
        # 测试切换到可视化调试子界面
        tui_app.switch_to_subview("visualization")
        assert tui_app.current_subview == "visualization"
        
        # 测试切换到系统管理子界面
        tui_app.switch_to_subview("system")
        assert tui_app.current_subview == "system"
        
        # 测试切换到错误反馈子界面
        tui_app.switch_to_subview("errors")
        assert tui_app.current_subview == "errors"
        
        # 测试返回主界面
        tui_app.return_to_main_view()
        assert tui_app.current_subview is None
    
    def test_invalid_subview_navigation(self, tui_app):
        """测试无效子界面导航"""
        # 尝试切换到无效子界面
        tui_app.switch_to_subview("invalid")
        assert tui_app.current_subview is None
    
    def test_command_handling(self, tui_app):
        """测试命令处理"""
        # 测试子界面切换命令
        tui_app._handle_command("analytics", [])
        assert tui_app.current_subview == "analytics"
        
        tui_app._handle_command("visualization", [])
        assert tui_app.current_subview == "visualization"
        
        tui_app._handle_command("system", [])
        assert tui_app.current_subview == "system"
        
        tui_app._handle_command("errors", [])
        assert tui_app.current_subview == "errors"
        
        tui_app._handle_command("main", [])
        assert tui_app.current_subview is None
        
        # 测试重定向命令
        tui_app._handle_command("studio", [])
        assert tui_app.current_subview == "system"
        
        tui_app._handle_command("performance", [])
        assert tui_app.current_subview == "analytics"
        
        tui_app._handle_command("debug", [])
        assert tui_app.current_subview == "visualization"
    
    def test_key_handling(self, tui_app):
        """测试按键处理"""
        # 测试子界面快捷键
        result = tui_app.handle_key("alt+1")
        assert result is True
        assert tui_app.current_subview == "analytics"
        
        result = tui_app.handle_key("alt+2")
        assert result is True
        assert tui_app.current_subview == "visualization"
        
        result = tui_app.handle_key("alt+3")
        assert result is True
        assert tui_app.current_subview == "system"
        
        result = tui_app.handle_key("alt+4")
        assert result is True
        assert tui_app.current_subview == "errors"
        
        # 测试ESC键返回
        result = tui_app.handle_key("escape")
        assert result is True
        assert tui_app.current_subview is None
    
    def test_subview_key_delegation(self, tui_app):
        """测试子界面按键委托"""
        # 切换到子界面
        tui_app.current_subview = "analytics"
        
        # 模拟子界面处理按键
        tui_app.analytics_view.handle_key = Mock(return_value=True)
        
        # 测试按键被委托给子界面
        result = tui_app.handle_key("r")  # 刷新键
        assert result is True
        tui_app.analytics_view.handle_key.assert_called_once_with("r")
    
    def test_ui_update_with_subview(self, tui_app):
        """测试子界面UI更新"""
        # 模拟Live对象
        mock_live = Mock()
        tui_app.live = mock_live
        
        # 切换到子界面
        tui_app.current_subview = "analytics"
        
        # 模拟子界面渲染
        mock_panel = Mock()
        tui_app.analytics_view.render = Mock(return_value=mock_panel)
        
        # 更新UI
        tui_app._update_ui()
        
        # 验证子界面被渲染
        tui_app.analytics_view.render.assert_called_once()
        mock_live.refresh.assert_called_once()
    
    def test_subview_data_update(self, tui_app):
        """测试子界面数据更新"""
        # 模拟Agent状态
        mock_state = Mock()
        mock_state.total_requests = 100
        mock_state.avg_response_time = 250.5
        mock_state.success_rate = 95.0
        mock_state.cpu_usage = 75.5
        mock_state.memory_usage = 60.2
        mock_state.workflow_nodes = [{"id": "node1", "type": "process"}]
        mock_state.current_step = "node1"
        mock_state.studio_running = True
        mock_state.studio_port = 8079
        mock_state.errors = [{"message": "Test error", "level": "error"}]
        
        tui_app.current_state = mock_state
        
        # 更新组件（包括子界面数据）
        tui_app._update_components()
        
        # 验证数据被传递到子界面
        assert tui_app.analytics_view.performance_data["total_requests"] == 100
        assert tui_app.system_view.studio_status["running"] is True
        assert len(tui_app.errors_view.error_list) == 1
    
    def test_status_bar_update(self, tui_app):
        """测试状态栏更新"""
        # 模拟Live对象
        mock_live = Mock()
        tui_app.live = mock_live
        
        # 设置会话ID
        tui_app.session_id = "test_session_12345678"
        
        # 更新状态栏
        tui_app._update_status_bar()
        
        # 验证状态栏被更新
        mock_live.refresh.assert_called_once()
    
    def test_help_command(self, tui_app):
        """测试帮助命令"""
        # 模拟主内容组件
        tui_app.main_content_component = Mock()
        tui_app.add_system_message = Mock()
        
        # 执行帮助命令
        tui_app._handle_command("help", [])
        
        # 验证帮助信息被显示
        tui_app.add_system_message.assert_called_once()
        tui_app.main_content_component.add_assistant_message.assert_called_once()
    
    def test_subview_callbacks(self, tui_app):
        """测试子界面回调"""
        # 测试Studio启动回调
        tui_app.add_system_message = Mock()
        tui_app._on_studio_started({"url": "http://localhost:8079"})
        tui_app.add_system_message.assert_called_with("Studio已启动: http://localhost:8079")
        
        # 测试Studio停止回调
        tui_app._on_studio_stopped({})
        tui_app.add_system_message.assert_called_with("Studio已停止")
        
        # 测试配置重载回调
        tui_app._on_config_reloaded({})
        tui_app.add_system_message.assert_called_with("配置已重载")
        
        # 测试错误反馈回调
        tui_app._on_error_feedback_submitted({"error_id": "error_1"})
        tui_app.add_system_message.assert_called_with("错误反馈已提交: error_1")
    
    def test_agent_selection_with_simplified_sidebar(self, tui_app):
        """测试Agent选择与精简侧边栏"""
        # 模拟Agent配置
        mock_agent_config = Mock()
        mock_agent_config.name = "Test Agent"
        mock_agent_config.model = "gpt-4"
        
        # 执行Agent选择
        tui_app._on_agent_selected(mock_agent_config)
        
        # 验证侧边栏被更新
        assert tui_app.sidebar_component.agent_info["name"] == "Test Agent"
        assert tui_app.sidebar_component.agent_info["model"] == "gpt-4"
    
    def test_complete_workflow(self, tui_app):
        """测试完整工作流程"""
        # 模拟Live对象
        mock_live = Mock()
        tui_app.live = mock_live
        
        # 1. 启动应用
        assert tui_app.running is True
        
        # 2. 切换到分析监控子界面
        tui_app.switch_to_subview("analytics")
        assert tui_app.current_subview == "analytics"
        
        # 3. 更新UI
        tui_app._update_ui()
        mock_live.refresh.assert_called()
        
        # 4. 切换到系统管理子界面
        tui_app.switch_to_subview("system")
        assert tui_app.current_subview == "system"
        
        # 5. 返回主界面
        tui_app.return_to_main_view()
        assert tui_app.current_subview is None
        
        # 6. 处理命令
        tui_app._handle_command("help", [])
        
        # 7. 处理按键
        tui_app.handle_key("alt+1")
        assert tui_app.current_subview == "analytics"
        
        # 8. 使用ESC返回
        tui_app.handle_key("escape")
        assert tui_app.current_subview is None


class TestTUIAppErrorHandling:
    """TUI应用错误处理测试"""
    
    @pytest.fixture
    def tui_app(self):
        """创建TUI应用实例"""
        with patch('src.presentation.tui.app.get_tui_config'):
            with patch('src.presentation.tui.app.get_global_container'):
                app = TUIApp()
                return app
    
    def test_invalid_command_handling(self, tui_app):
        """测试无效命令处理"""
        # 模拟控制台
        tui_app.console = Mock()
        
        # 执行无效命令
        tui_app._handle_command("invalid_command", [])
        
        # 验证错误消息被显示
        tui_app.console.print.assert_called()
    
    def test_subview_render_error_handling(self, tui_app):
        """测试子界面渲染错误处理"""
        # 模拟Live对象
        mock_live = Mock()
        tui_app.live = mock_live
        
        # 切换到子界面
        tui_app.current_subview = "analytics"
        
        # 模拟子界面渲染错误
        tui_app.analytics_view.render = Mock(side_effect=Exception("Render error"))
        
        # 更新UI应该不会抛出异常
        try:
            tui_app._update_ui()
        except Exception:
            pytest.fail("UI update should not raise exception")
    
    def test_callback_error_handling(self, tui_app):
        """测试回调错误处理"""
        # 模拟回调抛出异常
        tui_app.add_system_message = Mock(side_effect=Exception("Callback error"))
        
        # 执行回调应该不会抛出异常
        try:
            tui_app._on_studio_started({})
        except Exception:
            pytest.fail("Callback execution should not raise exception")


if __name__ == "__main__":
    pytest.main([__file__])
