"""TUI应用程序主文件"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from blessed import Terminal
from rich.console import Console
from rich.live import Live

from .layout import LayoutManager
from .config import get_tui_config, TUIConfig
from .components import (
    SidebarComponent,
    LangGraphPanelComponent,
    MainContentComponent,
    InputPanelComponent,
    SessionManagerDialog,
    AgentSelectDialog
)
from .subviews import (
    AnalyticsSubview,
    VisualizationSubview,
    SystemSubview,
    ErrorFeedbackSubview
)
from .event_engine import EventEngine
from .state_manager import StateManager
from .render_controller import RenderController
from .command_processor import CommandProcessor
from .callback_manager import TUICallbackManager
from .subview_controller import SubviewController
from .session_handler import SessionHandler

from src.infrastructure.container import get_global_container
from src.session.manager import ISessionManager
from src.prompts.agent_state import AgentState, HumanMessage


class TUIApp:
    """TUI应用程序，作为顶层协调器"""
    
    def __init__(self, config_path: Optional[Path] = None) -> None:
        """初始化TUI应用程序
        
        Args:
            config_path: 配置文件路径
        """
        self.console = Console()
        self.terminal = Terminal()
        self.running = False
        self.live: Optional[Live] = None
        
        # 加载配置
        self.config = get_tui_config(config_path)
        
        # 初始化布局管理器
        self.layout_manager = LayoutManager(self.config.layout)
        
        # 初始化依赖
        self.session_manager: Optional[ISessionManager] = None
        self._initialize_dependencies()
        
        # 初始化各个管理器
        self.state_manager = StateManager(self.session_manager)
        self.callback_manager = TUICallbackManager()
        self.session_handler = SessionHandler(self.session_manager)
        self.command_processor = CommandProcessor(self)
        
        # 初始化组件
        self._initialize_components()
        
        # 初始化子界面
        self._initialize_subviews()
        
        # 初始化控制器
        self._initialize_controllers()
        
        # 设置回调
        self._setup_callbacks()
    
    def _initialize_dependencies(self) -> None:
        """初始化依赖注入"""
        try:
            container = get_global_container()
            
            # 初始化必要的服务
            self._setup_container_services(container)
            
            # 获取会话管理器
            self.session_manager = container.get(ISessionManager)  # type: ignore
        except Exception as e:
            self.console.print(f"[red]初始化依赖失败: {e}[/red]")
    
    def _setup_container_services(self, container) -> None:
        """设置容器中的必要服务"""
        from ...infrastructure.config_loader import YamlConfigLoader, IConfigLoader
        from ...session.store import FileSessionStore
        from ...workflow.manager import WorkflowManager
        from ...session.git_manager import GitManager, create_git_manager
        from ...session.manager import SessionManager
        
        # 注册配置加载器
        if not container.has_service(IConfigLoader):
            config_loader = YamlConfigLoader()
            container.register_instance(IConfigLoader, config_loader)
        
        # 注册会话存储
        if not container.has_service(FileSessionStore):
            from pathlib import Path
            session_store = FileSessionStore(Path("./sessions"))
            container.register_instance(FileSessionStore, session_store)
        
        # 注册Git管理器
        if not container.has_service(GitManager):
            git_manager = create_git_manager(use_mock=True)  # 使用模拟管理器避免Git依赖
            container.register_instance(GitManager, git_manager)
        
        # 注册工作流管理器
        if not container.has_service(WorkflowManager):
            workflow_manager = WorkflowManager(container.get(IConfigLoader))
            container.register_instance(WorkflowManager, workflow_manager)
        
        # 注册会话管理器
        if not container.has_service(ISessionManager):
            session_manager = SessionManager(
                workflow_manager=container.get(WorkflowManager),
                session_store=container.get(FileSessionStore),
                git_manager=container.get(GitManager)
            )
            container.register_instance(ISessionManager, session_manager)
    
    def _initialize_components(self) -> None:
        """初始化组件"""
        self.sidebar_component = SidebarComponent(self.config)
        self.langgraph_component = LangGraphPanelComponent(self.config)
        self.main_content_component = MainContentComponent(self.config)
        self.input_component = InputPanelComponent(self.config)
        
        # 初始化对话框
        self.session_dialog = SessionManagerDialog(self.config)
        self.agent_dialog = AgentSelectDialog(self.config)
        
        # 设置会话对话框的会话管理器
        if self.session_manager:
            self.session_dialog.set_session_manager(self.session_manager)
        
        # 加载Agent配置
        self.agent_dialog.load_agent_configs()
        
        # 组件字典
        self.components = {
            "sidebar": self.sidebar_component,
            "langgraph": self.langgraph_component,
            "main_content": self.main_content_component,
            "input": self.input_component,
            "session_dialog": self.session_dialog,
            "agent_dialog": self.agent_dialog
        }
    
    def _initialize_subviews(self) -> None:
        """初始化子界面"""
        self.analytics_view = AnalyticsSubview(self.config)
        self.visualization_view = VisualizationSubview(self.config)
        self.system_view = SystemSubview(self.config)
        self.errors_view = ErrorFeedbackSubview(self.config)
        
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
        self.event_engine.register_key_handler("escape", self._handle_escape_key)
        self.event_engine.register_key_handler("alt+1", lambda _: self._switch_to_subview("analytics"))
        self.event_engine.register_key_handler("alt+2", lambda _: self._switch_to_subview("visualization"))
        self.event_engine.register_key_handler("alt+3", lambda _: self._switch_to_subview("system"))
        self.event_engine.register_key_handler("alt+4", lambda _: self._switch_to_subview("errors"))
    
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
        try:
            self.running = True
            
            # 设置终端模式
            with self.terminal.cbreak(), self.terminal.hidden_cursor():
                # 获取终端尺寸
                terminal_size = self.console.size
                
                # 创建布局
                layout = self.layout_manager.create_layout(terminal_size)
                
                # 启动Live显示
                with Live(layout, console=self.console, refresh_per_second=self.config.behavior.refresh_rate) as live:
                    self.live = live
                    self.render_controller.set_live(live)
                    
                    # 显示欢迎信息
                    self.render_controller.show_welcome_message()
                    
                    # 启动事件循环
                    self._run_main_loop()
                
        except KeyboardInterrupt:
            self._handle_shutdown()
        except Exception as e:
            self.console.print(f"[red]TUI运行错误: {e}[/red]")
            raise
        finally:
            self.running = False
            self.live = None
    
    def _handle_global_key(self, key: str) -> bool:
        """处理全局按键
        
        Args:
            key: 按键字符串
            
        Returns:
            bool: 是否处理了该按键
        """
        # 如果在子界面中，优先让子界面处理按键
        if self.state_manager.current_subview:
            return self.subview_controller.handle_key(key)
        
        # 处理对话框中的按键
        if self.state_manager.show_session_dialog:
            result = self.session_dialog.handle_key(key)
            return result is not None
        elif self.state_manager.show_agent_dialog:
            result = self.agent_dialog.handle_key(key)
            return result is not None
        
        return False
    
    def _handle_escape_key(self, key: str) -> bool:
        """处理ESC键
        
        Args:
            key: 按键字符串
            
        Returns:
            bool: 是否处理了该按键
        """
        if self.state_manager.current_subview:
            self.subview_controller.return_to_main_view()
            # 立即同步状态管理器的状态
            self.state_manager.current_subview = None
            return True
        elif self.state_manager.show_session_dialog:
            self.state_manager.set_show_session_dialog(False)
            return True
        elif self.state_manager.show_agent_dialog:
            self.state_manager.set_show_agent_dialog(False)
            return True
        
        return False
    
    def _switch_to_subview(self, subview_name: str) -> bool:
        """切换到指定子界面
        
        Args:
            subview_name: 子界面名称
            
        Returns:
            bool: 切换是否成功
        """
        if self.subview_controller.switch_to_subview(subview_name):
            # 立即同步状态管理器的状态
            self.state_manager.current_subview = subview_name
            return True
        return False
    
    def _handle_input_result(self, result: str) -> None:
        """处理输入组件返回的结果
        
        Args:
            result: 输入组件返回的结果
        """
        if result == "CLEAR_SCREEN":
            self.state_manager.clear_message_history()
            self.main_content_component.clear_all()
            self.state_manager.add_system_message("屏幕已清空")
        elif result == "EXIT":
            self.running = False
        elif result and result.startswith("LOAD_SESSION:"):
            session_id = result.split(":", 1)[1]
            self._load_session(session_id)
        elif result in ["SAVE_SESSION", "NEW_SESSION", "PAUSE_WORKFLOW",
                      "RESUME_WORKFLOW", "STOP_WORKFLOW", "OPEN_STUDIO",
                      "OPEN_SESSIONS", "OPEN_AGENTS"]:
            # 处理命令
            command = result.lower()
            self.command_processor.process_command(command, [])
        elif result:
            # 显示命令结果
            self.state_manager.add_system_message(result)
            self.main_content_component.add_assistant_message(result)
    
    def _handle_input_submit(self, input_text: str) -> None:
        """处理输入提交
        
        Args:
            input_text: 输入文本
        """
        # 添加用户消息到历史
        self.state_manager.add_user_message(input_text)
        
        # 添加到主内容组件
        self.main_content_component.add_user_message(input_text)
        
        # 处理用户输入
        self._process_user_input(input_text)
    
    def _handle_command(self, command: str, args: List[str]) -> None:
        """处理命令
        
        Args:
            command: 命令名称
            args: 命令参数
        """
        # 特殊处理一些需要直接操作状态的命令
        if command == "sessions":
            self.state_manager.set_show_session_dialog(True)
            self.session_dialog.refresh_sessions()
            self.state_manager.add_system_message("已打开会话管理对话框")
        elif command == "agents":
            self.state_manager.set_show_agent_dialog(True)
            self.state_manager.add_system_message("已打开Agent选择对话框")
        elif command in ["analytics", "visualization", "system", "errors"]:
            self._switch_to_subview(command)
        elif command == "main":
            self.subview_controller.return_to_main_view()
        else:
            # 其他命令交给命令处理器处理
            self.command_processor.process_command(command, args)
    
    def _process_user_input(self, input_text: str) -> None:
        """处理用户输入
        
        Args:
            input_text: 用户输入
        """
        # 这里可以添加实际的处理逻辑
        # 例如：调用工作流处理输入
        # 暂时添加一个简单的回复
        response = f"收到您的输入: {input_text}"
        self.state_manager.add_assistant_message(response)
        self.main_content_component.add_assistant_message(response)
    
    def _load_session(self, session_id: str) -> None:
        """加载会话
        
        Args:
            session_id: 会话ID
        """
        if self.session_handler:
            result = self.session_handler.load_session(session_id)
            if result:
                workflow, state = result
                self.state_manager.session_id = session_id
                self.state_manager.current_workflow = workflow
                self.state_manager.current_state = state
                self.state_manager.message_history = []
                self.state_manager.add_system_message(f"会话 {session_id[:8]}... 已加载")
            else:
                self.state_manager.add_system_message("加载会话失败")
        else:
            self.state_manager.add_system_message("会话处理器未初始化")
    
    def _handle_shutdown(self) -> None:
        """处理关闭事件"""
        # 保存会话
        if self.state_manager.session_id and self.state_manager.current_state and self.session_handler:
            success = self.session_handler.save_session(
                self.state_manager.session_id,
                self.state_manager.current_workflow,
                self.state_manager.current_state
            )
            if success:
                self.console.print("[green]会话已保存[/green]")
            else:
                self.console.print("[red]保存会话失败[/red]")
        
        self.console.print("[yellow]正在关闭TUI界面...[/yellow]")
        self.running = False
    
    # 回调方法
    def _on_session_selected(self, session_id: str) -> None:
        """会话选择回调"""
        try:
            self._load_session(session_id)
            self.state_manager.set_show_session_dialog(False)
            self.state_manager.add_system_message(f"已切换到会话 {session_id[:8]}...")
        except Exception as e:
            self.state_manager.add_system_message(f"切换会话失败: {e}")
    
    def _on_session_created(self, workflow_config: str, agent_config: Optional[str]) -> None:
        """会话创建回调"""
        try:
            session_id = self.session_handler.create_session(workflow_config, {} if agent_config else None)
            if session_id:
                result = self.session_handler.load_session(session_id)
                if result:
                    workflow, state = result
                    self.state_manager.session_id = session_id
                    self.state_manager.current_workflow = workflow
                    self.state_manager.current_state = state
                    self.state_manager.message_history = []
                    self.state_manager.set_show_session_dialog(False)
                    self.state_manager.add_system_message(f"已创建新会话 {session_id[:8]}...")
            else:
                self.state_manager.add_system_message("创建会话失败")
        except Exception as e:
            self.state_manager.add_system_message(f"创建会话失败: {e}")
    
    def _on_session_deleted(self, session_id: str) -> None:
        """会话删除回调"""
        try:
            success = self.session_handler.delete_session(session_id)
            if success:
                self.state_manager.add_system_message(f"已删除会话 {session_id[:8]}...")
                # 如果删除的是当前会话，重置状态
                if self.state_manager.session_id == session_id:
                    self.state_manager.session_id = None
                    self.state_manager.current_state = None
                    self.state_manager.current_workflow = None
                    self.state_manager.message_history = []
                    self.main_content_component.clear_all()
            else:
                self.state_manager.add_system_message("删除会话失败")
        except Exception as e:
            self.state_manager.add_system_message(f"删除会话失败: {e}")
    
    def _run_main_loop(self) -> None:
        """运行主循环"""
        import time
        
        # 启动事件循环线程
        import threading
        event_thread = threading.Thread(target=self.event_engine.start_event_loop, daemon=True)
        event_thread.start()
        
        # 主循环负责更新UI
        while self.running:
            try:
                # 更新UI
                self.update_ui()
                
                # 短暂休眠以减少CPU使用率
                time.sleep(0.05)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[red]主循环错误: {e}[/red]")
                break
        
        # 停止事件引擎
        self.event_engine.stop()
    
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
    
    def update_ui(self) -> None:
        """更新UI显示"""
        # 同步状态管理器中的子界面状态
        current_subview_name = self.subview_controller.get_current_subview_name()
        if self.state_manager.current_subview != current_subview_name:
            self.state_manager.current_subview = current_subview_name
        
        # 同步对话框状态 - 暂时保持原有状态，因为对话框没有is_visible方法
        # 这里可以根据实际需要添加对话框状态检测逻辑
        
        # 使用渲染控制器更新UI
        self.render_controller.update_ui(self.state_manager)