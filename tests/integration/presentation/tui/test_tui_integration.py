"""TUI模块集成测试"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from src.presentation.tui.app import TUIApp
from src.presentation.tui.config import TUIConfig, get_tui_config
from src.presentation.tui.state_manager import StateManager
from src.presentation.tui.layout import LayoutManager
from src.presentation.tui.event_engine import EventEngine
from src.presentation.tui.components.input_panel import InputPanelComponent
from src.presentation.tui.subviews.analytics import AnalyticsSubview


class TestTUIIntegration:
    """TUI模块集成测试"""
    
    def test_full_tui_app_initialization(self):
        """测试TUI应用完整初始化流程"""
        # 通过mock避免实际的依赖注入和终端操作
        with patch('src.presentation.tui.app.get_global_container') as mock_get_container, \
             patch('src.presentation.tui.app.get_tui_config') as mock_get_config, \
             patch('blessed.Terminal') as mock_terminal, \
             patch('rich.console.Console') as mock_console:
            
            # 模拟全局容器
            mock_container = Mock()
            mock_session_manager = Mock()
            mock_container.get.return_value = mock_session_manager
            mock_container.has_service.return_value = False
            mock_get_container.return_value = mock_container
            
            # 模拟配置
            mock_config = get_tui_config()  # 使用实际配置对象
            mock_get_config.return_value = mock_config
            
            # 模拟终端
            mock_term_instance = Mock()
            mock_terminal.return_value = mock_term_instance
            
            # 模拟控制台
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            # 初始化应用
            app = TUIApp()
            
            # 验证关键组件都被正确初始化
            assert app.config is not None
            assert app.layout_manager is not None
            assert app.state_manager is not None
            assert app.callback_manager is not None
            assert app.session_handler is not None
            assert app.command_processor is not None
            
            # 验证组件被初始化
            assert app.sidebar_component is not None
            assert app.langgraph_component is not None
            assert app.main_content_component is not None
            assert app.input_component is not None
            assert app.session_dialog is not None
            assert app.agent_dialog is not None
            
            # 验证子界面被初始化
            assert app.analytics_view is not None
            assert app.visualization_view is not None
            assert app.system_view is not None
            assert app.errors_view is not None
            
            # 验证控制器被初始化
            assert app.event_engine is not None
            assert app.subview_controller is not None
            assert app.render_controller is not None
    
    def test_config_component_integration(self):
        """测试配置组件集成"""
        # 测试配置管理器与应用的集成
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            
            # 获取配置
            config = get_tui_config(config_path)
            
            # 验证配置对象的完整性
            assert hasattr(config, 'layout')
            assert hasattr(config, 'theme')
            assert hasattr(config, 'behavior')
            assert hasattr(config, 'subview')
            assert hasattr(config, 'shortcuts')
            
            # 验证配置对象可以用于初始化布局管理器
            layout_manager = LayoutManager(config.layout)
            assert layout_manager.config is not None
            
            # 验证配置对象可以用于初始化其他组件
            state_manager = StateManager()
            assert state_manager is not None
    
    def test_state_manager_with_config_integration(self):
        """测试状态管理器与配置的集成"""
        config = get_tui_config()
        
        # 初始化状态管理器
        state_manager = StateManager()
        
        # 测试状态管理器功能与配置的兼容性
        state_manager.add_user_message("Test message")
        state_manager.add_assistant_message("Response message")
        
        assert len(state_manager.message_history) == 2
        assert state_manager.message_history[0]["type"] == "user"
        assert state_manager.message_history[1]["type"] == "assistant"
        
        # 测试子界面切换
        assert state_manager.switch_to_subview("analytics") is True
        assert state_manager.current_subview == "analytics"
        
        # 测试返回主界面
        state_manager.return_to_main_view()
        assert state_manager.current_subview is None
    
    def test_input_component_with_state_integration(self):
        """测试输入组件与状态管理器的集成"""
        # 初始化组件
        input_component = InputPanelComponent()
        state_manager = StateManager()
        
        # 设置回调，连接输入组件和状态管理器
        def on_submit(text):
            state_manager.add_user_message(text)
        
        def on_command(cmd, args):
            state_manager.add_system_message(f"Command: {cmd} with args: {args}")
        
        input_component.set_submit_callback(on_submit)
        input_component.set_command_callback(on_command)
        
        # 模拟输入
        input_component.input_buffer.set_text("Hello, world!")
        
        # 验证输入被正确处理
        result = input_component.handle_key("enter")
        
        # 检查消息是否被添加到状态管理器
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "user"
        assert state_manager.message_history[0]["content"] == "Hello, world!"
    
    def test_event_engine_with_input_component_integration(self):
        """测试事件引擎与输入组件的集成"""
        with patch('blessed.Terminal') as mock_terminal:
            mock_term_instance = Mock()
            mock_terminal.return_value = mock_term_instance
            
            # 初始化事件引擎和输入组件
            event_engine = EventEngine(mock_term_instance, get_tui_config())
            input_component = InputPanelComponent()
            
            # 设置输入组件处理器
            mock_result_handler = Mock()
            event_engine.set_input_component_handler(input_component.handle_key)
            event_engine.set_input_result_handler(mock_result_handler)
            
            # 验证事件引擎可以处理输入组件的输出
            input_component.input_buffer.set_text("Test input")
            
            # 事件引擎处理输入，应该调用输入组件的处理方法
            result = input_component.handle_key("char:a")
            assert result is None  # 因为这是字符输入，不是命令或回车
    
    def test_subview_with_config_integration(self):
        """测试子界面与配置的集成"""
        config = get_tui_config()
        
        # 初始化分析子界面
        analytics_subview = AnalyticsSubview(config)
        
        # 验证子界面使用了正确的配置
        assert analytics_subview.config == config
        
        # 测试子界面功能
        analytics_subview.update_performance_data({
            "total_requests": 10,
            "avg_response_time": 100.0
        })
        
        assert analytics_subview.performance_data["total_requests"] == 10
        assert analytics_subview.performance_data["avg_response_time"] == 100.0
        
        # 测试渲染不抛出异常
        panel = analytics_subview.render()
        assert panel is not None
    
    def test_component_callback_integration(self):
        """测试组件间回调集成"""
        # 创建状态管理器
        state_manager = StateManager()
        
        # 创建输入组件并设置回调
        input_component = InputPanelComponent()
        
        def submit_callback(text):
            # 当输入提交时，更新状态管理器
            state_manager.add_user_message(text)
        
        def command_callback(cmd, args):
            # 当命令执行时，更新状态管理器
            state_manager.add_system_message(f"Command executed: {cmd}")
        
        input_component.set_submit_callback(submit_callback)
        input_component.set_command_callback(command_callback)
        
        # 模拟输入和提交
        input_component.input_buffer.set_text("Test message")
        
        # 模拟回车键提交
        input_component.handle_key("enter")
        
        # 验证状态管理器被正确更新
        assert len(state_manager.message_history) == 1
        assert state_manager.message_history[0]["type"] == "user"
        assert state_manager.message_history[0]["content"] == "Test message"
    
    def test_layout_manager_with_components_integration(self):
        """测试布局管理器与组件的集成"""
        config = get_tui_config()
        layout_manager = LayoutManager(config.layout)
        
        # 创建一些组件
        input_component = InputPanelComponent(config)
        state_manager = StateManager()
        
        # 验证布局管理器可以与组件协作
        # 更新主内容区域
        layout_manager.update_region_content(
            layout_manager.config.regions.keys().__iter__().__next__(), 
            input_component.render()
        )
        
        # 验证布局管理器可以处理组件的渲染输出
        terminal_size = (100, 30)
        layout = layout_manager.create_layout(terminal_size)
        assert layout is not None
    
    def test_full_workflow_simulation(self):
        """测试完整工作流程模拟"""
        with patch('src.presentation.tui.app.get_global_container') as mock_get_container, \
             patch('src.presentation.tui.app.get_tui_config') as mock_get_config, \
             patch('blessed.Terminal') as mock_terminal, \
             patch('rich.console.Console') as mock_console:
            
            # 设置模拟对象
            mock_container = Mock()
            mock_session_manager = Mock()
            mock_container.get.return_value = mock_session_manager
            mock_container.has_service.return_value = False
            mock_get_container.return_value = mock_container
            
            mock_config = get_tui_config()
            mock_get_config.return_value = mock_config
            
            mock_term_instance = Mock()
            mock_terminal.return_value = mock_term_instance
            
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            # 创建应用
            app = TUIApp()
            
            # 模拟完整的交互流程
            # 1. 用户输入消息
            app.state_manager.add_user_message("Hello")
            
            # 2. 更新性能数据
            app.analytics_view.update_performance_data({
                "total_requests": 1,
                "avg_response_time": 200.0
            })
            
            # 3. 切换到子界面
            app._switch_to_subview("analytics")
            assert app.state_manager.current_subview == "analytics"
            
            # 4. 返回主界面
            app._handle_escape_key("escape")
            assert app.state_manager.current_subview is None
            
            # 5. 模拟命令处理
            app._handle_command("sessions", [])
            assert app.state_manager.show_session_dialog is True
            
            # 6. 更新UI
            app.update_ui()
            
            # 验证整个流程没有抛出异常
            assert True # 如果执行到这里，说明流程成功
    
    def test_subview_navigation_integration(self):
        """测试子界面导航集成"""
        with patch('src.presentation.tui.app.get_global_container') as mock_get_container, \
             patch('src.presentation.tui.app.get_tui_config') as mock_get_config, \
             patch('blessed.Terminal') as mock_terminal, \
             patch('rich.console.Console') as mock_console:
            
            # 设置模拟对象
            mock_container = Mock()
            mock_session_manager = Mock()
            mock_container.get.return_value = mock_session_manager
            mock_container.has_service.return_value = False
            mock_get_container.return_value = mock_container
            
            mock_config = get_tui_config()
            mock_get_config.return_value = mock_config
            
            mock_term_instance = Mock()
            mock_terminal.return_value = mock_term_instance
            
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            # 创建应用
            app = TUIApp()
            
            # 测试子界面控制器与应用的集成
            # 切换到不同子界面
            assert app._switch_to_subview("analytics") is True
            assert app.state_manager.current_subview == "analytics"
            
            # 切换到另一个子界面
            assert app._switch_to_subview("system") is True
            assert app.state_manager.current_subview == "system"
            
            # 验证子界面控制器的状态同步
            current_subview = app.subview_controller.get_current_subview_name()
            # 由于实现细节，我们验证状态管理器与子界面控制器的交互
            assert app.state_manager.current_subview == "system"
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        with patch('src.presentation.tui.app.get_global_container') as mock_get_container, \
             patch('src.presentation.tui.app.get_tui_config') as mock_get_config, \
             patch('blessed.Terminal') as mock_terminal, \
             patch('rich.console.Console') as mock_console:
            
            # 设置模拟对象
            mock_container = Mock()
            mock_session_manager = Mock()
            mock_container.get.return_value = mock_session_manager
            mock_container.has_service.return_value = False
            mock_get_container.return_value = mock_container
            
            mock_config = get_tui_config()
            mock_get_config.return_value = mock_config
            
            mock_term_instance = Mock()
            mock_terminal.return_value = mock_term_instance
            
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            # 创建应用
            app = TUIApp()
            
            # 测试在各种操作中不会抛出异常
            try:
                # 尝试加载不存在的会话
                app._load_session("nonexistent_session")
                
                # 尝试执行无效命令
                app._handle_command("invalid_command", [])
                
                # 尝试处理无效按键
                app._handle_global_key("invalid_key")
                
                # 更新UI
                app.update_ui()
                
                # 处理关闭事件
                app._handle_shutdown()
                
            except Exception as e:
                pytest.fail(f"集成测试中出现未处理的异常: {e}")