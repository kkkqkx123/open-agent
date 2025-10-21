"""错误提示和反馈系统组件

包含错误显示、用户反馈和系统通知功能
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
import asyncio

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from ..config import TUIConfig


class NotificationType(Enum):
    """通知类型枚举"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    LOADING = "loading"


class Notification:
    """通知消息"""
    
    def __init__(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        title: Optional[str] = None,
        details: Optional[str] = None,
        actions: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ):
        self.message = message
        self.type = notification_type
        self.title = title or self._get_default_title()
        self.details = details
        self.actions = actions or []
        self.timeout = timeout
        self.timestamp = datetime.now()
        self.id = f"{notification_type.value}_{self.timestamp.timestamp()}"
    
    def _get_default_title(self) -> str:
        """获取默认标题
        
        Returns:
            str: 默认标题
        """
        titles = {
            NotificationType.INFO: "信息",
            NotificationType.SUCCESS: "成功",
            NotificationType.WARNING: "警告",
            NotificationType.ERROR: "错误",
            NotificationType.LOADING: "加载中"
        }
        return titles.get(self.type, "通知")
    
    def get_style(self) -> str:
        """获取样式
        
        Returns:
            str: 样式字符串
        """
        styles = {
            NotificationType.INFO: "blue",
            NotificationType.SUCCESS: "green",
            NotificationType.WARNING: "yellow",
            NotificationType.ERROR: "red",
            NotificationType.LOADING: "cyan"
        }
        return styles.get(self.type, "white")
    
    def is_expired(self) -> bool:
        """检查是否过期
        
        Returns:
            bool: 是否过期
        """
        if self.timeout is None:
            return False
        return (datetime.now() - self.timestamp).total_seconds() > self.timeout


class ErrorFeedbackSystem:
    """错误反馈系统"""
    
    def __init__(self, max_notifications: int = 50):
        self.max_notifications = max_notifications
        self.notifications: List[Notification] = []
        self.current_notification: Optional[Notification] = None
        self.show_details = False
        
        # 回调函数
        self.on_action: Optional[Callable[[str, str], None]] = None
        self.on_dismiss: Optional[Callable[[str], None]] = None
    
    def set_action_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置动作回调
        
        Args:
            callback: 回调函数，参数为(notification_id, action)
        """
        self.on_action = callback
    
    def set_dismiss_callback(self, callback: Callable[[str], None]) -> None:
        """设置关闭回调
        
        Args:
            callback: 回调函数，参数为notification_id
        """
        self.on_dismiss = callback
    
    def add_notification(self, notification: Notification) -> None:
        """添加通知
        
        Args:
            notification: 通知对象
        """
        # 移除过期通知
        self._cleanup_expired()
        
        # 如果是错误或重要通知，设为当前通知
        if notification.type in [NotificationType.ERROR, NotificationType.WARNING]:
            self.current_notification = notification
        
        self.notifications.append(notification)
        
        # 限制通知数量
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]
    
    def add_info(self, message: str, title: Optional[str] = None, **kwargs: Any) -> None:
        """添加信息通知
        
        Args:
            message: 消息内容
            title: 标题
            **kwargs: 其他参数
        """
        notification = Notification(
            message=message,
            notification_type=NotificationType.INFO,
            title=title,
            **kwargs
        )
        self.add_notification(notification)
    
    def add_success(self, message: str, title: Optional[str] = None, **kwargs: Any) -> None:
        """添加成功通知
        
        Args:
            message: 消息内容
            title: 标题
            **kwargs: 其他参数
        """
        notification = Notification(
            message=message,
            notification_type=NotificationType.SUCCESS,
            title=title,
            **kwargs
        )
        self.add_notification(notification)
    
    def add_warning(self, message: str, title: Optional[str] = None, **kwargs: Any) -> None:
        """添加警告通知
        
        Args:
            message: 消息内容
            title: 标题
            **kwargs: 其他参数
        """
        notification = Notification(
            message=message,
            notification_type=NotificationType.WARNING,
            title=title,
            timeout=10.0,  # 警告默认10秒超时
            **kwargs
        )
        self.add_notification(notification)
    
    def add_error(self, message: str, title: Optional[str] = None, details: Optional[str] = None, **kwargs: Any) -> None:
        """添加错误通知
        
        Args:
            message: 消息内容
            title: 标题
            details: 详细信息
            **kwargs: 其他参数
        """
        notification = Notification(
            message=message,
            notification_type=NotificationType.ERROR,
            title=title,
            details=details,
            actions=["重试", "忽略", "详情"],
            **kwargs
        )
        self.add_notification(notification)
    
    def add_loading(self, message: str, title: Optional[str] = None, **kwargs: Any) -> None:
        """添加加载通知
        
        Args:
            message: 消息内容
            title: 标题
            **kwargs: 其他参数
        """
        notification = Notification(
            message=message,
            notification_type=NotificationType.LOADING,
            title=title,
            **kwargs
        )
        self.add_notification(notification)
    
    def dismiss_current(self) -> None:
        """关闭当前通知"""
        if self.current_notification:
            if self.on_dismiss:
                self.on_dismiss(self.current_notification.id)
            self.current_notification = None
    
    def handle_action(self, action: str) -> None:
        """处理动作
        
        Args:
            action: 动作名称
        """
        if self.current_notification and self.on_action:
            self.on_action(self.current_notification.id, action)
    
    def toggle_details(self) -> None:
        """切换详情显示"""
        self.show_details = not self.show_details
    
    def get_recent_notifications(self, count: int = 10) -> List[Notification]:
        """获取最近的通知
        
        Args:
            count: 返回数量
            
        Returns:
            List[Notification]: 通知列表
        """
        return self.notifications[-count:] if self.notifications else []
    
    def _cleanup_expired(self) -> None:
        """清理过期通知"""
        self.notifications = [
            n for n in self.notifications 
            if not n.is_expired() or n.type in [NotificationType.ERROR]
        ]
    
    def render_current_notification(self) -> Optional[Panel]:
        """渲染当前通知
        
        Returns:
            Optional[Panel]: 通知面板
        """
        if not self.current_notification:
            return None
        
        notification = self.current_notification
        
        # 创建通知内容
        content = Text()
        content.append(notification.message, style=notification.get_style())
        
        # 添加详情
        if self.show_details and notification.details:
            content.append("\\n\\n详细信息:\\n", style="dim")
            content.append(notification.details, style="dim")
        
        # 添加动作按钮
        if notification.actions:
            content.append("\\n\\n可用操作: ", style="bold")
            for i, action in enumerate(notification.actions):
                if i > 0:
                    content.append(" | ")
                content.append(f"[{action}]", style="cyan")
        
        # 添加时间戳
        time_str = notification.timestamp.strftime("%H:%M:%S")
        content.append(f"\\n\\n时间: {time_str}", style="dim")
        
        return Panel(
            content,
            title=notification.title,
            border_style=notification.get_style(),
            padding=(1, 1)
        )
    
    def render_notification_list(self) -> Optional[Table]:
        """渲染通知列表
        
        Returns:
            Optional[Table]: 通知列表表格
        """
        if not self.notifications:
            return None
        
        table = Table(
            title="通知历史",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("时间", style="dim", width=8)
        table.add_column("类型", style="bold", width=6)
        table.add_column("消息", style="white")
        
        for notification in self.notifications[-10:]:  # 显示最近10条
            time_str = notification.timestamp.strftime("%H:%M:%S")
            type_text = notification.type.value.upper()
            type_style = notification.get_style()
            
            # 截断长消息
            message = notification.message[:40] + "..." if len(notification.message) > 40 else notification.message
            
            table.add_row(
                time_str,
                f"[{type_style}]{type_text}[/{type_style}]",
                message
            )
        
        return table


class LoadingIndicator:
    """加载指示器"""
    
    def __init__(self) -> None:
        self.is_loading = False
        self.message = "加载中..."
        self.progress = 0.0
        self.total = 100.0
    
    def start(self, message: str = "加载中...") -> None:
        """开始加载
        
        Args:
            message: 加载消息
        """
        self.is_loading = True
        self.message = message
        self.progress = 0.0
    
    def update(self, progress: float, message: Optional[str] = None) -> None:
        """更新进度
        
        Args:
            progress: 进度值 (0-100)
            message: 新消息
        """
        self.progress = min(max(progress, 0.0), 100.0)
        if message:
            self.message = message
    
    def finish(self, message: str = "完成") -> None:
        """完成加载
        
        Args:
            message: 完成消息
        """
        self.progress = 100.0
        self.message = message
        self.is_loading = False
    
    def render(self) -> Optional[Panel]:
        """渲染加载指示器
        
        Returns:
            Optional[Panel]: 加载面板
        """
        if not self.is_loading:
            return None
        
        # 创建进度条
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        progress.add_task(self.message, completed=int(self.progress), total=int(self.total))
        
        return Panel(
            progress,
            title="系统状态",
            border_style="cyan",
            padding=(1, 1)
        )


class ErrorFeedbackPanel:
    """错误反馈面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.feedback_system = ErrorFeedbackSystem()
        self.loading_indicator = LoadingIndicator()
        self.show_history = False
        
        # 设置回调
        self.feedback_system.set_action_callback(self._on_action)
        self.feedback_system.set_dismiss_callback(self._on_dismiss)
        
        # 外部回调
        self.on_user_action: Optional[Callable[[str, str], None]] = None
    
    def set_user_action_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置用户动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_user_action = callback
    
    def _on_action(self, notification_id: str, action: str) -> None:
        """处理动作
        
        Args:
            notification_id: 通知ID
            action: 动作名称
        """
        if self.on_user_action:
            self.on_user_action(notification_id, action)
    
    def _on_dismiss(self, notification_id: str) -> None:
        """处理关闭
        
        Args:
            notification_id: 通知ID
        """
        # 可以添加关闭后的处理逻辑
        pass
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "escape":
            self.feedback_system.dismiss_current()
        elif key == "d":
            self.feedback_system.toggle_details()
        elif key == "h":
            self.show_history = not self.show_history
        elif key == "1":
            self.feedback_system.handle_action("重试")
        elif key == "2":
            self.feedback_system.handle_action("忽略")
        elif key == "3":
            self.feedback_system.handle_action("详情")
        
        return None
    
    def start_loading(self, message: str = "加载中...") -> None:
        """开始加载
        
        Args:
            message: 加载消息
        """
        self.loading_indicator.start(message)
    
    def update_loading(self, progress: float, message: Optional[str] = None) -> None:
        """更新加载进度
        
        Args:
            progress: 进度值
            message: 消息
        """
        self.loading_indicator.update(progress, message)
    
    def finish_loading(self, message: str = "完成") -> None:
        """完成加载
        
        Args:
            message: 完成消息
        """
        self.loading_indicator.finish(message)
    
    def add_info(self, message: str, **kwargs: Any) -> None:
        """添加信息通知"""
        self.feedback_system.add_info(message, **kwargs)
    
    def add_success(self, message: str, **kwargs: Any) -> None:
        """添加成功通知"""
        self.feedback_system.add_success(message, **kwargs)
    
    def add_warning(self, message: str, **kwargs: Any) -> None:
        """添加警告通知"""
        self.feedback_system.add_warning(message, **kwargs)
    
    def add_error(self, message: str, **kwargs: Any) -> None:
        """添加错误通知"""
        self.feedback_system.add_error(message, **kwargs)
    
    def render(self) -> Optional[Panel]:
        """渲染反馈面板
        
        Returns:
            Optional[Panel]: 反馈面板
        """
        # 优先显示加载指示器
        loading_panel = self.loading_indicator.render()
        if loading_panel:
            return loading_panel
        
        # 显示当前通知
        if self.show_history:
            # 显示通知历史
            history_table = self.feedback_system.render_notification_list()
            if history_table:
                return Panel(
                    history_table,
                    title="通知历史 (H=返回, Esc=关闭)",
                    border_style="blue"
                )
        else:
            # 显示当前通知
            current_panel = self.feedback_system.render_current_notification()
            if current_panel:
                title = "系统通知 (D=详情, H=历史, Esc=关闭)"
                if self.feedback_system.current_notification and self.feedback_system.current_notification.actions:
                    title += " (1/2/3=操作)"
                
                return Panel(
                    current_panel,
                    title=title,
                    border_style="blue"
                )
        
        return None