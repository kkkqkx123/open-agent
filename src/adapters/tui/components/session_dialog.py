"""会话管理对话框组件

包含会话创建、选择、切换和管理功能
"""

from typing import Optional, Dict, Any, List, Callable, cast, Union
from datetime import datetime
from pathlib import Path

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.prompt import Prompt, Confirm

from ..config import TUIConfig
from src.interfaces.sessions.base import ISessionManager
from src.interfaces.sessions.service import ISessionService


class SessionListComponent:
    """会话列表组件"""
    
    def __init__(self) -> None:
        self.sessions: List[Dict[str, Any]] = []
        self.selected_index = 0
        self.sort_by = "created_at"  # created_at, name, status
        self.sort_order = "desc"  # asc, desc
    
    def update_sessions(self, sessions: List[Dict[str, Any]]) -> None:
        """更新会话列表
        
        Args:
            sessions: 会话列表
        """
        self.sessions = sessions
        self._sort_sessions()
    
    def _sort_sessions(self) -> None:
        """排序会话列表"""
        if self.sort_by == "created_at":
            self.sessions.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=(self.sort_order == "desc")
            )
        elif self.sort_by == "name":
            self.sessions.sort(
                key=lambda x: x.get("workflow_config_path", ""),
                reverse=(self.sort_order == "desc")
            )
        elif self.sort_by == "status":
            self.sessions.sort(
                key=lambda x: x.get("status", ""),
                reverse=(self.sort_order == "desc")
            )
    
    def navigate_up(self) -> None:
        """向上导航"""
        if self.selected_index > 0:
            self.selected_index -= 1
    
    def navigate_down(self) -> None:
        """向下导航"""
        if self.selected_index < len(self.sessions) - 1:
            self.selected_index += 1
    
    def get_selected_session(self) -> Optional[Dict[str, Any]]:
        """获取选中的会话
        
        Returns:
            Optional[Dict[str, Any]]: 选中的会话信息
        """
        if 0 <= self.selected_index < len(self.sessions):
            return cast(Dict[str, Any], self.sessions[self.selected_index])
        return None
    
    def render(self) -> Table:
        """渲染会话列表
        
        Returns:
            Table: 会话列表表格
        """
        table = Table(
            title="会话列表",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        # 添加列
        table.add_column("ID", style="dim", width=8)
        table.add_column("工作流", style="green")
        table.add_column("状态", style="yellow", width=8)
        table.add_column("创建时间", style="white", width=16)
        table.add_column("更新时间", style="white", width=16)
        
        # 添加行
        for i, session in enumerate(self.sessions):
            session_id = session.get("session_id", "")
            workflow_path = session.get("workflow_config_path", "")
            status = session.get("status", "unknown")
            created_at = session.get("created_at", "")
            updated_at = session.get("updated_at", "")
            
            # 格式化时间
            try:
                created_dt = datetime.fromisoformat(created_at) if created_at else None
                updated_dt = datetime.fromisoformat(updated_at) if updated_at else None
                created_str = created_dt.strftime("%Y-%m-%d %H:%M") if created_dt else ""
                updated_str = updated_dt.strftime("%Y-%m-%d %H:%M") if updated_dt else ""
            except (ValueError, TypeError):
                created_str = created_at[:16] if created_at else ""
                updated_str = updated_at[:16] if updated_at else ""
            
            # 状态样式
            status_style = self._get_status_style(status)
            
            # 选中行高亮
            row_style = "bold reverse" if i == self.selected_index else ""
            
            table.add_row(
                session_id[:8] + "...",
                workflow_path.split('/')[-1] if '/' in workflow_path else workflow_path,
                f"[{status_style}]{status}[/{status_style}]",
                created_str,
                updated_str,
                style=row_style
            )
        
        return table
    
    def _get_status_style(self, status: str) -> str:
        """获取状态样式
        
        Args:
            status: 状态字符串
            
        Returns:
            str: 样式字符串
        """
        status_styles = {
            "active": "green",
            "paused": "yellow",
            "completed": "blue",
            "error": "red",
            "deleted": "dim"
        }
        return status_styles.get(status, "white")


class SessionCreateDialog:
    """会话创建对话框"""
    
    def __init__(self) -> None:
        self.workflow_configs: List[str] = []
        self.agent_configs: List[str] = []
        self.selected_workflow = 0
        self.selected_agent = 0
        self.session_name = ""
    
    def update_config_lists(self, workflow_configs: List[str], agent_configs: List[str]) -> None:
        """更新配置列表
        
        Args:
            workflow_configs: 工作流配置列表
            agent_configs: Agent配置列表
        """
        self.workflow_configs = workflow_configs
        self.agent_configs = agent_configs
    
    def navigate_workflow_up(self) -> None:
        """向上选择工作流"""
        if self.selected_workflow > 0:
            self.selected_workflow -= 1
    
    def navigate_workflow_down(self) -> None:
        """向下选择工作流"""
        if self.selected_workflow < len(self.workflow_configs) - 1:
            self.selected_workflow += 1
    
    def navigate_agent_up(self) -> None:
        """向上选择Agent"""
        if self.selected_agent > 0:
            self.selected_agent -= 1
    
    def navigate_agent_down(self) -> None:
        """向下选择Agent"""
        if self.selected_agent < len(self.agent_configs) - 1:
            self.selected_agent += 1
    
    def get_selected_workflow(self) -> Optional[str]:
        """获取选中的工作流配置
        
        Returns:
            Optional[str]: 工作流配置路径
        """
        if 0 <= self.selected_workflow < len(self.workflow_configs):
            return cast(str, self.workflow_configs[self.selected_workflow])
        return None
    
    def get_selected_agent(self) -> Optional[str]:
        """获取选中的Agent配置
        
        Returns:
            Optional[str]: Agent配置路径
        """
        if 0 <= self.selected_agent < len(self.agent_configs):
            return cast(str, self.agent_configs[self.selected_agent])
        return None
    
    def render(self) -> Panel:
        """渲染创建对话框
        
        Returns:
            Panel: 创建对话框面板
        """
        # 创建工作流选择表格
        workflow_table = Table(
            title="选择工作流配置",
            show_header=False,
            border_style="green"
        )
        workflow_table.add_column("配置", style="green")
        
        for i, config in enumerate(self.workflow_configs):
            style = "bold reverse" if i == self.selected_workflow else ""
            workflow_table.add_row(config, style=style)
        
        # 创建Agent选择表格
        agent_table = Table(
            title="选择Agent配置",
            show_header=False,
            border_style="cyan"
        )
        agent_table.add_column("配置", style="cyan")
        
        for i, config in enumerate(self.agent_configs):
            style = "bold reverse" if i == self.selected_agent else ""
            agent_table.add_row(config, style=style)
        
        # 组合内容
        content = Columns([workflow_table, agent_table], equal=True)
        
        return Panel(
            content,
            title="创建新会话",
            border_style="blue",
            padding=(1, 1)
        )


class SessionManagerDialog:
    """会话管理器对话框
    
    包含会话列表、创建、删除、切换等功能
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.session_manager: Optional[Union[ISessionManager, ISessionService]] = None
        self.current_mode = "list"  # list, create, confirm_delete
        self.session_list = SessionListComponent()
        self.create_dialog = SessionCreateDialog()
        self.delete_target: Optional[Dict[str, Any]] = None
        
        # 回调函数
        self.on_session_selected: Optional[Callable[[str], None]] = None
        self.on_session_created: Optional[Callable[[str, Optional[str]], None]] = None
        self.on_session_deleted: Optional[Callable[[str], None]] = None
    
    def set_session_manager(self, session_manager: Union[ISessionManager, ISessionService]) -> None:
        """设置会话管理器
        
        Args:
            session_manager: 会话管理器或会话服务
        """
        self.session_manager = session_manager
    
    def set_session_selected_callback(self, callback: Callable[[str], None]) -> None:
        """设置会话选择回调
        
        Args:
            callback: 回调函数
        """
        self.on_session_selected = callback
    
    def set_session_created_callback(self, callback: Callable[[str, Optional[str]], None]) -> None:
        """设置会话创建回调
        
        Args:
            callback: 回调函数
        """
        self.on_session_created = callback
    
    def set_session_deleted_callback(self, callback: Callable[[str], None]) -> None:
        """设置会话删除回调
        
        Args:
            callback: 回调函数
        """
        self.on_session_deleted = callback
    
    def refresh_sessions(self) -> None:
        """刷新会话列表"""
        if self.session_manager:
            import asyncio
            sessions = asyncio.run(self.session_manager.list_sessions())
            self.session_list.update_sessions(sessions)
    
    def switch_to_list_mode(self) -> None:
        """切换到列表模式"""
        self.current_mode = "list"
        self.refresh_sessions()
    
    def switch_to_create_mode(self) -> None:
        """切换到创建模式"""
        self.current_mode = "create"
        # 这里应该加载可用的配置列表
        # 暂时使用模拟数据
        workflow_configs = [
            "configs/workflows/react.yaml",
            "configs/workflows/plan_execute.yaml",
            "configs/workflows/collaborative.yaml"
        ]
        agent_configs = [
            "configs/agents/default.yaml",
            "configs/agents/advanced.yaml"
        ]
        self.create_dialog.update_config_lists(workflow_configs, agent_configs)
    
    def switch_to_delete_mode(self, session: Dict[str, Any]) -> None:
        """切换到删除确认模式"""
        self.current_mode = "confirm_delete"
        self.delete_target = session
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if self.current_mode == "list":
            return self._handle_list_mode_key(key)
        elif self.current_mode == "create":
            return self._handle_create_mode_key(key)
        elif self.current_mode == "confirm_delete":
            return self._handle_delete_mode_key(key)
        
        return None
    
    def _handle_list_mode_key(self, key: str) -> Optional[str]:
        """处理列表模式按键"""
        if key == "up":
            self.session_list.navigate_up()
        elif key == "down":
            self.session_list.navigate_down()
        elif key == "enter":
            selected = self.session_list.get_selected_session()
            if selected and self.on_session_selected:
                self.on_session_selected(selected["session_id"])
                return "SESSION_SELECTED"
        elif key == "s":  # 快速切换会话
            selected = self.session_list.get_selected_session()
            if selected:
                if self.on_session_selected:
                    self.on_session_selected(selected["session_id"])
                return "SESSION_SWITCHED"
        elif key == "c":  # 创建新会话
            self.switch_to_create_mode()
        elif key == "n":
            self.switch_to_create_mode()
        elif key == "d":
            selected = self.session_list.get_selected_session()
            if selected:
                self.switch_to_delete_mode(selected)
        elif key == "r":
            self.refresh_sessions()
        elif key == "escape":
            return "CLOSE_DIALOG"
        
        return None
    
    def _handle_create_mode_key(self, key: str) -> Optional[str]:
        """处理创建模式按键"""
        if key == "up":
            self.create_dialog.navigate_workflow_up()
        elif key == "down":
            self.create_dialog.navigate_workflow_down()
        elif key == "left":
            self.create_dialog.navigate_agent_up()
        elif key == "right":
            self.create_dialog.navigate_agent_down()
        elif key == "enter":
            workflow_config = self.create_dialog.get_selected_workflow()
            agent_config = self.create_dialog.get_selected_agent()
            if workflow_config and self.on_session_created:
                self.on_session_created(workflow_config, agent_config)
                return "SESSION_CREATED"
        elif key == "escape":
            self.switch_to_list_mode()
        
        return None
    
    def _handle_delete_mode_key(self, key: str) -> Optional[str]:
        """处理删除模式按键"""
        if key == "y":
            if self.delete_target and self.on_session_deleted:
                session_id = self.delete_target["session_id"]
                self.on_session_deleted(session_id)
                self.switch_to_list_mode()
                return "SESSION_DELETED"
        elif key == "n" or key == "escape":
            self.switch_to_list_mode()
        
        return None
    
    def render(self) -> Panel:
        """渲染对话框
        
        Returns:
            Panel: 对话框面板
        """
        # 声明 content 变量的类型，可以是 Table、Panel 或 Text
        content: Union[Table, Panel, Text]
        
        if self.current_mode == "list":
            content = self.session_list.render()
            title = "会话管理 (Enter=选择, S=切换, N=新建, D=删除, R=刷新, Esc=关闭)"
        elif self.current_mode == "create":
            content = self.create_dialog.render()
            title = "创建新会话 (方向键=选择, Enter=创建, Esc=取消)"
        elif self.current_mode == "confirm_delete":
            if self.delete_target:
                session_id = self.delete_target["session_id"]
                workflow = self.delete_target.get("workflow_config_path", "未知")
                content = Text(
                    f"确定要删除会话 {session_id[:8]}... 吗？\\n"
                    f"工作流: {workflow}\\n\\n"
                    f"按 Y 确认，按 N 取消",
                    style="yellow"
                )
                title = "确认删除"
            else:
                content = Text("无会话可删除", style="red")
                title = "错误"
        else:
            content = Text("未知模式", style="red")
            title = "错误"
        
        return Panel(
            content,
            title=title,
            border_style="blue",
            padding=(1, 1)
        )