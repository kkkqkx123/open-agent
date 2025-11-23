"""历史回放功能组件

包含会话历史记录、回放控制和状态恢复功能
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout

from ..config import TUIConfig


class ReplayState(Enum):
    """回放状态枚举"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    SEEKING = "seeking"


class HistoryEvent:
    """历史事件"""
    
    def __init__(
        self,
        timestamp: datetime,
        event_type: str,
        data: Dict[str, Any],
        session_id: str
    ):
        self.timestamp = timestamp
        self.event_type = event_type
        self.data = data
        self.session_id = session_id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 事件字典
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "data": self.data,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEvent":
        """从字典创建事件
        
        Args:
            data: 事件字典
            
        Returns:
            HistoryEvent: 历史事件
        """
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            data=data["data"],
            session_id=data["session_id"]
        )


class SessionHistory:
    """会话历史"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[HistoryEvent] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """添加事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = HistoryEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            data=data,
            session_id=self.session_id
        )
        self.events.append(event)
        self.updated_at = datetime.now()
    
    def get_events_by_type(self, event_type: str) -> List[HistoryEvent]:
        """根据类型获取事件
        
        Args:
            event_type: 事件类型
            
        Returns:
            List[HistoryEvent]: 事件列表
        """
        return [event for event in self.events if event.event_type == event_type]
    
    def get_events_in_range(self, start_time: datetime, end_time: datetime) -> List[HistoryEvent]:
        """获取时间范围内的事件
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[HistoryEvent]: 事件列表
        """
        return [
            event for event in self.events
            if start_time <= event.timestamp <= end_time
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 历史字典
        """
        return {
            "session_id": self.session_id,
            "events": [event.to_dict() for event in self.events],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionHistory":
        """从字典创建历史
        
        Args:
            data: 历史字典
            
        Returns:
            SessionHistory: 会话历史
        """
        history = cls(data["session_id"])
        history.metadata = data.get("metadata", {})
        history.created_at = datetime.fromisoformat(data["created_at"])
        history.updated_at = datetime.fromisoformat(data["updated_at"])
        
        for event_data in data.get("events", []):
            event = HistoryEvent.from_dict(event_data)
            history.events.append(event)
        
        return history


class HistoryReplayManager:
    """历史回放管理器"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./history")
        self.histories: Dict[str, SessionHistory] = {}
        self.current_history: Optional[SessionHistory] = None
        self.replay_state = ReplayState.STOPPED
        self.current_event_index = 0
        self.replay_speed = 1.0  # 回放速度倍数
        
        # 回调函数
        self.on_event_replayed: Optional[Callable[[HistoryEvent], None]] = None
        self.on_replay_state_changed: Optional[Callable[[ReplayState], None]] = None
        self.on_history_loaded: Optional[Callable[[str], None]] = None
    
    def set_event_replayed_callback(self, callback: Callable[[HistoryEvent], None]) -> None:
        """设置事件回放回调
        
        Args:
            callback: 回调函数
        """
        self.on_event_replayed = callback
    
    def set_replay_state_changed_callback(self, callback: Callable[[ReplayState], None]) -> None:
        """设置回放状态变化回调
        
        Args:
            callback: 回调函数
        """
        self.on_replay_state_changed = callback
    
    def set_history_loaded_callback(self, callback: Callable[[str], None]) -> None:
        """设置历史加载回调
        
        Args:
            callback: 回调函数
        """
        self.on_history_loaded = callback
    
    def _set_replay_state(self, state: ReplayState) -> None:
        """设置回放状态
        
        Args:
            state: 新状态
        """
        self.replay_state = state
        if self.on_replay_state_changed:
            self.on_replay_state_changed(state)
    
    def save_history(self, history: SessionHistory) -> bool:
        """保存历史
        
        Args:
            history: 会话历史
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 确保存储目录存在
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # 保存到文件
            file_path = self.storage_path / f"{history.session_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history.to_dict(), f, indent=2, ensure_ascii=False)
            
            # 更新内存中的历史
            self.histories[history.session_id] = history
            
            return True
        except Exception:
            return False
    
    def load_history(self, session_id: str) -> Optional[SessionHistory]:
        """加载历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[SessionHistory]: 会话历史
        """
        if session_id in self.histories:
            return self.histories[session_id]
        
        try:
            file_path = self.storage_path / f"{session_id}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                history = SessionHistory.from_dict(data)
                self.histories[session_id] = history
                
                if self.on_history_loaded:
                    self.on_history_loaded(session_id)
                
                return history
        except Exception:
            pass
        
        return None
    
    def list_histories(self) -> List[Dict[str, Any]]:
        """列出所有历史
        
        Returns:
            List[Dict[str, Any]]: 历史列表
        """
        histories = []
        
        # 扫描存储目录
        if self.storage_path.exists():
            for file_path in self.storage_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    histories.append({
                        "session_id": data["session_id"],
                        "event_count": len(data.get("events", [])),
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "metadata": data.get("metadata", {})
                    })
                except Exception:
                    continue
        
        # 按更新时间排序
        histories.sort(key=lambda x: x["updated_at"], reverse=True)
        return histories
    
    def delete_history(self, session_id: str) -> bool:
        """删除历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 删除文件
            file_path = self.storage_path / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            # 从内存中删除
            self.histories.pop(session_id, None)
            
            # 如果是当前历史，重置
            if self.current_history and self.current_history.session_id == session_id:
                self.current_history = None
                self._set_replay_state(ReplayState.STOPPED)
                self.current_event_index = 0
            
            return True
        except Exception:
            return False
    
    def start_replay(self, session_id: str) -> bool:
        """开始回放
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功开始
        """
        history = self.load_history(session_id)
        if not history or not history.events:
            return False
        
        self.current_history = history
        self.current_event_index = 0
        self._set_replay_state(ReplayState.PLAYING)
        
        return True
    
    def pause_replay(self) -> None:
        """暂停回放"""
        if self.replay_state == ReplayState.PLAYING:
            self._set_replay_state(ReplayState.PAUSED)
    
    def resume_replay(self) -> None:
        """恢复回放"""
        if self.replay_state == ReplayState.PAUSED:
            self._set_replay_state(ReplayState.PLAYING)
    
    def stop_replay(self) -> None:
        """停止回放"""
        self._set_replay_state(ReplayState.STOPPED)
        self.current_event_index = 0
    
    def seek_to_event(self, event_index: int) -> bool:
        """跳转到指定事件
        
        Args:
            event_index: 事件索引
            
        Returns:
            bool: 是否成功跳转
        """
        if not self.current_history or event_index < 0 or event_index >= len(self.current_history.events):
            return False
        
        old_state = self.replay_state
        self._set_replay_state(ReplayState.SEEKING)
        self.current_event_index = event_index
        
        # 回放指定事件
        event = self.current_history.events[event_index]
        if self.on_event_replayed:
            self.on_event_replayed(event)
        
        self._set_replay_state(old_state)
        return True
    
    def next_event(self) -> bool:
        """下一个事件
        
        Returns:
            bool: 是否有下一个事件
        """
        if not self.current_history or self.current_event_index >= len(self.current_history.events):
            return False
        
        event = self.current_history.events[self.current_event_index]
        if self.on_event_replayed:
            self.on_event_replayed(event)
        
        self.current_event_index += 1
        
        # 检查是否回放完成
        if self.current_event_index >= len(self.current_history.events):
            self._set_replay_state(ReplayState.STOPPED)
        
        return True
    
    def previous_event(self) -> bool:
        """上一个事件
        
        Returns:
            bool: 是否有上一个事件
        """
        if not self.current_history or self.current_event_index <= 0:
            return False
        
        self.current_event_index -= 1
        event = self.current_history.events[self.current_event_index]
        
        if self.on_event_replayed:
            self.on_event_replayed(event)
        
        return True
    
    def set_replay_speed(self, speed: float) -> None:
        """设置回放速度
        
        Args:
            speed: 回放速度倍数
        """
        self.replay_speed = max(0.1, min(10.0, speed))
    
    def get_replay_progress(self) -> Dict[str, Any]:
        """获取回放进度
        
        Returns:
            Dict[str, Any]: 进度信息
        """
        if not self.current_history:
            return {
                "total_events": 0,
                "current_event": 0,
                "progress_percentage": 0.0,
                "state": self.replay_state.value
            }
        
        total_events = len(self.current_history.events)
        progress_percentage = (self.current_event_index / total_events * 100) if total_events > 0 else 0
        
        return {
            "total_events": total_events,
            "current_event": self.current_event_index,
            "progress_percentage": progress_percentage,
            "state": self.replay_state.value,
            "speed": self.replay_speed
        }


class HistoryReplayPanel:
    """历史回放面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.replay_manager = HistoryReplayManager()
        self.show_history_list = False
        self.selected_history: Optional[str] = None
        
        # 设置回调
        self.replay_manager.set_replay_state_changed_callback(self._on_replay_state_changed)
        self.replay_manager.set_history_loaded_callback(self._on_history_loaded)
        
        # 外部回调
        self.on_replay_action: Optional[Callable[[str, Any], None]] = None
    
    def set_replay_action_callback(self, callback: Callable[[str, Any], None]) -> None:
        """设置回放动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_replay_action = callback
    
    def _on_replay_state_changed(self, state: ReplayState) -> None:
        """回放状态变化处理
        
        Args:
            state: 新状态
        """
        if self.on_replay_action:
            self.on_replay_action("state_changed", {"state": state.value})
    
    def _on_history_loaded(self, session_id: str) -> None:
        """历史加载处理
        
        Args:
            session_id: 会话ID
        """
        if self.on_replay_action:
            self.on_replay_action("history_loaded", {"session_id": session_id})
    
    def toggle_history_list(self) -> None:
        """切换历史列表显示"""
        self.show_history_list = not self.show_history_list
    
    def select_history(self, session_id: str) -> None:
        """选择历史
        
        Args:
            session_id: 会话ID
        """
        self.selected_history = session_id
    
    def start_replay(self) -> bool:
        """开始回放
        
        Returns:
            bool: 是否成功开始
        """
        if self.selected_history:
            return self.replay_manager.start_replay(self.selected_history)
        return False
    
    def pause_replay(self) -> None:
        """暂停回放"""
        self.replay_manager.pause_replay()
    
    def resume_replay(self) -> None:
        """恢复回放"""
        self.replay_manager.resume_replay()
    
    def stop_replay(self) -> None:
        """停止回放"""
        self.replay_manager.stop_replay()
    
    def next_event(self) -> bool:
        """下一个事件
        
        Returns:
            bool: 是否有下一个事件
        """
        return self.replay_manager.next_event()
    
    def previous_event(self) -> bool:
        """上一个事件
        
        Returns:
            bool: 是否有上一个事件
        """
        return self.replay_manager.previous_event()
    
    def set_replay_speed(self, speed: float) -> None:
        """设置回放速度
        
        Args:
            speed: 回放速度
        """
        self.replay_manager.set_replay_speed(speed)
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "l":
            self.toggle_history_list()
        elif key == "space":
            if self.replay_manager.replay_state == ReplayState.PLAYING:
                self.pause_replay()
                return "REPLAY_PAUSED"
            else:
                if self.replay_manager.replay_state == ReplayState.PAUSED:
                    self.resume_replay()
                    return "REPLAY_RESUMED"
                else:
                    if self.start_replay():
                        return "REPLAY_STARTED"
        elif key == "s":
            self.stop_replay()
            return "REPLAY_STOPPED"
        elif key == "right":
            if self.next_event():
                return "NEXT_EVENT"
        elif key == "left":
            if self.previous_event():
                return "PREVIOUS_EVENT"
        elif key == "up":
            self.set_replay_speed(self.replay_manager.replay_speed + 0.5)
            return f"SPEED_CHANGED:{self.replay_manager.replay_speed}"
        elif key == "down":
            self.set_replay_speed(self.replay_manager.replay_speed - 0.5)
            return f"SPEED_CHANGED:{self.replay_manager.replay_speed}"
        
        return None
    
    def render(self) -> Panel:
        """渲染回放面板
        
        Returns:
            Panel: 回放面板
        """
        if self.show_history_list:
            content = self._render_history_list()
        else:
            content = self._render_replay_control()
        
        return Panel(
            content,
            title="历史回放 (L=列表, Space=播放/暂停, S=停止, ←→=事件, ↑↓=速度)",
            border_style="blue",
            padding=(1, 1)
        )
    
    def _render_history_list(self) -> Table:
        """渲染历史列表
        
        Returns:
            Table: 历史列表表格
        """
        table = Table(
            title="会话历史列表",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("会话ID", style="bold")
        table.add_column("事件数", style="green")
        table.add_column("创建时间", style="white")
        table.add_column("更新时间", style="white")
        
        histories = self.replay_manager.list_histories()
        
        for history in histories:
            session_id = history["session_id"]
            session_display = session_id[:8] + "..."
            
            # 格式化时间
            try:
                created_dt = datetime.fromisoformat(history["created_at"])
                updated_dt = datetime.fromisoformat(history["updated_at"])
                created_str = created_dt.strftime("%m-%d %H:%M")
                updated_str = updated_dt.strftime("%m-%d %H:%M")
            except (ValueError, TypeError):
                created_str = history["created_at"][:16] if history["created_at"] else ""
                updated_str = history["updated_at"][:16] if history["updated_at"] else ""
            
            # 高亮选中的历史
            row_style = "bold reverse" if session_id == self.selected_history else ""
            
            table.add_row(
                session_display,
                str(history["event_count"]),
                created_str,
                updated_str,
                style=row_style
            )
        
        return table
    
    def _render_replay_control(self) -> Table:
        """渲染回放控制
        
        Returns:
            Table: 回放控制表格
        """
        table = Table.grid()
        table.add_column()
        
        # 获取回放进度
        progress = self.replay_manager.get_replay_progress()
        
        # 状态信息
        status_text = Text()
        status_text.append("回放状态: ", style="bold")
        
        state_styles = {
            ReplayState.STOPPED.value: "red",
            ReplayState.PLAYING.value: "green",
            ReplayState.PAUSED.value: "yellow",
            ReplayState.SEEKING.value: "blue"
        }
        
        state_style = state_styles.get(progress["state"], "white")
        status_text.append(progress["state"].upper(), style=state_style)
        
        if self.selected_history:
            status_text.append(f"\\n会话: {self.selected_history[:8]}...")
        
        status_text.append(f"\\n事件: {progress['current_event']}/{progress['total_events']}")
        status_text.append(f"\\n进度: {progress['progress_percentage']:.1f}%")
        status_text.append(f"\\n速度: {progress['speed']:.1f}x")
        
        table.add_row(status_text)
        
        # 进度条
        if progress["total_events"] > 0:
            progress_bar = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            )
            progress_bar.add_task(
                "回放进度",
                completed=progress["current_event"],
                total=progress["total_events"]
            )
            table.add_row("")
            table.add_row(progress_bar)
        
        return table