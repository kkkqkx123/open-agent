"""TUI应用程序主文件"""

import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from .layout import LayoutManager, LayoutRegion, LayoutConfig, RegionConfig
from .config import get_tui_config, TUIConfig
from .components import (
    SidebarComponent,
    LangGraphPanelComponent,
    MainContentComponent,
    InputPanelComponent,
    SessionManagerDialog,
    AgentSelectDialog,
    SidebarComponent
)
from .subviews import (
    AnalyticsSubview,
    VisualizationSubview,
    SystemSubview,
    ErrorFeedbackSubview
)
from src.infrastructure.container import get_global_container
from src.session.manager import ISessionManager
from src.prompts.agent_state import AgentState, HumanMessage, BaseMessage


class TUIApp:
    """TUI应用程序"""
    
    def __init__(self) -> None:
        """初始化TUI应用程序"""
        self.console = Console()
        
        # 加载配置
        self.config = get_tui_config()
        
        # 使用配置创建布局管理器
        self.layout_manager = LayoutManager(self.config.layout)
        self.live: Optional[Live] = None
        self.running = False
        
        # 会话相关
        self.session_id: Optional[str] = None
        self.session_manager: Optional[ISessionManager] = None
        self.current_state: Optional[AgentState] = None
        
        # UI状态
        self.input_buffer = ""
        self.message_history: List[Dict[str, Any]] = []
        self.current_workflow: Optional[Any] = None
        
        # 初始化组件
        self.sidebar_component = SidebarComponent(self.config)
        self.langgraph_component = LangGraphPanelComponent(self.config)
        self.main_content_component = MainContentComponent(self.config)
        self.input_component = InputPanelComponent(self.config)
        
        # 初始化对话框
        self.session_dialog = SessionManagerDialog(self.config)
        self.agent_dialog = AgentSelectDialog(self.config)
        
        # 对话框状态
        self.show_session_dialog = False
        self.show_agent_dialog = False
        
        # 子界面状态管理
        self.current_subview: Optional[str] = None  # None, "analytics", "visualization", "system", "errors"
        
        # 初始化子界面组件
        self.analytics_view = AnalyticsSubview(self.config)
        self.visualization_view = VisualizationSubview(self.config)
        self.system_view = SystemSubview(self.config)
        self.errors_view = ErrorFeedbackSubview(self.config)
        
        # 设置子界面回调
        self._setup_subview_callbacks()
        
        # 设置组件回调
        self._setup_component_callbacks()
        self._setup_dialog_callbacks()
        
        # 初始化依赖
        self._initialize_dependencies()
    
    def _setup_component_callbacks(self) -> None:
        """设置组件回调函数"""
        # 设置输入组件回调
        self.input_component.set_submit_callback(self._handle_input_submit)
        self.input_component.set_command_callback(self._handle_command)
    
    def _setup_subview_callbacks(self) -> None:
        """设置子界面回调函数"""
        # 设置分析监控子界面回调
        self.analytics_view.set_callback("data_refreshed", self._on_analytics_data_refreshed)
        
        # 设置可视化调试子界面回调
        self.visualization_view.set_callback("node_selected", self._on_visualization_node_selected)
        
        # 设置系统管理子界面回调
        self.system_view.set_callback("studio_started", self._on_studio_started)
        self.system_view.set_callback("studio_stopped", self._on_studio_stopped)
        self.system_view.set_callback("config_reloaded", self._on_config_reloaded)
        
        # 设置错误反馈子界面回调
        self.errors_view.set_callback("feedback_submitted", self._on_error_feedback_submitted)
    
    def _setup_dialog_callbacks(self) -> None:
        """设置对话框回调函数"""
        # 设置会话对话框回调
        self.session_dialog.set_session_selected_callback(self._on_session_selected)
        self.session_dialog.set_session_created_callback(self._on_session_created)
        self.session_dialog.set_session_deleted_callback(self._on_session_deleted)
        
        # 设置Agent对话框回调
        self.agent_dialog.set_agent_selected_callback(self._on_agent_selected)
    
    def _initialize_dependencies(self) -> None:
        """初始化依赖注入"""
        try:
            container = get_global_container()
            self.session_manager = container.get(ISessionManager)  # type: ignore
            
            # 设置会话对话框的会话管理器
            self.session_dialog.set_session_manager(self.session_manager)
            
            # 加载Agent配置
            self.agent_dialog.load_agent_configs()
            
        except Exception as e:
            self.console.print(f"[red]初始化依赖失败: {e}[/red]")
    
    def run(self) -> None:
        """运行TUI应用程序"""
        try:
            self.running = True
            
            # 获取终端尺寸
            terminal_size = self.console.size
            
            # 创建布局
            layout = self.layout_manager.create_layout(terminal_size)
            
            # 启动Live显示
            with Live(layout, console=self.console, refresh_per_second=self.config.behavior.refresh_rate) as live:
                self.live = live
                
                # 显示欢迎信息
                self._show_welcome_message()
                
                # 主事件循环
                self._run_event_loop()
                
        except KeyboardInterrupt:
            self._handle_shutdown()
        except Exception as e:
            self.console.print(f"[red]TUI运行错误: {e}[/red]")
            raise
        finally:
            self.running = False
            self.live = None
    
    def _run_event_loop(self) -> None:
        """运行主事件循环"""
        # 简化的事件循环，实际应用中可以使用更复杂的输入处理
        while self.running:
            try:
                # 模拟用户输入（实际应用中需要真实的输入处理）
                import time
                time.sleep(0.1)
                
                # 处理快捷键（这里需要实际的键盘输入处理）
                # 在实际实现中，需要集成键盘输入库如keyboard或prompt_toolkit
                
                # 更新UI
                self._update_ui()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[red]事件循环错误: {e}[/red]")
                break
    
    def handle_key(self, key: str) -> bool:
        """处理键盘输入
        
        Args:
            key: 按键字符串
            
        Returns:
            bool: True表示已处理，False表示需要传递到下层
        """
        # 如果在子界面中，优先让子界面处理按键
        if self.current_subview:
            subview = self._get_current_subview()
            if subview and subview.handle_key(key):
                return True
        
        # 处理全局快捷键
        if key == "escape":
            # ESC键返回主界面
            if self.current_subview:
                self.current_subview = None
                return True
            elif self.show_session_dialog:
                self.show_session_dialog = False
                return True
            elif self.show_agent_dialog:
                self.show_agent_dialog = False
                return True
        
        # 子界面快捷键
        elif key == "alt+1":
            self.current_subview = "analytics"
            return True
        elif key == "alt+2":
            self.current_subview = "visualization"
            return True
        elif key == "alt+3":
            self.current_subview = "system"
            return True
        elif key == "alt+4":
            self.current_subview = "errors"
            return True
        
        return False
    
    def _get_current_subview(self) -> Optional[Any]:
        """获取当前子界面对象
        
        Returns:
            BaseSubview: 当前子界面对象
        """
        if self.current_subview == "analytics":
            return self.analytics_view
        elif self.current_subview == "visualization":
            return self.visualization_view
        elif self.current_subview == "system":
            return self.system_view
        elif self.current_subview == "errors":
            return self.errors_view
        return None
    
    def _update_ui(self) -> None:
        """更新UI显示"""
        if not self.live:
            return
        
        # 检查是否显示子界面
        if self.current_subview:
            self._render_subview()
        elif self.show_session_dialog or self.show_agent_dialog:
            self._update_dialogs()
        else:
            # 更新主界面
            self._update_main_view()
        
        # 刷新显示
        self.live.refresh()
    
    def _render_subview(self) -> None:
        """渲染子界面"""
        if self.current_subview == "analytics":
            content = self.analytics_view.render()
        elif self.current_subview == "visualization":
            content = self.visualization_view.render()
        elif self.current_subview == "system":
            content = self.system_view.render()
        elif self.current_subview == "errors":
            content = self.errors_view.render()
        else:
            # 未知子界面，返回主界面
            self.current_subview = None
            self._update_main_view()
            return
        
        # 更新布局显示子界面
        self.layout_manager.update_region_content(LayoutRegion.MAIN, content)
        
        # 隐藏其他区域
        self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
        self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
        self.layout_manager.update_region_content(LayoutRegion.STATUS, "")
        
        # 更新标题栏显示子界面信息
        self._update_subview_header()
    
    def _update_main_view(self) -> None:
        """更新主界面"""
        # 更新组件状态
        self._update_components()
        
        # 更新各个区域的内容
        self._update_header()
        self._update_sidebar()
        self._update_main_content()
        self._update_input_area()
        self._update_status_bar()
    
    def _update_subview_header(self) -> None:
        """更新子界面标题栏"""
        title_text = Text("模块化代理框架", style="bold cyan")
        
        if self.current_subview == "analytics":
            subtitle_text = Text(" - 分析监控", style="bold green")
        elif self.current_subview == "visualization":
            subtitle_text = Text(" - 可视化调试", style="bold cyan")
        elif self.current_subview == "system":
            subtitle_text = Text(" - 系统管理", style="bold blue")
        elif self.current_subview == "errors":
            subtitle_text = Text(" - 错误反馈", style="bold red")
        else:
            subtitle_text = Text(" - TUI界面", style="dim")
        
        if self.session_id:
            session_info = Text(f" | 会话: {self.session_id[:8]}...", style="yellow")
        else:
            session_info = Text(" | 未连接", style="red")
        
        header_content = Text()
        header_content.append(title_text)
        header_content.append(subtitle_text)
        header_content.append(session_info)
        
        header_panel = Panel(
            header_content,
            style=self.config.theme.primary_color,
            border_style=self.config.theme.primary_color
        )
        
        self.layout_manager.update_region_content(LayoutRegion.HEADER, header_panel)
    
    def _update_components(self) -> None:
        """更新组件状态"""
        # 更新所有组件的状态
        self.sidebar_component.update_from_state(self.current_state)
        self.langgraph_component.update_from_state(
            self.current_state,
            current_node=getattr(self.current_state, 'current_step', '未运行') if self.current_state else '未运行',
            node_status="running" if self.current_state and self.current_state.iteration_count < self.current_state.max_iterations else "idle"
        )
        self.main_content_component.update_from_state(self.current_state)
        
        # 更新子界面数据
        self._update_subviews_data()
    
    def _update_subviews_data(self) -> None:
        """更新子界面数据"""
        # 更新分析监控子界面数据
        if self.current_state:
            # 性能数据
            performance_data = {
                "total_requests": getattr(self.current_state, 'total_requests', 0),
                "avg_response_time": getattr(self.current_state, 'avg_response_time', 0.0),
                "success_rate": getattr(self.current_state, 'success_rate', 100.0),
                "error_count": getattr(self.current_state, 'error_count', 0),
                "tokens_used": getattr(self.current_state, 'tokens_used', 0),
                "cost_estimate": getattr(self.current_state, 'cost_estimate', 0.0)
            }
            self.analytics_view.update_performance_data(performance_data)
            
            # 系统指标
            system_metrics = {
                "cpu_usage": getattr(self.current_state, 'cpu_usage', 0.0),
                "memory_usage": getattr(self.current_state, 'memory_usage', 0.0),
                "disk_usage": getattr(self.current_state, 'disk_usage', 0.0),
                "network_io": getattr(self.current_state, 'network_io', 0.0)
            }
            self.analytics_view.update_system_metrics(system_metrics)
        
        # 更新可视化调试子界面数据
        if self.current_state and hasattr(self.current_state, 'workflow_data'):
            workflow_data = {
                "nodes": getattr(self.current_state, 'workflow_nodes', []),
                "edges": getattr(self.current_state, 'workflow_edges', []),
                "current_node": getattr(self.current_state, 'current_step', None),
                "execution_path": getattr(self.current_state, 'execution_path', []),
                "node_states": getattr(self.current_state, 'node_states', {})
            }
            self.visualization_view.update_workflow_data(workflow_data)
        
        # 更新系统管理子界面数据
        studio_status = {
            "running": getattr(self.current_state, 'studio_running', False),
            "port": getattr(self.current_state, 'studio_port', 8079),
            "url": getattr(self.current_state, 'studio_url', ""),
            "start_time": getattr(self.current_state, 'studio_start_time', None),
            "version": "1.0.0",
            "connected_clients": getattr(self.current_state, 'studio_clients', 0)
        }
        self.system_view.update_studio_status(studio_status)
        
        # 更新错误反馈子界面数据
        if self.current_state and hasattr(self.current_state, 'errors') and getattr(self.current_state, 'errors', None):
            for error in self.current_state.errors:
                self.errors_view.add_error(error)
    
    def _update_header(self) -> None:
        """更新标题栏"""
        title_text = Text("模块化代理框架", style="bold cyan")
        subtitle_text = Text("TUI界面", style="dim")
        
        if self.session_id:
            session_info = Text(f" | 会话: {self.session_id[:8]}...", style="yellow")
        else:
            session_info = Text(" | 未连接", style="red")
        
        header_content = Text()
        header_content.append(title_text)
        header_content.append(" - ")
        header_content.append(subtitle_text)
        header_content.append(session_info)
        
        header_panel = Panel(
            header_content,
            style=self.config.theme.primary_color,
            border_style=self.config.theme.primary_color
        )
        
        self.layout_manager.update_region_content(LayoutRegion.HEADER, header_panel)
    
    def _update_sidebar(self) -> None:
        """更新侧边栏"""
        if not self.layout_manager.is_region_visible(LayoutRegion.SIDEBAR):
            return
        
        # 使用侧边栏组件
        sidebar_panel = self.sidebar_component.render()
        self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, sidebar_panel)
    
    def _update_main_content(self) -> None:
        """更新主内容区"""
        # 使用主内容组件
        main_panel = self.main_content_component.render()
        self.layout_manager.update_region_content(LayoutRegion.MAIN, main_panel)
    
    def _update_input_area(self) -> None:
        """更新输入区域"""
        # 使用输入组件
        input_panel = self.input_component.render()
        self.layout_manager.update_region_content(LayoutRegion.INPUT, input_panel)
    
    def _update_langgraph_panel(self) -> None:
        """更新LangGraph面板"""
        # 使用LangGraph组件
        langgraph_panel = self.langgraph_component.render()
        self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, langgraph_panel)
    
    def _update_dialogs(self) -> None:
        """更新对话框显示"""
        if self.show_session_dialog:
            # 显示会话管理对话框，覆盖整个主内容区
            dialog_panel = self.session_dialog.render()
            self.layout_manager.update_region_content(LayoutRegion.MAIN, dialog_panel)
            
            # 隐藏其他区域
            self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
            self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
            
        elif self.show_agent_dialog:
            # 显示Agent选择对话框，覆盖整个主内容区
            dialog_panel = self.agent_dialog.render()
            self.layout_manager.update_region_content(LayoutRegion.MAIN, dialog_panel)
            
            # 隐藏其他区域
            self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
            self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
    
    def _show_welcome_message(self) -> None:
        """显示欢迎信息"""
        welcome_text = Text()
        welcome_text.append("正在启动TUI界面...\n", style="bold green")
        welcome_text.append("请稍候...", style="dim")
        
        welcome_panel = Panel(
            welcome_text,
            title="欢迎",
            border_style="cyan"
        )
        
        self.layout_manager.update_region_content(LayoutRegion.MAIN, welcome_panel)
        
        if self.live:
            self.live.refresh()
    
    def _handle_shutdown(self) -> None:
        """处理关闭事件"""
        # 保存会话
        if self.session_id and self.current_state and self.session_manager:
            try:
                self.session_manager.save_session(self.session_id, self.current_workflow, self.current_state)
                self.console.print("[green]会话已保存[/green]")
            except Exception as e:
                self.console.print(f"[red]保存会话失败: {e}[/red]")
        
        self.console.print("[yellow]正在关闭TUI界面...[/yellow]")
        self.running = False
    
    def create_session(self, workflow_config: str, agent_config: Optional[str] = None) -> bool:
        """创建新会话"""
        try:
            if not self.session_manager:
                self.console.print("[red]会话管理器未初始化[/red]")
                return False
            
            # 创建会话
            self.session_id = self.session_manager.create_session(
                workflow_config_path=workflow_config,
                agent_config={} if agent_config else None
            )
            
            # 恢复会话以获取工作流和状态
            self.current_workflow, self.current_state = self.session_manager.restore_session(self.session_id)
            
            # 清空消息历史
            self.message_history = []
            
            # 添加系统消息
            self.message_history.append({
                "type": "system",
                "content": f"新会话已创建: {self.session_id[:8]}..."
            })
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]创建会话失败: {e}[/red]")
            return False
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.message_history.append({
            "type": "user",
            "content": content
        })
        
        # 更新状态
        if self.current_state:
            human_message = HumanMessage(content=content)
            self.current_state.add_message(human_message)
    
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息"""
        self.message_history.append({
            "type": "assistant",
            "content": content
        })
    
    def add_system_message(self, content: str) -> None:
        """添加系统消息"""
        self.message_history.append({
            "type": "system",
            "content": content
        })
    
    def set_input_buffer(self, text: str) -> None:
        """设置输入缓冲区"""
        self.input_buffer = text
    
    def clear_input_buffer(self) -> None:
        """清空输入缓冲区"""
        self.input_buffer = ""
    
    def get_current_breakpoint(self) -> str:
        """获取当前断点"""
        return self.layout_manager.get_current_breakpoint()
    
    def _handle_input_submit(self, input_text: str) -> None:
        """处理输入提交
        
        Args:
            input_text: 输入文本
        """
        # 添加用户消息到历史
        self.add_user_message(input_text)
        
        # 添加到主内容组件
        self.main_content_component.add_user_message(input_text)
        
        # 更新状态
        if self.current_state:
            human_message = HumanMessage(content=input_text)
            self.current_state.add_message(human_message)
        
        # 这里可以添加处理用户输入的逻辑
        # 例如：调用工作流处理输入
        self._process_user_input(input_text)
    
    def _handle_command(self, command: str, args: List[str]) -> None:
        """处理命令
        
        Args:
            command: 命令名称
            args: 命令参数
        """
        if command == "help":
            self._show_help()
        elif command == "clear":
            self._clear_screen()
        elif command == "exit":
            self._exit_app()
        elif command == "save":
            self._save_session()
        elif command == "load":
            if args:
                self._load_session(args[0])
        elif command == "new":
            self._create_new_session()
        elif command == "pause":
            self._pause_workflow()
        elif command == "resume":
            self._resume_workflow()
        elif command == "stop":
            self._stop_workflow()
        elif command == "studio":
            # 重定向到系统管理子界面
            self.current_subview = "system"
        elif command == "sessions":
            self._open_session_dialog()
        elif command == "agents":
            self._open_agent_dialog()
        elif command == "performance":
            # 重定向到分析监控子界面
            self.current_subview = "analytics"
        elif command == "debug":
            # 重定向到可视化调试子界面
            self.current_subview = "visualization"
        elif command == "errors":
            # 重定向到错误反馈子界面
            self.current_subview = "errors"
        # 子界面切换命令
        elif command == "analytics":
            self.current_subview = "analytics"
        elif command == "visualization":
            self.current_subview = "visualization"
        elif command == "system":
            self.current_subview = "system"
        elif command == "errors":
            self.current_subview = "errors"
        elif command == "main":
            self.current_subview = None
        else:
            self.console.print(f"[red]未知命令: {command}[/red]")
    
    def _process_user_input(self, input_text: str) -> None:
        """处理用户输入
        
        Args:
            input_text: 用户输入
        """
        # 这里可以添加实际的处理逻辑
        # 例如：调用工作流处理输入
        # 暂时添加一个简单的回复
        self.add_assistant_message(f"收到您的输入: {input_text}")
        self.main_content_component.add_assistant_message(f"收到您的输入: {input_text}")
    
    def _show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
可用命令:
  /help - 显示帮助
  /clear - 清空屏幕
  /exit - 退出应用
  /save - 保存会话
  /load <session_id> - 加载会话
  /new - 创建新会话
  /pause - 暂停工作流
  /resume - 恢复工作流
  /stop - 停止工作流
  /studio - 打开系统管理界面
  /sessions - 打开会话管理
  /agents - 打开Agent选择
  /performance - 打开分析监控界面
  /debug - 打开可视化调试界面
  /errors - 打开错误反馈界面
  
子界面命令:
  /analytics - 打开分析监控界面
  /visualization - 打开可视化调试界面
  /system - 打开系统管理界面
  /errors - 打开错误反馈界面
  /main - 返回主界面

快捷键:
  Alt+1 - 分析监控
  Alt+2 - 可视化调试
  Alt+3 - 系统管理
  Alt+4 - 错误反馈
  ESC - 返回主界面
"""
        self.add_system_message(help_text)
        self.main_content_component.add_assistant_message(help_text)
    
    def _clear_screen(self) -> None:
        """清空屏幕"""
        self.message_history = []
        self.main_content_component.clear_all()
        self.add_system_message("屏幕已清空")
    
    def _exit_app(self) -> None:
        """退出应用"""
        self.running = False
    
    def _save_session(self) -> None:
        """保存会话"""
        if self.session_id and self.current_state and self.session_manager:
            try:
                self.session_manager.save_session(self.session_id, self.current_workflow, self.current_state)
                self.add_system_message(f"会话 {self.session_id[:8]}... 已保存")
            except Exception as e:
                self.add_system_message(f"保存会话失败: {e}")
        else:
            self.add_system_message("无活动会话可保存")
    
    def _load_session(self, session_id: str) -> None:
        """加载会话
        
        Args:
            session_id: 会话ID
        """
        if not self.session_manager:
            self.add_system_message("会话管理器未初始化")
            return
        
        try:
            self.current_workflow, self.current_state = self.session_manager.restore_session(session_id)
            self.session_id = session_id
            self.message_history = []
            self.add_system_message(f"会话 {session_id[:8]}... 已加载")
        except Exception as e:
            self.add_system_message(f"加载会话失败: {e}")
    
    def _create_new_session(self) -> None:
        """创建新会话"""
        # 这里可以添加创建新会话的逻辑
        self.session_id = None
        self.current_state = AgentState()
        self.current_workflow = None
        self.message_history = []
        self.main_content_component.clear_all()
        self.add_system_message("已创建新会话")
    
    def _pause_workflow(self) -> None:
        """暂停工作流"""
        self.add_system_message("工作流已暂停")
    
    def _resume_workflow(self) -> None:
        """恢复工作流"""
        self.add_system_message("工作流已恢复")
    
    def _stop_workflow(self) -> None:
        """停止工作流"""
        self.add_system_message("工作流已停止")
    
    def _open_studio(self) -> None:
        """打开Studio"""
        self.add_system_message("Studio功能尚未实现")
    
    def _open_session_dialog(self) -> None:
        """打开会话管理对话框"""
        self.show_session_dialog = True
        self.session_dialog.refresh_sessions()
        self.add_system_message("已打开会话管理对话框")
    
    def _open_agent_dialog(self) -> None:
        """打开Agent选择对话框"""
        self.show_agent_dialog = True
        self.add_system_message("已打开Agent选择对话框")
    
    def _on_session_selected(self, session_id: str) -> None:
        """会话选择回调"""
        try:
            self._load_session(session_id)
            self.show_session_dialog = False
            self.add_system_message(f"已切换到会话 {session_id[:8]}...")
        except Exception as e:
            self.add_system_message(f"切换会话失败: {e}")
    
    def _on_session_created(self, workflow_config: str, agent_config: Optional[str]) -> None:
        """会话创建回调"""
        try:
            success = self.create_session(workflow_config, agent_config)
            if success:
                self.show_session_dialog = False
                self.add_system_message(f"已创建新会话 {self.session_id[:8]}..." if self.session_id else "已创建新会话")
            else:
                self.add_system_message("创建会话失败")
        except Exception as e:
            self.add_system_message(f"创建会话失败: {e}")
    
    def _on_session_deleted(self, session_id: str) -> None:
        """会话删除回调"""
        try:
            if self.session_manager:
                success = self.session_manager.delete_session(session_id)
                if success:
                    self.add_system_message(f"已删除会话 {session_id[:8]}...")
                    # 如果删除的是当前会话，重置状态
                    if self.session_id == session_id:
                        self.session_id = None
                        self.current_state = None
                        self.current_workflow = None
                        self.message_history = []
                        self.main_content_component.clear_all()
                else:
                    self.add_system_message("删除会话失败")
        except Exception as e:
            self.add_system_message(f"删除会话失败: {e}")
    
    def _on_agent_selected(self, agent_config: Any) -> None:
        """Agent选择回调"""
        try:
            # 更新侧边栏的Agent信息
            self.sidebar_component.update_agent_info(
                name=agent_config.name,
                model=agent_config.model,
                status="就绪"
            )
            
            self.show_agent_dialog = False
            self.add_system_message(f"已选择Agent: {agent_config.name}")
        except Exception as e:
            self.add_system_message(f"选择Agent失败: {e}")
    
    # 子界面回调方法
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
        self.add_system_message(f"Studio已启动: {studio_status.get('url', 'Unknown')}")
    
    def _on_studio_stopped(self, studio_status: Dict[str, Any]) -> None:
        """Studio停止回调"""
        self.add_system_message("Studio已停止")
    
    def _on_config_reloaded(self, config_data: Dict[str, Any]) -> None:
        """配置重载回调"""
        self.add_system_message("配置已重载")
    
    def _on_error_feedback_submitted(self, feedback_data: Dict[str, Any]) -> None:
        """错误反馈提交回调"""
        error_id = feedback_data.get("error_id", "Unknown")
        self.add_system_message(f"错误反馈已提交: {error_id}")
    
    def switch_to_subview(self, subview_name: str) -> None:
        """切换到指定子界面
        
        Args:
            subview_name: 子界面名称
        """
        valid_subviews = ["analytics", "visualization", "system", "errors"]
        if subview_name in valid_subviews:
            self.current_subview = subview_name
        else:
            self.add_system_message(f"无效的子界面: {subview_name}")
    
    def return_to_main_view(self) -> None:
        """返回主界面"""
        self.current_subview = None
    
    def _update_status_bar(self) -> None:
        """更新状态栏"""
        from rich.text import Text
        from rich.panel import Panel
        
        status_text = Text()
        status_text.append("快捷键: ", style="bold")
        status_text.append("Alt+1=分析, Alt+2=可视化, Alt+3=系统, Alt+4=错误, ESC=返回", style="dim")
        status_text.append(" | ", style="dim")
        
        # 显示当前状态
        if self.current_subview:
            status_text.append(f"当前界面: {self.current_subview}", style="cyan")
        else:
            status_text.append("状态: 就绪", style="green")
        
        # 显示会话信息
        if self.session_id:
            status_text.append(f" | 会话: {self.session_id[:8]}...", style="yellow")
        
        status_panel = Panel(
            status_text,
            style="dim",
            border_style="dim"
        )
        
        self.layout_manager.update_region_content(LayoutRegion.STATUS, status_panel)