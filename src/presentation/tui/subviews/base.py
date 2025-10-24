"""子界面基类"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree

from ..config import TUIConfig


class BaseSubview(ABC):
    """子界面基类"""
    
    def __init__(self, config: TUIConfig):
        """初始化子界面
        
        Args:
            config: TUI配置
        """
        self.config = config
        self.data: Dict[str, Any] = {}
        self.callbacks: Dict[str, Any] = {}
    
    @abstractmethod
    def render(self) -> Panel:
        """渲染子界面
        
        Returns:
            Panel: 子界面面板
        """
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """获取子界面标题
        
        Returns:
            str: 子界面标题
        """
        pass
    
    def handle_key(self, key: str) -> bool:
        """处理键盘输入
        
        Args:
            key: 按键
            
        Returns:
            bool: True表示已处理，False表示需要传递到上层
        """
        # 默认处理ESC键返回主界面
        if key == "escape":
            return True
        
        # 子类可以重写此方法处理特定按键
        return False
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """更新子界面数据
        
        Args:
            data: 更新的数据
        """
        self.data.update(data)
    
    def set_callback(self, event: str, callback: Any) -> None:
        """设置回调函数
        
        Args:
            event: 事件名称
            callback: 回调函数
        """
        self.callbacks[event] = callback
    
    def trigger_callback(self, event: str, *args, **kwargs) -> Any:
        """触发回调函数
        
        Args:
            event: 事件名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 回调函数返回值
        """
        if event in self.callbacks:
            return self.callbacks[event](*args, **kwargs)
        return None
    
    def create_header(self) -> Text:
        """创建子界面头部
        
        Returns:
            Text: 头部文本
        """
        header_text = Text()
        header_text.append(self.get_title(), style="bold cyan")
        header_text.append(" (按ESC返回主界面)", style="dim yellow")
        return header_text
    
    def create_help_text(self) -> Text:
        """创建帮助文本
        
        Returns:
            Text: 帮助文本
        """
        help_text = Text()
        help_text.append("快捷键: ", style="bold")
        help_text.append("ESC - 返回主界面", style="dim")
        return help_text
    
    def create_empty_state(self, message: str = "暂无数据") -> Panel:
        """创建空状态面板
        
        Args:
            message: 空状态消息
            
        Returns:
            Panel: 空状态面板
        """
        content = Text(message, style="dim italic")
        return Panel(
            content,
            title=self.get_title(),
            border_style="dim"
        )
    
    def create_loading_state(self, message: str = "加载中...") -> Panel:
        """创建加载状态面板
        
        Args:
            message: 加载消息
            
        Returns:
            Panel: 加载状态面板
        """
        from rich.spinner import Spinner
        
        # 创建一个简单的加载状态文本，不使用动画spinner
        content = Text()
        content.append("⚫ ")  # 使用静态圆点代替动画spinner
        content.append(message)
        return Panel(
            content,
            title=self.get_title(),
            border_style="blue"
        )
    
    def create_error_state(self, error_message: str) -> Panel:
        """创建错误状态面板
        
        Args:
            error_message: 错误消息
            
        Returns:
            Panel: 错误状态面板
        """
        content = Text(f"错误: {error_message}", style="red")
        return Panel(
            content,
            title=f"{self.get_title()} - 错误",
            border_style="red"
        )