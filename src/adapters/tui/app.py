"""TUI应用程序主文件"""

from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from blessed import Terminal
from rich.console import Console
from rich.live import Live

from .layout import LayoutManager
from .config import get_tui_config, TUIConfig
from .components import (
    SidebarComponent,
    UnifiedMainContentComponent,
    InputPanel,
    SessionManagerDialog,
    AgentSelectDialog,
    WorkflowControlPanel,
    ErrorFeedbackPanel,
    ConfigReloadPanel,
    NavigationBarComponent
)
from .subviews import (
    AnalyticsSubview,
    VisualizationSubview,
    SystemSubview,
    ErrorFeedbackSubview,
    StatusOverviewSubview
)
from .event_engine import EventEngine
from .key import Key, KEY_ESCAPE, KEY_ALT_1, KEY_ALT_2, KEY_ALT_3, KEY_ALT_4, KEY_ALT_5, KEY_ALT_6
from .state_manager import StateManager
from .render_controller import RenderController
from .command_processor import CommandProcessor
from .callback_manager import TUICallbackManager
from .subview_controller import SubviewController
from .session_handler import SessionHandler

# 新架构导入
from src.services.container import get_global_container
from src.interfaces.config import IConfigLoader
from src.core.config.models.global_config import GlobalConfig
from src.interfaces.sessions.service import ISessionService
from src.core.state import WorkflowState
from src.interfaces.history import IHistoryManager
from src.services.history.manager import HistoryManager
from src.interfaces.workflow.services import IWorkflowManager, IWorkflowExecutor

# 导入TUI日志系统
from .logger import get_tui_silent_logger, TUILoggerManager


class TUIApp:
    """TUI应用程序，作为顶层协调器"""
    
    def __init__(self, config_path: Optional[Path] = None) -> None:
        """初始化TUI应用程序
         
         Args:
             config_path: 配置文件路径
         """
        # 初始化TUI调试日志记录器
        self.tui_logger = get_tui_silent_logger("app")
        self.tui_manager = TUILoggerManager()
        
        # 如果环境变量设置了TUI_DEBUG，启用调试模式
        import os
        if os.getenv("TUI_DEBUG", "0").lower() in ("1", "true", "yes"):
            self.tui_logger.set_debug_mode(True)
            self.tui_manager.set_debug_mode(True)
        
        self.console = Console()
        self.terminal = Terminal()
        self.running = False
        self.live: Optional[Live] = None
        
        # 加载配置
        self.config = get_tui_config(config_path)
        
        # 初始化布局管理器
        self.layout_manager = LayoutManager(self.config.layout)
        
        # 初始化依赖
        self.session_service: Optional[ISessionService] = None
        self.workflow_executor: Optional[IWorkflowExecutor] = None
        self._initialize_dependencies()
        
        # 初始化全局配置并设置日志系统
        self._initialize_global_config()
        
        # 初始化各个管理器
        self.state_manager = StateManager(self.session_service)
        self.callback_manager = TUICallbackManager()
        self.session_handler = SessionHandler(self.session_service)
        self.command_processor = CommandProcessor(self)
        
        # 集成历史存储
        container = get_global_container()
        if container.has_service(IHistoryManager):
            history_manager = container.get(IHistoryManager)  # type: ignore
            self.history_manager = history_manager  # type: ignore
            
            # 注册钩子
            if hasattr(self.state_manager, 'add_user_message_hook'):
                self.state_manager.add_user_message_hook(
                    self._on_user_message
                )
            if hasattr(self.state_manager, 'add_assistant_message_hook'):
                self.state_manager.add_assistant_message_hook(
                    self._on_assistant_message
                )
            if hasattr(self.state_manager, 'add_tool_call_hook'):
                self.state_manager.add_tool_call_hook(
                    lambda tool_name, args, context=None: self._on_tool_call(tool_name, args)
                )
        
        # 初始化组件
        self._initialize_components()
        
        # 初始化子界面
        self._initialize_subviews()
        
        # 初始化控制器
        self._initialize_controllers()
        
        # 设置回调
        self._setup_callbacks()
        
        # 添加最小刷新间隔以避免过度刷新
        import time
        self._last_update_time = 0
        # 移除固定的时间间隔检查，改为基于内容变化的更新
        
        # 初始化终端尺寸跟踪
        self.previous_terminal_size: Optional[Tuple[int, int]] = None
        self._resize_threshold = 5  # 终端尺寸变化阈值，避免频繁调整
        
        # 用于跟踪是否需要更新UI
        self._needs_ui_update = True
    
    def _initialize_dependencies(self) -> None:
        """初始化依赖注入"""
        try:
            container = get_global_container()
            
            # 初始化必要的服务
            self._setup_container_services(container)
            
            # 获取会话服务（通过工作流执行器与graph交互）
            if container.has_service(ISessionService):
                self.session_service = container.get(ISessionService)  # type: ignore
            
            # 获取工作流执行器
            if container.has_service(IWorkflowExecutor):
                self.workflow_executor = container.get(IWorkflowExecutor)  # type: ignore
                
        except Exception as e:
            self.console.print(f"[red]初始化依赖失败: {e}[/red]")
    
    def _setup_container_services(self, container: Any) -> None:
        """设置容器中的必要服务"""
        from src.core.config.config_manager import ConfigManager as CoreConfigManager
        
        # 注册配置加载器（如果还未注册）
        if not container.has_service(IConfigLoader):
            try:
                config_manager = CoreConfigManager()
                container.register_instance(IConfigLoader, config_manager)
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法初始化配置加载器: {e}[/yellow]")
        
        # 注册历史管理器（如果还未注册）
        if not container.has_service(IHistoryManager):
            try:
                # HistoryManager需要存储实现
                history_manager = HistoryManager(storage=None)  # type: ignore
                container.register_instance(IHistoryManager, history_manager)
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法初始化历史管理器: {e}[/yellow]")
        
        # 注册会话服务（如果还未注册）
        if not container.has_service(ISessionService):
            try:
                # 会话服务应该在bootstrap中注册
                # 这里只做备选处理
                self.console.print(f"[yellow]会话服务未在容器中注册，请在启动时配置[/yellow]")
            except Exception as e:
                self.console.print(f"[yellow]警告: 无法初始化会话服务: {e}[/yellow]")
    
    def _initialize_global_config(self) -> None:
        """初始化全局配置并设置日志系统"""
        try:
            container = get_global_container()
            
            # 尝试从容器获取配置加载器
            if container.has_service(IConfigLoader):
                config_loader = container.get(IConfigLoader)  # type: ignore
                
                # 加载全局配置
                try:
                    global_config_data = config_loader.load("global.yaml")
                    
                    # 创建全局配置对象
                    if isinstance(global_config_data, dict):
                        global_config = GlobalConfig(**global_config_data)
                    else:
                        global_config = global_config_data
                    
                    # 初始化TUI日志管理器
                    self.tui_manager.initialize(global_config)
                    
                    # 记录调试信息
                    self.tui_logger.info("全局配置已初始化", config_path="global.yaml")
                except Exception as e:
                    self.console.print(f"[yellow]警告: 加载全局配置失败: {e}[/yellow]")
                    self.tui_logger.warning(f"加载全局配置失败: {e}")
            else:
                self.console.print(f"[yellow]警告: 配置加载器未在容器中注册[/yellow]")
            
        except Exception as e:
            self.console.print(f"[red]初始化全局配置失败: {e}[/red]")
            # 即使初始化失败也继续运行，使用默认配置
            self.tui_logger.error(f"初始化全局配置失败: {e}")
    
    def _initialize_components(self) -> None:
        """初始化组件"""
        self.sidebar_component = SidebarComponent(self.config)
        self.main_content_component = UnifiedMainContentComponent(self.config)
        self.input_component = InputPanel(self.config)
        
        # 初始化工作流控制面板
        self.workflow_control_panel = WorkflowControlPanel(self.config)
        
        # 初始化错误反馈面板
        self.error_feedback_panel = ErrorFeedbackPanel(self.config)
        
        # 初始化配置重载面板
        self.config_reload_panel = ConfigReloadPanel(self.config)
        
        # 初始化对话框
        self.session_dialog = SessionManagerDialog(self.config)
        self.agent_dialog = AgentSelectDialog(self.config)
        
        # 初始化导航栏组件
        self.navigation_component = NavigationBarComponent(self.config)
        
        # 设置会话对话框的会话服务
        if self.session_service:
            self.session_dialog.set_session_manager(self.session_service)
        
        # 加载Agent配置
        self.agent_dialog.load_agent_configs()
        
        # 组件字典
        self.components = {
            "sidebar": self.sidebar_component,
            "main_content": self.main_content_component,
            "input": self.input_component,
            "workflow_control": self.workflow_control_panel,
            "error_feedback": self.error_feedback_panel,
            "config_reload": self.config_reload_panel,
            "session_dialog": self.session_dialog,
            "agent_dialog": self.agent_dialog,
            "navigation": self.navigation_component
        }
    
    def _initialize_subviews(self) -> None:
        """初始化子界面"""
        self.analytics_view = AnalyticsSubview(self.config)
        self.visualization_view = VisualizationSubview(self.config)
        self.system_view = SystemSubview(self.config)
        self.errors_view = ErrorFeedbackSubview(self.config)
        self.status_overview_view = StatusOverviewSubview(self.config)
        
        # 子界面字典
        self.subviews = {
            "analytics": self.analytics_view,
            "visualization": self.visualization_view,
            "system": self.system_view,
            "errors": self.errors_view
        }
    
    def _initialize_controllers(self) -> None:
        """初始化控制器"""
        # 初始化事件引擎
        self.event_engine = EventEngine(self.terminal, self.config)
        
        # 初始化子界面控制器
        self.subview_controller = SubviewController(self.subviews)
        
        # 初始化渲染控制器
        self.render_controller = RenderController(
            self.layout_manager,
            self.components,
            self.subviews,
            self.config
        )
    
    def _setup_callbacks(self) -> None:
        """设置回调函数"""
        # 设置组件回调
        self.input_component.set_submit_callback(self._handle_input_submit)
        self.input_component.set_command_callback(self._handle_command)
        
        # 设置对话框回调
        self.session_dialog.set_session_selected_callback(self._on_session_selected)
        self.session_dialog.set_session_created_callback(self._on_session_created)
        self.session_dialog.set_session_deleted_callback(self._on_session_deleted)
        self.agent_dialog.set_agent_selected_callback(self._on_agent_selected)
        
        # 设置工作流控制回调
        self.workflow_control_panel.set_control_action_callback(self._on_workflow_action)
        
        # 设置错误反馈回调
        self.error_feedback_panel.set_user_action_callback(self._on_error_action)
        
        # 设置配置重载回调
        self.config_reload_panel.set_config_updated_callback(self._on_config_updated)
        
        # 设置子界面回调
        self.subview_controller.setup_subview_callbacks(self.callback_manager)
        
        # 设置事件引擎回调
        self.event_engine.set_input_component_handler(self.input_component.handle_key)
        self.event_engine.set_input_result_handler(self._handle_input_result)
        self.event_engine.set_global_key_handler(self._handle_global_key)
        
        # 注册全局快捷键
        self._register_global_shortcuts()
        
        # 注册回调管理器回调
        self._register_callback_manager_callbacks()
    
    def _register_global_shortcuts(self) -> None:
        """注册全局快捷键"""
        # 使用新的Key对象注册快捷键
        self.event_engine.register_key_handler(KEY_ESCAPE, lambda k: self._handle_escape_key(k))
        self.event_engine.register_key_handler(KEY_ALT_1, lambda _: (self._switch_to_subview("analytics"), True)[1])
        self.event_engine.register_key_handler(KEY_ALT_2, lambda _: (self._switch_to_subview("visualization"), True)[1])
        self.event_engine.register_key_handler(KEY_ALT_3, lambda _: (self._switch_to_subview("system"), True)[1])
        self.event_engine.register_key_handler(KEY_ALT_4, lambda _: (self._switch_to_subview("errors"), True)[1])
        self.event_engine.register_key_handler(KEY_ALT_5, lambda _: (self._switch_to_subview("status_overview"), True)[1])

        # 统一时间线快捷键
        from .key import KEY_PAGE_UP, KEY_PAGE_DOWN, KEY_HOME, KEY_END, KeyType
        self.event_engine.register_key_handler(KEY_PAGE_UP, self._handle_timeline_scroll)
        self.event_engine.register_key_handler(KEY_PAGE_DOWN, self._handle_timeline_scroll)
        self.event_engine.register_key_handler(KEY_HOME, self._handle_timeline_scroll)
        self.event_engine.register_key_handler(KEY_END, self._handle_timeline_scroll)
        # Key构造器 - 创建一个字符按键对象
        try:
            from .key import Key as KeyClass, KeyType as KeyTypeEnum
            key_a = KeyClass(name="a", key_type=KeyTypeEnum.CHARACTER)
            self.event_engine.register_key_handler(key_a, self._handle_timeline_scroll)
        except Exception:
            # 如果创建失败，跳过这个快捷键
            pass
    
    def _register_callback_manager_callbacks(self) -> None:
        """注册回调管理器回调"""
        # 会话相关回调
        self.callback_manager.register_session_selected_callback(self._on_session_selected)
        self.callback_manager.register_session_created_callback(self._on_session_created)
        self.callback_manager.register_session_deleted_callback(self._on_session_deleted)
        self.callback_manager.register_agent_selected_callback(self._on_agent_selected)
        
        # 子界面相关回调
        self.callback_manager.register_analytics_data_refreshed_callback(self._on_analytics_data_refreshed)
        self.callback_manager.register_visualization_node_selected_callback(self._on_visualization_node_selected)
        self.callback_manager.register_studio_started_callback(self._on_studio_started)
        self.callback_manager.register_studio_stopped_callback(self._on_studio_stopped)
        self.callback_manager.register_config_reloaded_callback(self._on_config_reloaded)
        self.callback_manager.register_error_feedback_submitted_callback(self._on_error_feedback_submitted)
        
        # 输入和命令回调
        self.callback_manager.register_input_submit_callback(self._handle_input_submit)
        self.callback_manager.register_command_callback(self._handle_command)
    
    def run(self) -> None:
        """运行TUI应用程序"""
        self.tui_logger.debug_component_event("TUIApp", "run_start")
        try:
            self.running = True
            
            # 设置终端模式
            with self.terminal.cbreak(), self.terminal.hidden_cursor():
                # 获取终端尺寸
                terminal_size = self.console.size
                
                # 创建布局
                layout = self.layout_manager.create_layout((terminal_size.width, terminal_size.height))
                
                # 启动Live显示 - 设置为极低的刷新率，主要依赖手动刷新
                with Live(layout, console=self.console, refresh_per_second=0.1, screen=True) as live:  # 降低到0.1 FPS
                    self.live = live
                    self.render_controller.set_live(live)
                    
                    # 显示欢迎信息
                    self.render_controller.show_welcome_message()
                    # 初始化previous_terminal_size
                    self.previous_terminal_size = (terminal_size.width, terminal_size.height)
                    
                    # 启动事件循环
                    self._run_main_loop()
                
        except KeyboardInterrupt:
            self.tui_logger.debug_component_event("TUIApp", "keyboard_interrupt")
            self._handle_shutdown()
        except Exception as e:
            self.tui_logger.debug_error_handling("run_exception", str(e))
            self._handle_critical_error(e)
            raise
        finally:
            self.tui_logger.debug_component_event("TUIApp", "run_end")
            self.running = False
            self.live = None
    
    def _handle_global_key(self, key: Key) -> bool:
        """处理全局按键
        
        Args:
            key: Key对象
            
        Returns:
            bool: 是否处理了该按键
        """
        self.tui_logger.debug_key_event(key.to_string(), True, "global_handler")
        
        # ESC键特殊处理：无论在子界面还是对话框中，都由主应用处理
        if key.name == "escape":
            return self._handle_escape_key(key)
        
        # 如果在子界面中，优先让子界面处理按键（非ESC键）
        if self.state_manager.current_subview:
            self.tui_logger.debug_key_event(key.to_string(), True, f"subview_{self.state_manager.current_subview}")
            return self.subview_controller.handle_key(key.to_string())
        
        # 处理对话框中的按键
        if self.state_manager.show_session_dialog:
            self.tui_logger.debug_key_event(key.to_string(), True, "session_dialog")
            result = self.session_dialog.handle_key(key.to_string())
            return result is not None
        elif self.state_manager.show_agent_dialog:
            self.tui_logger.debug_key_event(key.to_string(), True, "agent_dialog")
            result = self.agent_dialog.handle_key(key.to_string())
            return result is not None
        
        self.tui_logger.debug_key_event(key.to_string(), False, "global_handler")
        return False
    
    def _handle_escape_key(self, key: Key) -> bool:
        """处理ESC键
        
        Args:
            key: Key对象
            
        Returns:
            bool: 是否处理了该按键
        """
        # 如果有对话框打开，关闭对话框
        if self.state_manager.show_session_dialog:
            self.state_manager.set_show_session_dialog(False)
            return True
        elif self.state_manager.show_agent_dialog:
            self.state_manager.set_show_agent_dialog(False)
            return True
        
        # 如果在子界面，返回主视图
        if self.state_manager.current_subview:
            self.subview_controller.return_to_main_view()
            return True
        
        return False
    
    def _switch_to_subview(self, subview_name: str) -> None:
        """切换到子界面"""
        self.subview_controller.switch_to_subview(subview_name)
    
    def _handle_timeline_scroll(self, key: Key) -> bool:
        """处理时间线滚动"""
        # 获取当前子界面并处理滚动
        current_subview = self.subview_controller.get_current_subview()
        if current_subview and hasattr(current_subview, 'handle_key'):
            return current_subview.handle_key(key.to_string())
        return False
    
    def _handle_input_result(self, result: str) -> None:
        """处理输入结果"""
        if result == "CLEAR_SCREEN":
            self.state_manager.clear_message_history()
            self.main_content_component.clear_all()
            self.state_manager.add_system_message("屏幕已清空")
        elif result == "EXIT":
            self.running = False
        elif result == "REFRESH_UI":
            # 处理UI刷新请求 - 强制更新UI
            self.tui_logger.debug_render_operation("input_result", "refresh_ui_requested")
            # 同步更新状态管理器中的input_buffer
            if self.input_component:
                self.state_manager.set_input_buffer(self.input_component.input_buffer.get_text())
            # 设置强制刷新标记
            self.state_manager._force_refresh = True
        elif result and result.startswith("LOAD_SESSION:"):
            session_id = result.split(":", 1)[1]
            self._load_session(session_id)
        elif result in ["SAVE_SESSION", "NEW_SESSION", "PAUSE_WORKFLOW",
                      "RESUME_WORKFLOW", "STOP_WORKFLOW", "OPEN_STUDIO",
                      "OPEN_SESSIONS", "OPEN_AGENTS"]:
            # 处理命令
            command = result.lower()
            self.command_processor.process_command(command, [])
        elif result and not result.startswith("USER_INPUT:"):
            # 显示命令结果
            self.state_manager.add_system_message(result)
            self.main_content_component.add_assistant_message(result)
        elif result and result.startswith("USER_INPUT:"):
            # 处理用户输入
            input_text = result[len("USER_INPUT:"):]  # 移除前缀，获取实际输入文本
            self.tui_logger.debug_input_handling("user_input_received", f"Received user input: {input_text}")
            # 用户输入已经通过回调处理，这里可以添加额外的处理逻辑
    
    def _handle_input_submit(self, input_text: str) -> None:
        """处理输入提交
        
        Args:
            input_text: 输入文本
        """
        self.tui_logger.debug_input_handling("user_input", input_text)
        
        # 添加用户消息到历史
        self.state_manager.add_user_message(input_text)
        
        # 添加到主内容组件
        self.main_content_component.add_user_message(input_text)
        
        # 处理用户输入 - 通过工作流执行器发送到graph
        self._process_user_input(input_text)
    
    def _handle_command(self, command: str, args: List[str]) -> None:
        """处理命令
        
        Args:
            command: 命令名称
            args: 命令参数
        """
        self.tui_logger.debug_input_handling("command", command, args=args)
        
        # 特殊处理一些需要直接操作状态的命令
        if command == "sessions":
            self.state_manager.set_show_session_dialog(True)
            self.session_dialog.refresh_sessions()
            self.state_manager.add_system_message("已打开会话管理对话框")
            self.tui_logger.debug_component_event("command", "open_sessions_dialog")
        elif command == "agents":
            self.state_manager.set_show_agent_dialog(True)
            self.state_manager.add_system_message("已打开Agent选择对话框")
            self.tui_logger.debug_component_event("command", "open_agents_dialog")
        elif command in ["analytics", "visualization", "system", "errors"]:
            self._switch_to_subview(command)
            self.tui_logger.debug_component_event("command", "switch_subview", subview=command)
        elif command == "main":
            self.subview_controller.return_to_main_view()
            self.tui_logger.debug_component_event("command", "return_to_main_view")
        elif command in ["pause", "resume", "stop", "start"]:
            self._handle_workflow_command(command)
            self.tui_logger.debug_workflow_operation(f"workflow_{command}")
        else:
            # 其他命令交给命令处理器处理
            self.command_processor.process_command(command, args)
            self.tui_logger.debug_component_event("command", "process_other_command", command=command)
    
    def _process_user_input(self, input_text: str) -> None:
        """处理用户输入 - 通过工作流执行器
        
        Args:
            input_text: 用户输入
        """
        self.tui_logger.debug_input_handling("process_user_input", input_text)
        
        # 如果有工作流执行器，通过它处理输入
        if self.workflow_executor:
            try:
                # 通过工作流执行器将输入发送到graph
                # 这是TUI与graph交互的主要方式
                # 具体实现应该调用workflow_executor的相应方法
                pass
            except Exception as e:
                self.tui_logger.debug_error_handling("workflow_execution_error", str(e))
                self.state_manager.add_system_message(f"工作流执行错误: {e}")
        else:
            # 备选方案：直接添加响应
            response = f"收到您的输入: {input_text}"
            self.state_manager.add_assistant_message(response)
            self.main_content_component.add_assistant_message(response)
            self.tui_logger.debug_component_event("main_content", "add_assistant_message", response=response)
    
    def _load_session(self, session_id: str) -> None:
        """加载会话
        
        Args:
            session_id: 会话ID
        """
        self.tui_logger.debug_session_operation("load_session_start", session_id)
        
        if self.session_handler:
            result = self.session_handler.load_session(session_id)
            if result:
                workflow, state = result
                self.state_manager.session_id = session_id
                self.state_manager.current_workflow = workflow
                self.state_manager.current_state = state
                self.state_manager.message_history = []
                self.tui_logger.debug_session_operation("load_session_success", session_id)
                self.state_manager.add_system_message(f"会话 {session_id[:8]}... 已加载")
            else:
                self.tui_logger.debug_session_operation("load_session_failed", session_id)
                self.state_manager.add_system_message("加载会话失败")
        else:
            self.tui_logger.debug_session_operation("session_handler_not_initialized", session_id)
            self.state_manager.add_system_message("会话处理器未初始化")
    
    def _handle_shutdown(self) -> None:
        """处理关闭事件"""
        self.tui_logger.debug_component_event("TUIApp", "shutdown_start")
        
        # 保存会话
        if self.state_manager.session_id and self.state_manager.current_state and self.session_handler:
            self.tui_logger.debug_session_operation("save_on_shutdown", self.state_manager.session_id)
            success = self.session_handler.save_session(
                self.state_manager.session_id,
                self.state_manager.current_workflow,
                self.state_manager.current_state
            )
            if success:
                self.tui_logger.debug_session_operation("save_success", self.state_manager.session_id)
                self.console.print("[green]会话已保存[/green]")
            else:
                self.tui_logger.debug_session_operation("save_failed", self.state_manager.session_id)
                self.console.print("[red]保存会话失败[/red]")
        
        self.console.print("[yellow]正在关闭TUI界面...[/yellow]")
        self.tui_logger.debug_component_event("TUIApp", "shutdown_complete")
        self.running = False
    
    # 回调方法
    def _on_session_selected(self, session_id: str) -> None:
        """会话选择回调"""
        self.tui_logger.debug_session_operation("session_selected", session_id)
        
        try:
            # 保存当前会话（如果有）
            if self.state_manager.session_id and self.state_manager.current_state:
                self.tui_logger.debug_session_operation("save_before_switch", self.state_manager.session_id)
                self.session_handler.save_session(
                    self.state_manager.session_id,
                    self.state_manager.current_workflow,
                    self.state_manager.current_state
                )
            
            # 加载新会话
            self._load_session(session_id)
            self.state_manager.set_show_session_dialog(False)
            self.state_manager.add_system_message(f"已切换到会话 {session_id[:8]}...")
            self.add_success_notification(f"已切换到会话 {session_id[:8]}...")
            
            # 更新侧边栏显示会话信息
            if self.sidebar_component and self.session_handler:
                session_info = self.session_handler.get_session_info(session_id)
                if session_info:
                    self.sidebar_component.update_session_info(
                        session_id=session_id,
                        workflow_config=session_info.get("workflow_config_path", ""),
                        status="已加载"
                    )
                    self.tui_logger.debug_component_event("sidebar", "update_session_info", session_id=session_id)
        except Exception as e:
            self.tui_logger.debug_error_handling("session_selected", str(e))
            self._handle_session_error(e, "切换")
    
    def _on_session_created(self, workflow_config: str, agent_config: Optional[str]) -> None:
        """会话创建回调"""
        self.tui_logger.debug_session_operation("session_created", f"workflow_config: {workflow_config}")
        
        try:
            # 创建会话
            session_id = self.session_handler.create_session(workflow_config, {} if agent_config else None)
            if session_id:
                self.tui_logger.debug_session_operation("session_created_success", session_id)
                # 加载会话以获取工作流和状态
                result = self.session_handler.load_session(session_id)
                if result:
                    workflow, state = result
                    self.state_manager.session_id = session_id
                    self.state_manager.current_workflow = workflow
                    self.state_manager.current_state = state
                    self.state_manager.message_history = []
                    self.state_manager.set_show_session_dialog(False)
                    self.state_manager.add_system_message(f"已创建新会话 {session_id[:8]}...")
                    self.add_success_notification(f"会话 {session_id[:8]}... 创建成功")
                    
                    # 更新侧边栏显示会话信息
                    if self.sidebar_component:
                        self.sidebar_component.update_session_info(
                            session_id=session_id,
                            workflow_config=workflow_config,
                            status="运行中"
                        )
                        self.tui_logger.debug_component_event("sidebar", "update_session_info", session_id=session_id, status="running")
                else:
                    error_msg = "加载新会话失败"
                    self.tui_logger.debug_session_operation("session_load_failed", session_id)
                    self.state_manager.add_system_message(error_msg)
                    self.add_error_notification(error_msg, title="会话加载错误")
            else:
                error_msg = "创建会话失败"
                self.tui_logger.debug_session_operation("session_creation_failed", "none")
                self.state_manager.add_system_message(error_msg)
                self.add_error_notification(error_msg, title="会话创建错误")
        except Exception as e:
            self.tui_logger.debug_error_handling("session_created", str(e))
            self._handle_session_error(e, "创建")
    
    def _on_session_deleted(self, session_id: str) -> None:
        """会话删除回调"""
        self.tui_logger.debug_session_operation("session_deleted", session_id)
        
        try:
            success = self.session_handler.delete_session(session_id)
            if success:
                self.tui_logger.debug_session_operation("session_deleted_success", session_id)
                self.state_manager.add_system_message(f"已删除会话 {session_id[:8]}...")
                self.add_success_notification(f"会话 {session_id[:8]}... 已删除")
                
                # 如果删除的是当前会话，重置状态
                if self.state_manager.session_id == session_id:
                    self.tui_logger.debug_session_operation("reset_current_session", session_id)
                    self.state_manager.session_id = None
                    self.state_manager.current_state = None
                    self.state_manager.current_workflow = None
                    self.state_manager.message_history = []
                    if self.main_content_component:
                        self.main_content_component.clear_all()
                    
                    # 更新侧边栏清除会话信息
                    if self.sidebar_component:
                        self.sidebar_component.clear_session_info()
                        self.tui_logger.debug_component_event("sidebar", "clear_session_info")
            else:
                error_msg = "删除会话失败"
                self.tui_logger.debug_session_operation("session_deleted_failed", session_id)
                self.state_manager.add_system_message(error_msg)
                self.add_error_notification(error_msg, title="会话删除错误")
        except Exception as e:
            self.tui_logger.debug_error_handling("session_deleted", str(e))
            self._handle_session_error(e, "删除")
    
    def _run_main_loop(self) -> None:
        """运行主循环"""
        self.tui_logger.debug_component_event("TUIApp", "main_loop_start")
        import time
        
        # 启动事件循环线程
        import threading
        event_thread = threading.Thread(target=self.event_engine.start, daemon=True)
        event_thread.start()
        self.tui_logger.debug_component_event("event_engine", "event_loop_started")
        
        # 主循环负责更新UI
        while self.running:
            try:
                # 获取当前终端尺寸以检测是否发生变化
                current_terminal_size = self.console.size
                
                # 如果终端尺寸发生变化，通知布局管理器
                if self.previous_terminal_size is not None:
                    if (abs(current_terminal_size.width - self.previous_terminal_size[0]) > self._resize_threshold or
                        abs(current_terminal_size.height - self.previous_terminal_size[1]) > self._resize_threshold):
                        # 终端尺寸变化较大，更新布局
                        self.layout_manager.resize_layout((current_terminal_size.width, current_terminal_size.height))
                        # 更新UI以反映布局变化
                        self.update_ui()
                        if self.live:  # 确保live对象存在
                            self.live.refresh()  # 强制刷新显示
                        time.sleep(0.1)  # 休眠更长时间以避免频繁调整
                
                self.previous_terminal_size = (current_terminal_size.width, current_terminal_size.height)
                
                # 更新UI，并获取是否需要刷新的标志
                needs_refresh = self.update_ui()
                if needs_refresh:
                    # 只有当内容真正变化时才刷新UI
                    if self.live:  # 确保live对象存在
                        self.live.refresh()
                        self.tui_logger.debug_render_operation("main_loop", "ui_refreshed")
                    # 如果需要刷新，使用较短的休眠时间以保持响应性
                    time.sleep(0.01)
                else:
                    # 如果不需要刷新，使用较长的休眠时间以减少CPU使用
                    time.sleep(0.05)
                
            except KeyboardInterrupt:
                self.tui_logger.debug_component_event("TUIApp", "main_loop_keyboard_interrupt")
                break
            except Exception as e:
                self.tui_logger.debug_error_handling("main_loop", str(e))
                self.console.print(f"[red]主循环错误: {e}[/red]")
                break
        
        # 停止事件引擎
        self.event_engine.stop()
        self.tui_logger.debug_component_event("TUIApp", "main_loop_end")
    
    def enable_tui_debug(self, enabled: bool = True) -> None:
        """启用或禁用TUI调试模式
        
        Args:
            enabled: 是否启用调试模式
        """
        self.tui_logger.set_debug_mode(enabled)
        self.tui_manager.set_debug_mode(enabled)
        if enabled:
            self.state_manager.add_system_message("TUI调试模式已启用")
        else:
            self.state_manager.add_system_message("TUI调试模式已禁用")
    
    def _on_agent_selected(self, agent_config: Any) -> None:
        """Agent选择回调"""
        try:
            # 更新侧边栏的Agent信息
            self.sidebar_component.update_agent_info(
                name=agent_config.name,
                model=agent_config.model,
                status="就绪"
            )
            
            self.state_manager.set_show_agent_dialog(False)
            self.state_manager.add_system_message(f"已选择Agent: {agent_config.name}")
        except Exception as e:
            self.state_manager.add_system_message(f"选择Agent失败: {e}")
    
    def _on_analytics_data_refreshed(self, data: Dict[str, Any]) -> None:
        """分析监控数据刷新回调"""
        # 这里可以添加数据刷新后的处理逻辑
        pass
    
    def _on_visualization_node_selected(self, node_id: str) -> None:
        """可视化节点选择回调"""
        # 这里可以添加节点选择后的处理逻辑
        pass
    
    def _on_studio_started(self, studio_status: Dict[str, Any]) -> None:
        """Studio启动回调"""
        self.state_manager.add_system_message(f"Studio已启动: {studio_status.get('url', 'Unknown')}")
    
    def _on_studio_stopped(self, studio_status: Dict[str, Any]) -> None:
        """Studio停止回调"""
        self.state_manager.add_system_message("Studio已停止")
    
    def _on_config_reloaded(self, config_data: Dict[str, Any]) -> None:
        """配置重载回调"""
        self.state_manager.add_system_message("配置已重载")
    
    def _on_error_feedback_submitted(self, feedback_data: Dict[str, Any]) -> None:
        """错误反馈提交回调"""
        error_id = feedback_data.get("error_id", "Unknown")
        self.state_manager.add_system_message(f"错误反馈已提交: {error_id}")
    
    def _handle_workflow_command(self, command: str) -> None:
        """处理工作流控制命令
        
        Args:
            command: 命令名称
        """
        if command == "pause":
            self.workflow_control_panel.handle_action("pause")
            self.state_manager.add_system_message("工作流已暂停")
        elif command == "resume":
            self.workflow_control_panel.handle_action("resume")
            self.state_manager.add_system_message("工作流已恢复")
        elif command == "stop":
            self.workflow_control_panel.handle_action("stop")
            self.state_manager.add_system_message("工作流已停止")
        elif command == "start":
            self.workflow_control_panel.handle_action("start")
            self.state_manager.add_system_message("工作流已启动")
    
    def _on_workflow_action(self, action: str) -> None:
        """工作流动作回调
        
        Args:
            action: 动作名称
        """
        # 更新状态管理器中的工作流状态
        if action == "pause":
            if self.state_manager.current_state:
                setattr(self.state_manager.current_state, 'workflow_status', 'paused')
        elif action == "resume":
            if self.state_manager.current_state:
                setattr(self.state_manager.current_state, 'workflow_status', 'running')
        elif action == "stop":
            if self.state_manager.current_state:
                setattr(self.state_manager.current_state, 'workflow_status', 'stopped')
        elif action == "start":
            if self.state_manager.current_state:
                setattr(self.state_manager.current_state, 'workflow_status', 'running')
    
    def update_ui(self) -> bool:
        """更新UI显示"""
        # 同步状态管理器中的子界面状态
        current_subview_name = self.subview_controller.get_current_subview_name()
        if self.state_manager.current_subview != current_subview_name:
            old_subview = self.state_manager.current_subview
            self.state_manager.current_subview = current_subview_name
            self.tui_logger.debug_ui_state_change(
                "subview", old_subview, current_subview_name
            )
        
        # 同步对话框状态 - 暂时保持原有状态，因为对话框没有is_visible方法
        # 这里可以根据实际需要添加对话框状态检测逻辑
        
        # 使用渲染控制器更新UI，并检查是否真正需要刷新
        needs_refresh = self.render_controller.update_ui(self.state_manager)
        
        # 只在真正需要刷新时才记录日志，减少日志噪音
        if needs_refresh and self.tui_manager.is_debug_enabled():
            self.tui_logger.debug_render_operation("main", "update_ui_refresh_needed")
        
        return needs_refresh
    
    def _on_error_action(self, notification_id: str, action: str) -> None:
        """错误反馈动作回调
        
        Args:
            notification_id: 通知ID
            action: 动作名称
        """
        if action == "重试":
            self.state_manager.add_system_message(f"重试操作: {notification_id}")
        elif action == "忽略":
            self.state_manager.add_system_message(f"忽略错误: {notification_id}")
        elif action == "详情":
            self.state_manager.add_system_message(f"查看详情: {notification_id}")
    
    def _on_config_updated(self, config_data: Any) -> None:
        """配置更新回调
        
        Args:
            config_data: 新配置数据
        """
        self.state_manager.add_system_message("配置已更新")
    
    def _handle_critical_error(self, error: Exception) -> None:
        """处理关键错误
        
        Args:
            error: 错误对象
        """
        self.console.print(f"[red]关键错误: {error}[/red]")
        if self.error_feedback_panel:
            self.error_feedback_panel.add_error(
                f"关键错误: {error}",
                title="系统错误",
                details=str(error)
            )
    
    def _handle_session_error(self, error: Exception, operation: str) -> None:
        """处理会话错误
        
        Args:
            error: 错误对象
            operation: 操作类型
        """
        error_msg = f"{operation}会话时发生错误: {error}"
        self.state_manager.add_system_message(error_msg)
        self.add_error_notification(error_msg, title=f"会话{operation}错误")
    
    def add_success_notification(self, message: str, title: Optional[str] = None) -> None:
        """添加成功通知
        
        Args:
            message: 消息内容
            title: 标题
        """
        if self.error_feedback_panel:
            self.error_feedback_panel.add_success(message, title=title)
    
    def add_error_notification(self, message: str, title: Optional[str] = None, details: Optional[str] = None) -> None:
        """添加错误通知
        
        Args:
            message: 消息内容
            title: 标题
            details: 详细信息
        """
        if self.error_feedback_panel:
            self.error_feedback_panel.add_error(message, title=title, details=details)
    
    def _on_user_message(self, message: str) -> None:
        """用户消息钩子"""
        # 这里可以添加与历史管理器的集成逻辑
        pass
    
    def _on_assistant_message(self, message: str) -> None:
        """助手消息钩子"""
        # 这里可以添加与历史管理器的集成逻辑
        pass
    
    def _on_tool_call(self, tool_name: str, args: Dict[str, Any]) -> None:
        """工具调用钩子"""
        # 这里可以添加与历史管理器的集成逻辑
        pass
