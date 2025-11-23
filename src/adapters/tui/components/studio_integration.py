"""TUI-Studio联动组件

包含TUI与LangGraph Studio的双向通信、状态同步和一键跳转功能
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
import asyncio
import json
import webbrowser
from urllib.parse import urljoin

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult

from ..config import TUIConfig


class SyncDirection(Enum):
    """同步方向枚举"""
    TUI_TO_STUDIO = "tui_to_studio"
    STUDIO_TO_TUI = "studio_to_tui"
    BIDIRECTIONAL = "bidirectional"


class IntegrationEvent:
    """集成事件"""
    
    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str,
        timestamp: Optional[datetime] = None
    ):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = timestamp or datetime.now()
        self.processed = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 事件字典
        """
        return {
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed
        }


class StudioIntegrationManager:
    """Studio集成管理器"""
    
    def __init__(self):
        self.studio_url = "http://localhost:8123"
        self.session_id: Optional[str] = None
        self.sync_enabled = False
        self.sync_direction = SyncDirection.BIDIRECTIONAL
        self.events: List[IntegrationEvent] = []
        self.max_events = 1000
        
        # 回调函数
        self.on_sync_event: Optional[Callable[[IntegrationEvent], None]] = None
        self.on_connection_changed: Optional[Callable[[bool], None]] = None
        self.on_jump_to_studio: Optional[Callable[[str, str], None]] = None
    
    def set_sync_event_callback(self, callback: Callable[[IntegrationEvent], None]) -> None:
        """设置同步事件回调
        
        Args:
            callback: 回调函数
        """
        self.on_sync_event = callback
    
    def set_connection_changed_callback(self, callback: Callable[[bool], None]) -> None:
        """设置连接状态变化回调
        
        Args:
            callback: 回调函数
        """
        self.on_connection_changed = callback
    
    def set_jump_to_studio_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置跳转到Studio回调
        
        Args:
            callback: 回调函数
        """
        self.on_jump_to_studio = callback
    
    def set_studio_url(self, url: str) -> None:
        """设置Studio URL
        
        Args:
            url: Studio URL
        """
        self.studio_url = url
    
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID
        
        Args:
            session_id: 会话ID
        """
        self.session_id = session_id
    
    def enable_sync(self, direction: SyncDirection = SyncDirection.BIDIRECTIONAL) -> None:
        """启用同步
        
        Args:
            direction: 同步方向
        """
        self.sync_enabled = True
        self.sync_direction = direction
        
        event = IntegrationEvent(
            "sync_enabled",
            {"direction": direction.value},
            "tui"
        )
        self._add_event(event)
    
    def disable_sync(self) -> None:
        """禁用同步"""
        self.sync_enabled = False
        
        event = IntegrationEvent(
            "sync_disabled",
            {},
            "tui"
        )
        self._add_event(event)
    
    def _add_event(self, event: IntegrationEvent) -> None:
        """添加事件
        
        Args:
            event: 集成事件
        """
        self.events.append(event)
        
        # 限制事件数量
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # 通知回调
        if self.on_sync_event:
            self.on_sync_event(event)
    
    def sync_session_to_studio(self, session_data: Dict[str, Any]) -> None:
        """同步会话到Studio
        
        Args:
            session_data: 会话数据
        """
        if not self.sync_enabled or self.sync_direction == SyncDirection.STUDIO_TO_TUI:
            return
        
        event = IntegrationEvent(
            "session_sync_to_studio",
            {
                "session_id": self.session_id,
                "session_data": session_data
            },
            "tui"
        )
        self._add_event(event)
    
    def sync_session_from_studio(self, session_data: Dict[str, Any]) -> None:
        """从Studio同步会话
        
        Args:
            session_data: 会话数据
        """
        if not self.sync_enabled or self.sync_direction == SyncDirection.TUI_TO_STUDIO:
            return
        
        event = IntegrationEvent(
            "session_sync_from_studio",
            {
                "session_id": self.session_id,
                "session_data": session_data
            },
            "studio"
        )
        self._add_event(event)
    
    def sync_workflow_state(self, workflow_state: Dict[str, Any]) -> None:
        """同步工作流状态
        
        Args:
            workflow_state: 工作流状态
        """
        if not self.sync_enabled:
            return
        
        if self.sync_direction in [SyncDirection.TUI_TO_STUDIO, SyncDirection.BIDIRECTIONAL]:
            # TUI -> Studio
            event = IntegrationEvent(
                "workflow_state_to_studio",
                {
                    "session_id": self.session_id,
                    "workflow_state": workflow_state
                },
                "tui"
            )
            self._add_event(event)
        
        if self.sync_direction in [SyncDirection.STUDIO_TO_TUI, SyncDirection.BIDIRECTIONAL]:
            # Studio -> TUI
            event = IntegrationEvent(
                "workflow_state_from_studio",
                {
                    "session_id": self.session_id,
                    "workflow_state": workflow_state
                },
                "studio"
            )
            self._add_event(event)
    
    def jump_to_studio(self, node_id: str, view_type: str = "graph") -> str:
        """跳转到Studio
        
        Args:
            node_id: 节点ID
            view_type: 视图类型
            
        Returns:
            str: Studio URL
        """
        if not self.session_id:
            return ""
        
        # 构建Studio URL
        studio_url = f"{self.studio_url}/sessions/{self.session_id}"
        
        if node_id:
            studio_url += f"?node={node_id}&view={view_type}"
        
        # 记录跳转事件
        event = IntegrationEvent(
            "jump_to_studio",
            {
                "session_id": self.session_id,
                "node_id": node_id,
                "view_type": view_type,
                "url": studio_url
            },
            "tui"
        )
        self._add_event(event)
        
        # 通知回调
        if self.on_jump_to_studio:
            self.on_jump_to_studio(node_id, studio_url)
        
        return studio_url
    
    def open_studio_in_browser(self, node_id: Optional[str] = None) -> bool:
        """在浏览器中打开Studio
        
        Args:
            node_id: 节点ID
            
        Returns:
            bool: 是否成功打开
        """
        try:
            if node_id:
                url = self.jump_to_studio(node_id)
            else:
                url = f"{self.studio_url}/sessions/{self.session_id}" if self.session_id else self.studio_url
            
            webbrowser.open(url)
            return True
        except Exception:
            return False
    
    def get_recent_events(self, count: int = 20) -> List[IntegrationEvent]:
        """获取最近的事件
        
        Args:
            count: 返回数量
            
        Returns:
            List[IntegrationEvent]: 事件列表
        """
        return self.events[-count:] if self.events else []
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态
        
        Returns:
            Dict[str, Any]: 同步状态
        """
        return {
            "sync_enabled": self.sync_enabled,
            "sync_direction": self.sync_direction.value,
            "studio_url": self.studio_url,
            "session_id": self.session_id,
            "total_events": len(self.events),
            "recent_events": len([e for e in self.events if not e.processed])
        }


class StudioIntegrationPanel:
    """Studio集成面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.integration_manager = StudioIntegrationManager()
        self.show_events = False
        self.auto_sync = True
        
        # 设置回调
        self.integration_manager.set_sync_event_callback(self._on_sync_event)
        self.integration_manager.set_connection_changed_callback(self._on_connection_changed)
        self.integration_manager.set_jump_to_studio_callback(self._on_jump_to_studio)
        
        # 外部回调
        self.on_integration_action: Optional[Callable[[str, Any], None]] = None
    
    def set_integration_action_callback(self, callback: Callable[[str, Any], None]) -> None:
        """设置集成动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_integration_action = callback
    
    def _on_sync_event(self, event: IntegrationEvent) -> None:
        """同步事件处理
        
        Args:
            event: 集成事件
        """
        if self.on_integration_action:
            self.on_integration_action("sync_event", {
                "event_type": event.event_type,
                "source": event.source,
                "data": event.data
            })
    
    def _on_connection_changed(self, connected: bool) -> None:
        """连接状态变化处理
        
        Args:
            connected: 是否连接
        """
        if self.on_integration_action:
            self.on_integration_action("connection_changed", {"connected": connected})
    
    def _on_jump_to_studio(self, node_id: str, url: str) -> None:
        """跳转到Studio处理
        
        Args:
            node_id: 节点ID
            url: Studio URL
        """
        if self.on_integration_action:
            self.on_integration_action("jump_to_studio", {
                "node_id": node_id,
                "url": url
            })
    
    def toggle_events(self) -> None:
        """切换事件显示"""
        self.show_events = not self.show_events
    
    def toggle_auto_sync(self) -> None:
        """切换自动同步"""
        self.auto_sync = not self.auto_sync
    
    def enable_sync(self) -> None:
        """启用同步"""
        self.integration_manager.enable_sync()
    
    def disable_sync(self) -> None:
        """禁用同步"""
        self.integration_manager.disable_sync()
    
    def jump_to_studio(self, node_id: Optional[str] = None) -> bool:
        """跳转到Studio
        
        Args:
            node_id: 节点ID
            
        Returns:
            bool: 是否成功跳转
        """
        return self.integration_manager.open_studio_in_browser(node_id)
    
    def sync_session(self, session_data: Dict[str, Any]) -> None:
        """同步会话
        
        Args:
            session_data: 会话数据
        """
        if self.auto_sync:
            self.integration_manager.sync_session_to_studio(session_data)
    
    def sync_workflow_state(self, workflow_state: Dict[str, Any]) -> None:
        """同步工作流状态
        
        Args:
            workflow_state: 工作流状态
        """
        if self.auto_sync:
            self.integration_manager.sync_workflow_state(workflow_state)
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "e":
            self.toggle_events()
        elif key == "a":
            self.toggle_auto_sync()
        elif key == "s":
            if self.integration_manager.sync_enabled:
                self.disable_sync()
                return "SYNC_DISABLED"
            else:
                self.enable_sync()
                return "SYNC_ENABLED"
        elif key == "j":
            if self.jump_to_studio():
                return "JUMPED_TO_STUDIO"
            else:
                return "JUMP_FAILED"
        elif key == "o":
            if self.jump_to_studio():
                return "OPENED_STUDIO"
            else:
                return "OPEN_STUDIO_FAILED"
        
        return None
    
    def render(self) -> Panel:
        """渲染集成面板
        
        Returns:
            Panel: 集成面板
        """
        if self.show_events:
            content = self._render_events()
        else:
            content = self._render_control_panel()
        
        return Panel(
            content,
            title="Studio集成 (E=事件, A=自动同步, S=同步开关, J=跳转, O=打开)",
            border_style="cyan",
            padding=(1, 1)
        )
    
    def _render_control_panel(self) -> Table:
        """渲染控制面板
        
        Returns:
            Table: 控制面板表格
        """
        table = Table.grid()
        table.add_column()
        
        # 获取同步状态
        status = self.integration_manager.get_sync_status()
        
        # 状态信息
        status_text = Text()
        status_text.append("同步状态: ", style="bold")
        
        if status["sync_enabled"]:
            status_text.append("已启用", style="green")
            status_text.append(f" ({status['sync_direction']})")
        else:
            status_text.append("已禁用", style="red")
        
        status_text.append(f"\\nStudio URL: {status['studio_url']}")
        
        if status["session_id"]:
            status_text.append(f"\\n会话ID: {status['session_id'][:8]}...")
        
        status_text.append(f"\\n事件总数: {status['total_events']}")
        status_text.append(f"\\n自动同步: {'开启' if self.auto_sync else '关闭'}")
        
        table.add_row(status_text)
        
        # 操作说明
        table.add_row("")
        table.add_row("可用操作:")
        table.add_row("  [S] 启用/禁用同步")
        table.add_row("  [A] 切换自动同步")
        table.add_row("  [J] 跳转到Studio")
        table.add_row("  [O] 在浏览器打开Studio")
        table.add_row("  [E] 查看事件日志")
        
        return table
    
    def _render_events(self) -> Table:
        """渲染事件日志
        
        Returns:
            Table: 事件日志表格
        """
        table = Table(
            title="集成事件日志",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("时间", style="dim", width=8)
        table.add_column("来源", style="bold", width=6)
        table.add_column("类型", style="green")
        table.add_column("详情", style="white")
        
        events = self.integration_manager.get_recent_events(20)
        
        for event in reversed(events):  # 最新的在前
            time_str = event.timestamp.strftime("%H:%M:%S")
            source_style = "blue" if event.source == "tui" else "yellow"
            
            # 格式化详情
            if event.event_type == "jump_to_studio":
                details = f"节点: {event.data.get('node_id', 'N/A')}"
            elif event.event_type.startswith("session_sync"):
                details = f"会话: {event.data.get('session_id', 'N/A')[:8]}..."
            elif event.event_type.startswith("workflow_state"):
                details = f"状态同步"
            else:
                details = str(event.data)[:30] + "..." if len(str(event.data)) > 30 else str(event.data)
            
            table.add_row(
                time_str,
                f"[{source_style}]{event.source.upper()}[/{source_style}]",
                event.event_type,
                details
            )
        
        return table