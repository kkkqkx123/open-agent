"""TUI渲染控制器"""

from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

from .layout import LayoutManager, LayoutRegion
from .components import (
    SidebarComponent,
    LangGraphPanelComponent,
    MainContentComponent,
    InputPanel,
    SessionManagerDialog,
    AgentSelectDialog
)
from .subviews import (
    AnalyticsSubview,
    VisualizationSubview,
    SystemSubview,
    ErrorFeedbackSubview
)


class RenderController:
    """渲染控制器，负责管理UI组件的渲染和更新"""
    
    def __init__(
        self,
        layout_manager: LayoutManager,
        components: Dict[str, Any],
        subviews: Dict[str, Any],
        config: Any
    ) -> None:
        """初始化渲染控制器
        
        Args:
            layout_manager: 布局管理器
            components: 组件字典
            subviews: 子界面字典
            config: TUI配置
        """
        self.layout_manager = layout_manager
        self.config = config
        self.live: Optional[Live] = None
        
        # 组件
        self.sidebar_component = components.get("sidebar")
        self.langgraph_component = components.get("langgraph")
        self.main_content_component = components.get("main_content")
        self.input_component = components.get("input")
        
        # 对话框
        self.session_dialog = components.get("session_dialog")
        self.agent_dialog = components.get("agent_dialog")
        
        # 子界面
        self.analytics_view = subviews.get("analytics")
        self.visualization_view = subviews.get("visualization")
        self.system_view = subviews.get("system")
        self.errors_view = subviews.get("errors")
    
    def set_live(self, live: Live) -> None:
        """设置Live对象
        
        Args:
            live: Rich Live对象
        """
        self.live = live
    
    def update_ui(self, state_manager: Any) -> None:
        """更新UI显示
        
        Args:
            state_manager: 状态管理器
        """
        if not self.live:
            return
        
        # 检查是否显示子界面
        if state_manager.current_subview:
            self._render_subview(state_manager)
        elif state_manager.show_session_dialog or state_manager.show_agent_dialog:
            self._update_dialogs(state_manager)
        else:
            # 更新主界面
            self._update_main_view(state_manager)
        
        # 刷新显示
        self.live.refresh()
    
    def _render_subview(self, state_manager: Any) -> None:
        """渲染子界面
        
        Args:
            state_manager: 状态管理器
        """
        content = None
        if state_manager.current_subview == "analytics" and self.analytics_view:
            content = self.analytics_view.render()
        elif state_manager.current_subview == "visualization" and self.visualization_view:
            content = self.visualization_view.render()
        elif state_manager.current_subview == "system" and self.system_view:
            content = self.system_view.render()
        elif state_manager.current_subview == "errors" and self.errors_view:
            content = self.errors_view.render()
        
        if content:
            # 更新布局显示子界面
            self.layout_manager.update_region_content(LayoutRegion.MAIN, content)
            
            # 隐藏其他区域
            self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
            self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
            self.layout_manager.update_region_content(LayoutRegion.STATUS, "")
            
            # 更新标题栏显示子界面信息
            self._update_subview_header(state_manager)
        else:
            # 未知子界面，返回主界面
            state_manager.current_subview = None
            self._update_main_view(state_manager)
    
    def _update_main_view(self, state_manager: Any) -> None:
        """更新主界面
        
        Args:
            state_manager: 状态管理器
        """
        # 更新组件状态
        self._update_components(state_manager)
        
        # 更新各个区域的内容
        self._update_header(state_manager)
        self._update_sidebar()
        self._update_main_content()
        self._update_input_area()
        self._update_langgraph_panel()
        self._update_status_bar(state_manager)
    
    def _update_subview_header(self, state_manager: Any) -> None:
        """更新子界面标题栏
        
        Args:
            state_manager: 状态管理器
        """
        title_text = Text("模块化代理框架", style="bold cyan")
        
        if state_manager.current_subview == "analytics":
            subtitle_text = Text(" - 分析监控", style="bold green")
        elif state_manager.current_subview == "visualization":
            subtitle_text = Text(" - 可视化调试", style="bold cyan")
        elif state_manager.current_subview == "system":
            subtitle_text = Text(" - 系统管理", style="bold blue")
        elif state_manager.current_subview == "errors":
            subtitle_text = Text(" - 错误反馈", style="bold red")
        else:
            subtitle_text = Text(" - TUI界面", style="dim")
        
        if state_manager.session_id:
            session_info = Text(f" | 会话: {state_manager.session_id[:8]}...", style="yellow")
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
    
    def _update_components(self, state_manager: Any) -> None:
        """更新组件状态
        
        Args:
            state_manager: 状态管理器
        """
        # 更新所有组件的状态
        if self.sidebar_component:
            self.sidebar_component.update_from_state(state_manager.current_state)
        
        if self.langgraph_component:
            self.langgraph_component.update_from_state(
                state_manager.current_state,
                current_node=getattr(state_manager.current_state, 'current_step', '未运行') if state_manager.current_state else '未运行',
                node_status="running" if state_manager.current_state and state_manager.current_state.iteration_count < state_manager.current_state.max_iterations else "idle"
            )
        
        if self.main_content_component:
            self.main_content_component.update_from_state(state_manager.current_state)
        
        # 更新子界面数据
        self._update_subviews_data(state_manager)
    
    def _update_subviews_data(self, state_manager: Any) -> None:
        """更新子界面数据
        
        Args:
            state_manager: 状态管理器
        """
        # 更新分析监控子界面数据
        if self.analytics_view and state_manager.current_state:
            performance_data = state_manager.get_performance_data()
            self.analytics_view.update_performance_data(performance_data)
            
            system_metrics = state_manager.get_system_metrics()
            self.analytics_view.update_system_metrics(system_metrics)
        
        # 更新可视化调试子界面数据
        if self.visualization_view and state_manager.current_state:
            workflow_data = state_manager.get_workflow_data()
            self.visualization_view.update_workflow_data(workflow_data)
        
        # 更新系统管理子界面数据
        if self.system_view:
            studio_status = state_manager.get_studio_status()
            self.system_view.update_studio_status(studio_status)
        
        # 更新错误反馈子界面数据
        if self.errors_view and state_manager.current_state:
            errors = state_manager.get_errors()
            for error in errors:
                self.errors_view.add_error(error)
    
    def _update_header(self, state_manager: Any) -> None:
        """更新标题栏
        
        Args:
            state_manager: 状态管理器
        """
        title_text = Text("模块化代理框架", style="bold cyan")
        subtitle_text = Text("TUI界面", style="dim")
        
        if state_manager.session_id:
            session_info = Text(f" | 会话: {state_manager.session_id[:8]}...", style="yellow")
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
        
        if self.sidebar_component:
            sidebar_panel = self.sidebar_component.render()
            self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, sidebar_panel)
    
    def _update_main_content(self) -> None:
        """更新主内容区"""
        if self.main_content_component:
            main_panel = self.main_content_component.render()
            self.layout_manager.update_region_content(LayoutRegion.MAIN, main_panel)
    
    def _update_input_area(self) -> None:
        """更新输入区域"""
        if self.input_component:
            input_panel = self.input_component.render()
            self.layout_manager.update_region_content(LayoutRegion.INPUT, input_panel)
    
    def _update_langgraph_panel(self) -> None:
        """更新LangGraph面板"""
        if self.langgraph_component:
            langgraph_panel = self.langgraph_component.render()
            self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, langgraph_panel)
    
    def _update_status_bar(self, state_manager: Any) -> None:
        """更新状态栏
        
        Args:
            state_manager: 状态管理器
        """
        status_text = Text()
        status_text.append("快捷键: ", style="bold")
        status_text.append("Alt+1=分析, Alt+2=可视化, Alt+3=系统, Alt+4=错误, ESC=返回", style="dim")
        status_text.append(" | ", style="dim")
        
        # 显示当前状态
        if state_manager.current_subview:
            status_text.append(f"当前界面: {state_manager.current_subview}", style="cyan")
        else:
            status_text.append("状态: 就绪", style="green")
        
        # 显示会话信息
        if state_manager.session_id:
            status_text.append(f" | 会话: {state_manager.session_id[:8]}...", style="yellow")
        
        status_panel = Panel(
            status_text,
            style="dim",
            border_style="dim"
        )
        
        self.layout_manager.update_region_content(LayoutRegion.STATUS, status_panel)
    
    def _update_dialogs(self, state_manager: Any) -> None:
        """更新对话框显示
        
        Args:
            state_manager: 状态管理器
        """
        if state_manager.show_session_dialog and self.session_dialog:
            # 显示会话管理对话框，覆盖整个主内容区
            dialog_panel = self.session_dialog.render()
            self.layout_manager.update_region_content(LayoutRegion.MAIN, dialog_panel)
            
            # 隐藏其他区域
            self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
            self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
            
        elif state_manager.show_agent_dialog and self.agent_dialog:
            # 显示Agent选择对话框，覆盖整个主内容区
            dialog_panel = self.agent_dialog.render()
            self.layout_manager.update_region_content(LayoutRegion.MAIN, dialog_panel)
            
            # 隐藏其他区域
            self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
            self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
    
    def show_welcome_message(self) -> None:
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