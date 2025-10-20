"""TUI应用程序主文件"""

import asyncio
from typing import Optional, Dict, Any, List
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
    InputPanelComponent
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
        
        # 设置组件回调
        self._setup_component_callbacks()
        
        # 初始化依赖
        self._initialize_dependencies()
    
    def _setup_component_callbacks(self) -> None:
        """设置组件回调函数"""
        # 设置输入组件回调
        self.input_component.set_submit_callback(self._handle_input_submit)
        self.input_component.set_command_callback(self._handle_command)
    
    def _initialize_dependencies(self) -> None:
        """初始化依赖注入"""
        try:
            container = get_global_container()
            self.session_manager = container.get(ISessionManager)
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
                
                # 更新UI
                self._update_ui()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[red]事件循环错误: {e}[/red]")
                break
    
    def _update_ui(self) -> None:
        """更新UI显示"""
        if not self.live:
            return
        
        # 更新组件状态
        self._update_components()
        
        # 更新各个区域的内容
        self._update_header()
        self._update_sidebar()
        self._update_main_content()
        self._update_langgraph_panel()
        self._update_input_area()
        
        # 刷新显示
        self.live.refresh()
    
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
            self._open_studio()
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
        help_text = self.input_component.command_processor.get_command_help()
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