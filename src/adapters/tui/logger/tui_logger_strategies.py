"""TUI日志记录策略实现"""

from typing import Any, Dict, Optional
from src.interfaces.logger import LogLevel
from .tui_logger_base import TUILoggingStrategy


class SilentLoggingStrategy(TUILoggingStrategy):
    """静默日志记录策略，只在调试模式下记录日志"""
    
    def should_log(self, level: LogLevel) -> bool:
        """只在调试模式下记录日志"""
        from .tui_logger_manager import TUILoggerManager
        manager = TUILoggerManager()
        return manager.is_debug_enabled()
    
    def get_logger_prefix(self) -> str:
        """获取静默日志记录器前缀"""
        return "tui.silent"
    
    def handle_log_error(self, error: Exception) -> None:
        """静默处理日志记录错误，避免影响TUI运行"""
        # 静默处理，不输出任何错误信息
        pass


class DebugLoggingStrategy(TUILoggingStrategy):
    """调试日志记录策略，总是记录日志"""
    
    def should_log(self, level: LogLevel) -> bool:
        """总是记录日志"""
        return True
    
    def get_logger_prefix(self) -> str:
        """获取调试日志记录器前缀"""
        return "tui"
    
    def handle_log_error(self, error: Exception) -> None:
        """处理日志记录错误，输出到控制台"""
        print(f"TUI日志记录错误: {error}")
    
    def format_key_event(self, key: str) -> str:
        """格式化按键事件显示，提供更详细的信息"""
        # 对于char:类型按键，显示更详细的信息
        display_key = key
        if key.startswith("char:"):
            char_value = key[5:]  # 移除"char:"前缀
            if char_value == '\n':
                display_key = f"{key} (Enter/Newline)"
            elif char_value == '\x1b':
                display_key = f"{key} (Escape)"
            elif char_value == '\x7f':
                display_key = f"{key} (Backspace)"
            elif char_value == '\t':
                display_key = f"{key} (Tab)"
            elif char_value == ' ':
                display_key = f"{key} (Space)"
            else:
                # 显示字符的ASCII码
                display_key = f"{key} (ASCII: {ord(char_value) if char_value else 0})"
        
        return display_key