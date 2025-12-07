"""TUI渲染控制器"""

from typing import Optional, Dict, Any, List, Tuple
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

from .logger import get_tui_silent_logger
from .layout import LayoutManager, LayoutRegion
from .components import (
    SidebarComponent,
    MainContentComponent,
    InputPanel,
    SessionManagerDialog,
    AgentSelectDialog,
    NavigationBarComponent
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
        self.tui_logger = get_tui_silent_logger("render_controller")
        self.layout_manager = layout_manager
        self.config = config
        self.live: Optional[Live] = None
        self._needs_refresh: bool = False # 新增刷新标记
        self._last_render_state: Dict[str, Any] = {}  # 用于跟踪上次渲染状态
        self._render_stats: Dict[str, Any] = {
            'total_updates': 0,
            'skipped_updates': 0,
            'last_update_time': 0,
            'avg_update_interval': 0
        }  # 渲染统计信息
        
        # 组件
        self.sidebar_component = components.get("sidebar")
        self.main_content_component = components.get("main_content")
        self.input_component = components.get("input")
        self.workflow_control_panel = components.get("workflow_control")
        self.error_feedback_panel = components.get("error_feedback")
        self.navigation_component = components.get("navigation")
        
        # 对话框
        self.session_dialog = components.get("session_dialog")
        self.agent_dialog = components.get("agent_dialog")
        
        # 子界面
        self.analytics_view = subviews.get("analytics")
        self.visualization_view = subviews.get("visualization")
        self.system_view = subviews.get("system")
        self.errors_view = subviews.get("errors")
        self.status_overview_view = subviews.get("status_overview")
        
        # 注册布局变化回调
        self.layout_manager.register_layout_changed_callback(self._on_layout_changed)
    
    def set_live(self, live: Live) -> None:
        """设置Live对象
        
        Args:
            live: Rich Live对象
        """
        self.live = live
    
    def update_ui(self, state_manager: Any) -> bool:
        """更新UI显示
         
        Args:
            state_manager: 状态管理器
             
        Returns:
            bool: 是否需要刷新显示
        """
        import time
        start_time = time.time()
         
        # 检查状态变化以决定是否需要刷新
        current_state_hash = self._get_state_hash(state_manager)
        state_changed = current_state_hash != self._last_render_state.get('main_view_hash')
         
        # 如果状态没有变化，检查是否有强制刷新标记
        if not state_changed:
            force_refresh = getattr(state_manager, '_force_refresh', False)
            if not force_refresh:
                # 状态没有变化且没有强制刷新，跳过更新
                self._render_stats['skipped_updates'] += 1
                return False
         
        # 更新状态哈希 - 同时更新两个键以保持一致性
        self._last_render_state['hash'] = current_state_hash
        self._last_render_state['main_view_hash'] = current_state_hash
        
        # 重置刷新标记
        self._needs_refresh = False
        
        # 强制刷新标记 - 用于界面切换等场景
        force_refresh = getattr(state_manager, '_force_refresh', False)
        if force_refresh:
            # 清除哈希缓存，强制重新渲染
            self._last_render_state.pop('main_view_hash', None)
            self._last_render_state.pop('hash', None)
            state_manager._force_refresh = False  # 重置标记
        
        # 检查是否显示子界面
        if state_manager.current_subview:
            self._render_subview(state_manager)
        elif state_manager.show_session_dialog or state_manager.show_agent_dialog:
            self._update_dialogs(state_manager)
        else:
            # 更新主界面
            self._update_main_view(state_manager)
        
        # 检查并显示错误反馈面板
        self._check_error_feedback_panel()
        
        # 注意：不再在这里执行实际刷新，让主循环统一处理
        # 只返回是否需要刷新的标志
        
        return self._needs_refresh
    
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
        elif state_manager.current_subview == "status_overview" and self.status_overview_view:
            content = self.status_overview_view.render()
        
        if content:
            # 检查内容是否真正变化了
            import hashlib
            content_hash = hashlib.md5(str(content).encode() if content else b'').hexdigest()
            
            if self._last_render_state.get('subview_content_hash') != content_hash:
                # 更新布局显示子界面
                self.layout_manager.update_region_content(LayoutRegion.MAIN, content)
                
                # 隐藏其他区域
                self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
                self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
                self.layout_manager.update_region_content(LayoutRegion.STATUS, "")
                
                # 更新标题栏显示子界面信息
                self._update_subview_header(state_manager)
                
                # 标记需要刷新
                self._needs_refresh = True
                self._last_render_state['subview_content_hash'] = content_hash
        else:
            # 未知子界面，返回主界面
            state_manager.current_subview = None
            self._update_main_view(state_manager)
    def _update_main_view(self, state_manager: Any) -> None:
        """更新主界面
        
        Args:
            state_manager: 状态管理器
        """
        # 保存当前状态的哈希值，用于检测变化
        import hashlib
        import json
        
        # 创建当前状态的摘要 - 包含子界面状态以确保界面切换时触发刷新
        state_summary = {
            "session_id": getattr(state_manager, 'session_id', ''),
            "message_count": len(getattr(state_manager, 'message_history', [])),
            "current_state": str(getattr(state_manager, 'current_state', None)),
            "current_subview": getattr(state_manager, 'current_subview', None)  # 关键：包含子界面状态
        }
        
        # 添加输入缓冲区状态检测 - 从输入组件获取实际的输入缓冲区状态
        if hasattr(self, 'input_component') and self.input_component:
            input_buffer = self.input_component.input_buffer
            if input_buffer:
                state_summary['input_buffer_text'] = input_buffer.get_text()
                state_summary['input_buffer_cursor'] = input_buffer.cursor_position
                state_summary['input_buffer_multiline'] = input_buffer.multiline_mode
            else:
                state_summary['input_buffer_text'] = ''
                state_summary['input_buffer_cursor'] = 0
                state_summary['input_buffer_multiline'] = False
        else:
            state_summary['input_buffer_text'] = getattr(state_manager, 'input_buffer', '')
            state_summary['input_buffer_cursor'] = 0
            state_summary['input_buffer_multiline'] = False
        
        # 生成状态哈希
        state_hash = hashlib.md5(json.dumps(state_summary, sort_keys=True, default=str).encode()).hexdigest()
        
        # 检查状态是否真正发生了变化
        if self._last_render_state.get('main_view_state_hash') != state_hash:
            # 更新组件状态
            self._update_components(state_manager)
            
            # 更新各个区域的内容
            self._update_header(state_manager)
            self._update_sidebar()
            self._update_main_content()
            self._update_input_area()
            self._update_workflow_panel()
            self._update_status_bar(state_manager)
            self._update_navigation_bar(state_manager)
            
            # 更新错误反馈面板
            self._update_error_feedback_panel()
            
            # 更新状态哈希
            self._last_render_state['main_view_state_hash'] = state_hash
            
            # 标记需要刷新，因为主界面内容已更新
            self._needs_refresh = True
        self._update_error_feedback_panel()
    
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
        
        # 检查内容是否发生变化
        import hashlib
        content_hash = hashlib.md5(str(header_content).encode()).hexdigest()
        
        if self._last_render_state.get('subview_header_content_hash') != content_hash:
            header_panel = Panel(
                header_content,
                style=self.config.theme.primary_color,
                border_style=self.config.theme.primary_color
            )
            
            self.layout_manager.update_region_content(LayoutRegion.HEADER, header_panel)
            self._last_render_state['subview_header_content_hash'] = content_hash
            self._needs_refresh = True
    
    def _update_components(self, state_manager: Any) -> None:
        """更新组件状态
        
        Args:
            state_manager: 状态管理器
        """
        # 更新所有组件的状态
        if self.sidebar_component:
            self.sidebar_component.update_from_state(state_manager.current_state)
        
        
        if self.main_content_component:
            self.main_content_component.update_from_state(state_manager.current_state)
        
        # 更新子界面数据
        self._update_subviews_data(state_manager)
        
        # 更新工作流控制面板
        if self.workflow_control_panel and state_manager.current_state:
            self.workflow_control_panel.update_from_agent_state(state_manager.current_state)
            
        # 标记需要刷新，因为主界面内容已更新
        self._needs_refresh = True
    
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
            # 检查错误列表是否发生变化
            import hashlib
            import json
            errors_hash = hashlib.md5(json.dumps(errors, sort_keys=True, default=str).encode()).hexdigest()
            if self._last_render_state.get('errors_hash') != errors_hash:
                # 清除旧错误并添加新错误
                self.errors_view.error_list = []  # 直接清空错误列表
                self.errors_view._update_stats()  # 更新统计
                for error in errors:
                    self.errors_view.add_error(error)
                self._last_render_state['errors_hash'] = errors_hash
        
        # 更新状态概览子界面数据
        if self.status_overview_view and state_manager.current_state:
            # 更新会话信息
            session_info = {
                "session_id": getattr(state_manager, 'session_id', ''),
                "workflow_name": getattr(state_manager.current_state, 'workflow_name', ''),
                "status": "运行中" if getattr(state_manager, 'session_id', '') else "未连接",
                "message_count": len(getattr(state_manager, 'message_history', [])),
                "token_count": getattr(state_manager.current_state, 'total_tokens', 0)
            }
            self.status_overview_view.update_session_info(session_info)
            
            # 更新Agent信息
            agent_info = {
                "name": getattr(state_manager.current_state, 'agent_name', ''),
                "model": getattr(state_manager.current_state, 'model_name', ''),
                "status": "运行中" if getattr(state_manager.current_state, 'agent_name', '') else "未运行",
                "tool_count": len(getattr(state_manager.current_state, 'tools', [])),
                "current_task": getattr(state_manager.current_state, 'current_task', '')
            }
            self.status_overview_view.update_agent_info(agent_info)
            
            # 更新工作流状态
            workflow_status = {
                "name": getattr(state_manager.current_state, 'workflow_name', ''),
                "status": "进行中" if getattr(state_manager.current_state, 'is_running', False) else "未启动",
                "progress": getattr(state_manager.current_state, 'progress', 0.0),
                "iteration_count": getattr(state_manager.current_state, 'iteration_count', 0),
                "max_iterations": getattr(state_manager.current_state, 'max_iterations', 10)
            }
            self.status_overview_view.update_workflow_status(workflow_status)
            
            # 更新核心指标
            core_metrics = {
                "message_count": len(getattr(state_manager, 'message_history', [])),
                "token_count": getattr(state_manager.current_state, 'total_tokens', 0),
                "runtime": getattr(state_manager.current_state, 'runtime', 0.0),
                "success_rate": getattr(state_manager.current_state, 'success_rate', 100.0),
                "error_count": len(getattr(state_manager, 'get_errors', lambda: [])())
            }
            self.status_overview_view.update_core_metrics(core_metrics)
            
            # 更新性能监控数据
            performance_monitoring = {
                "cpu_usage": getattr(state_manager.current_state, 'cpu_usage', 0.0),
                "memory_usage": getattr(state_manager.current_state, 'memory_usage', 0.0),
                "response_time": getattr(state_manager.current_state, 'avg_response_time', 0.0),
                "error_rate": 100 - getattr(state_manager.current_state, 'success_rate', 100.0),
                "network_io": getattr(state_manager.current_state, 'network_io', 0.0),
                "disk_usage": getattr(state_manager.current_state, 'disk_usage', 0.0)
            }
            self.status_overview_view.update_performance_monitoring(performance_monitoring)
        
    
    def _update_header(self, state_manager: Any) -> None:
        """更新标题栏
        
        Args:
            state_manager: 状态管理器
        """
        # 创建新的标题内容
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
        
        # 检查内容是否发生变化
        import hashlib
        content_hash = hashlib.md5(str(header_content).encode()).hexdigest()
        
        if self._last_render_state.get('header_content_hash') != content_hash:
            header_panel = Panel(
                header_content,
                style=self.config.theme.primary_color,
                border_style=self.config.theme.primary_color
            )
            
            self.layout_manager.update_region_content(LayoutRegion.HEADER, header_panel)
            self._last_render_state['header_content_hash'] = content_hash
            self._needs_refresh = True
    
    def _update_sidebar(self) -> None:
        """更新侧边栏"""
        if not self.layout_manager.is_region_visible(LayoutRegion.SIDEBAR):
            return
        
        if self.sidebar_component:
            sidebar_panel = self.sidebar_component.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(sidebar_panel).encode() if sidebar_panel else b'').hexdigest()
            
            if self._last_render_state.get('sidebar_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, sidebar_panel)
                self._last_render_state['sidebar_content_hash'] = content_hash
                self._needs_refresh = True
    
    def _update_main_content(self) -> None:
        """更新主内容区"""
        if self.main_content_component:
            main_panel = self.main_content_component.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(main_panel).encode() if main_panel else b'').hexdigest()
            
            if self._last_render_state.get('main_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.MAIN, main_panel)
                self._last_render_state['main_content_hash'] = content_hash
                self._needs_refresh = True
                self.tui_logger.debug_render_operation("main_content", "content_updated", hash=content_hash[:8])
    
    def _update_input_area(self) -> None:
        """更新输入区域"""
        if self.input_component:
            input_panel = self.input_component.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(input_panel).encode() if input_panel else b'').hexdigest()
            
            if self._last_render_state.get('input_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.INPUT, input_panel)
                self._last_render_state['input_content_hash'] = content_hash
                self._needs_refresh = True
                self.tui_logger.debug_render_operation("input_area", "content_updated", hash=content_hash[:8])
    
    def _update_workflow_panel(self) -> None:
        """更新工作流面板"""
        # 优先显示工作流控制面板
        if self.workflow_control_panel:
            workflow_panel = self.workflow_control_panel.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(workflow_panel).encode() if workflow_panel else b'').hexdigest()
            
            if self._last_render_state.get('workflow_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, workflow_panel)
                self._last_render_state['workflow_content_hash'] = content_hash
                self._needs_refresh = True
    
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
        
        # 检查内容是否发生变化
        import hashlib
        content_hash = hashlib.md5(str(status_text).encode()).hexdigest()
        
        if self._last_render_state.get('status_content_hash') != content_hash:
            status_panel = Panel(
                status_text,
                style="dim",
                border_style="dim"
            )
            
            self.layout_manager.update_region_content(LayoutRegion.STATUS, status_panel)
            self._last_render_state['status_content_hash'] = content_hash
            self._needs_refresh = True
    
    def _update_dialogs(self, state_manager: Any) -> None:
        """更新对话框显示
        
        Args:
            state_manager: 状态管理器
        """
        if state_manager.show_session_dialog and self.session_dialog:
            # 显示会话管理对话框，覆盖整个主内容区
            dialog_panel = self.session_dialog.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(dialog_panel).encode() if dialog_panel else b'').hexdigest()
            
            if self._last_render_state.get('dialog_session_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.MAIN, dialog_panel)
                
                # 隐藏其他区域
                self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
                self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
                # 隐藏错误反馈面板
                if self.error_feedback_panel:
                    self.layout_manager.update_region_content(LayoutRegion.STATUS, "")
                
                self._last_render_state['dialog_session_content_hash'] = content_hash
                self._needs_refresh = True
            
        elif state_manager.show_agent_dialog and self.agent_dialog:
            # 显示Agent选择对话框，覆盖整个主内容区
            dialog_panel = self.agent_dialog.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(dialog_panel).encode() if dialog_panel else b'').hexdigest()
            
            if self._last_render_state.get('dialog_agent_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.MAIN, dialog_panel)
                
                # 隐藏其他区域
                self.layout_manager.update_region_content(LayoutRegion.SIDEBAR, "")
                self.layout_manager.update_region_content(LayoutRegion.LANGGRAPH, "")
                
                self._last_render_state['dialog_agent_content_hash'] = content_hash
                self._needs_refresh = True
    
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
        
        # 检查内容是否发生变化
        import hashlib
        content_hash = hashlib.md5(str(welcome_panel).encode() if welcome_panel else b'').hexdigest()
        
        if self._last_render_state.get('welcome_content_hash') != content_hash:
            self.layout_manager.update_region_content(LayoutRegion.MAIN, welcome_panel)
            self._last_render_state['welcome_content_hash'] = content_hash
            # 设置刷新标记而不是立即刷新
            self._needs_refresh = True
    
    def _get_state_hash(self, state_manager: Any) -> str:
        """获取状态管理器的哈希值，用于检测状态变化
        
        Args:
            state_manager: 状态管理器
            
        Returns:
            str: 状态哈希值
        """
        import hashlib
        import json
        
        # 创建状态的表示，包含更多细节以检测变化
        state_repr = {
            'current_subview': state_manager.current_subview,
            'show_session_dialog': getattr(state_manager, 'show_session_dialog', False),
            'show_agent_dialog': getattr(state_manager, 'show_agent_dialog', False),
            'session_id': getattr(state_manager, 'session_id', None),
            'message_history_length': len(getattr(state_manager, 'message_history', [])),
            # 添加最后一条消息的内容哈希，确保新消息被检测到
            'last_message_hash': '',
            'current_state': str(getattr(state_manager, 'current_state', None)),
        }
        
        # 添加最后一条消息的内容哈希
        message_history = getattr(state_manager, 'message_history', [])
        if message_history:
            last_msg = message_history[-1]
            msg_content = f"{last_msg.get('type', '')}:{last_msg.get('content', '')}"
            state_repr['last_message_hash'] = hashlib.md5(msg_content.encode()).hexdigest()
        
        # 添加输入缓冲区状态检测
        if hasattr(self, 'input_component') and self.input_component:
            input_buffer = self.input_component.input_buffer
            if input_buffer:
                input_text = input_buffer.get_text()
                state_repr['input_buffer_text'] = input_text
                state_repr['input_buffer_cursor'] = input_buffer.cursor_position
                state_repr['input_buffer_multiline'] = input_buffer.multiline_mode
        
        # 序列化并生成哈希
        state_str = json.dumps(state_repr, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def _on_layout_changed(self, breakpoint: str, terminal_size: Tuple[int, int]) -> None:
        """布局变化回调处理
        
        Args:
            breakpoint: 新的断点
            terminal_size: 终端尺寸
        """
        # 检查断点或终端尺寸是否真正发生变化
        import hashlib
        layout_state = f"{breakpoint}_{terminal_size[0]}_{terminal_size[1]}"
        layout_hash = hashlib.md5(layout_state.encode()).hexdigest()
        
        if self._last_render_state.get('layout_hash') != layout_hash:
            # 根据新布局调整组件显示
            self._adjust_components_to_layout(breakpoint, terminal_size)
            
            # 更新布局状态哈希
            self._last_render_state['layout_hash'] = layout_hash
            
            # 标记需要刷新，让主循环处理
            self._needs_refresh = True
    
    def _adjust_components_to_layout(self, breakpoint: str, terminal_size: Tuple[int, int]) -> None:
        """根据布局调整组件
        
        Args:
            breakpoint: 当前断点
            terminal_size: 终端尺寸
        """
        # 根据断点调整组件显示策略
        if breakpoint == "small":
            # 小屏幕优化
            self._optimize_for_small_screen()
        elif breakpoint == "medium":
            # 中等屏幕优化
            self._optimize_for_medium_screen()
        else:
            # 大屏幕优化
            self._optimize_for_large_screen()
    
    def _optimize_for_small_screen(self) -> None:
        """小屏幕优化"""
        # 可以在这里添加小屏幕特定的优化逻辑
        # 例如：简化组件显示、减少信息密度等
        pass
    
    def _optimize_for_medium_screen(self) -> None:
        """中等屏幕优化"""
        # 可以在这里添加中等屏幕特定的优化逻辑
        pass
    
    def _optimize_for_large_screen(self) -> None:
        """大屏幕优化"""
        # 可以在这里添加大屏幕特定的优化逻辑
        # 例如：显示更多信息、启用更多功能等
        pass
    
    def _check_error_feedback_panel(self) -> None:
        """检查并显示错误反馈面板"""
        if not self.error_feedback_panel or not self.live:
            return
        
        # 获取错误反馈面板内容
        error_panel = self.error_feedback_panel.render()
        if error_panel:
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(error_panel).encode() if error_panel else b'').hexdigest()
            
            if self._last_render_state.get('error_feedback_content_hash') != content_hash:
                # 将错误面板显示在状态栏位置
                self.layout_manager.update_region_content(LayoutRegion.STATUS, error_panel)
                self._last_render_state['error_feedback_content_hash'] = content_hash
                # 标记需要刷新
                self._needs_refresh = True
    
    def _update_error_feedback_panel(self) -> None:
        """更新错误反馈面板"""
        # 这个方法可以用来定期更新错误反馈面板的状态
        # 目前错误反馈面板是事件驱动的，不需要定期更新
    
    def _update_navigation_bar(self, state_manager: Any) -> None:
        """更新导航栏
        
        Args:
            state_manager: 状态管理器
        """
        if self.navigation_component:
            # 更新导航栏组件状态
            self.navigation_component.update_from_state(state_manager.current_state)
            
            # 渲染导航栏
            navigation_panel = self.navigation_component.render()
            
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(navigation_panel).encode() if navigation_panel else b'').hexdigest()
            
            if self._last_render_state.get('navigation_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.NAVIGATION, navigation_panel)
                self._last_render_state['navigation_content_hash'] = content_hash
                self._needs_refresh = True
        pass
    
    def get_render_stats(self) -> Dict[str, Any]:
        """获取渲染性能统计信息
        
        Returns:
            Dict[str, Any]: 渲染统计信息
        """
        return self._render_stats