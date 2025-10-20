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
from ...infrastructure.container import get_global_container
from ...session.manager import ISessionManager
from ...prompts.agent_state import AgentState, HumanMessage, BaseMessage


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
        
        # 初始化依赖
        self._initialize_dependencies()
    
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
        
        # 更新各个区域的内容
        self._update_header()
        self._update_sidebar()
        self._update_main_content()
        self._update_input_area()
        
        # 刷新显示
        self.live.refresh()
    
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
        
        # 创建会话信息树
        tree = Tree("会话信息", style="bold green")
        
        if self.session_id:
            tree.add(f"ID: {self.session_id[:8]}...")
            
            if self.current_state:
                tree.add(f"消息数: {len(self.current_state.messages)}")
                tree.add(f"工具调用: {len(self.current_state.tool_results)}")
                tree.add(f"当前步骤: {getattr(self.current_state, 'current_step', '未知')}")
            
            # 添加快捷键信息
            shortcuts = tree.add("快捷键")
            shortcuts.add("Ctrl+C - 退出")
            shortcuts.add("Ctrl+H - 帮助")
            shortcuts.add("Ctrl+S - 保存会话")
        else:
            tree.add("无活动会话")
            tree.add("按 Ctrl+N 创建新会话")
        
        sidebar_panel = Panel(
            tree,
            title="会话",
            border_style=self.config.theme.secondary_color
        )
        
        self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, sidebar_panel)
    
    def _update_main_content(self) -> None:
        """更新主内容区"""
        if self.message_history:
            # 显示消息历史
            content = Text()
            
            for msg in self.message_history[-10:]:  # 显示最近10条消息
                if msg["type"] == "user":
                    content.append(f"用户: {msg['content']}\n", style="blue")
                elif msg["type"] == "assistant":
                    content.append(f"助手: {msg['content']}\n", style="green")
                elif msg["type"] == "system":
                    content.append(f"系统: {msg['content']}\n", style="yellow")
                content.append("\n")
        else:
            # 显示欢迎信息
            content = Text()
            content.append("欢迎使用模块化代理框架TUI界面\n\n", style="bold cyan")
            content.append("功能特性:\n", style="bold")
            content.append("• 多LLM支持 (OpenAI, Gemini, Anthropic)\n", style="dim")
            content.append("• 灵活的工具系统\n", style="dim")
            content.append("• 会话管理和持久化\n", style="dim")
            content.append("• 响应式布局\n", style="dim")
            content.append("\n")
            content.append("开始使用:\n", style="bold")
            content.append("1. 按 Ctrl+N 创建新会话\n", style="dim")
            content.append("2. 按 Ctrl+O 打开现有会话\n", style="dim")
            content.append("3. 按 Ctrl+H 查看帮助\n", style="dim")
        
        main_panel = Panel(
            content,
            title="主内容",
            border_style=self.config.theme.text_color
        )
        
        self.layout_manager.update_region_content(LayoutRegion.MAIN, main_panel)
    
    def _update_input_area(self) -> None:
        """更新输入区域"""
        if self.input_buffer:
            input_text = Text(f"> {self.input_buffer}", style="bold green")
        else:
            input_text = Text("> 在此输入消息...", style="dim")
        
        input_panel = Panel(
            input_text,
            title="输入",
            border_style=self.config.theme.secondary_color
        )
        
        self.layout_manager.update_region_content(LayoutRegion.INPUT, input_panel)
    
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