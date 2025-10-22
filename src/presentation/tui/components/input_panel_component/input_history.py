"""输入历史记录组件

负责管理用户输入的历史记录，支持导航和检索功能
"""

from typing import List

from ...logger import get_tui_silent_logger


class InputHistory:
    """输入历史记录组件"""
    
    def __init__(self, max_history: int = 100):
        """初始化输入历史组件
        
        Args:
            max_history: 最大历史记录数量
        """
        self.max_history = max_history
        self.history: List[str] = []
        self.current_index = -1  # -1 表示当前输入，>=0 表示历史记录索引
        self.temp_input = ""  # 临时保存当前输入
        
        # 初始化TUI调试日志记录器
        self.tui_logger = get_tui_silent_logger("input_history")
    
    def add_entry(self, input_text: str) -> None:
        """添加历史记录
        
        Args:
            input_text: 输入文本
        """
        self.tui_logger.debug_input_handling("add_history", f"Adding entry to history: {input_text}")
        
        # 如果输入为空或与上一条相同，则不添加
        if not input_text.strip() or (self.history and input_text == self.history[-1]):
            self.tui_logger.debug_input_handling("add_history", "Entry is empty or duplicate, not adding")
            return
        
        self.history.append(input_text)
        self.tui_logger.debug_input_handling("add_history", f"Added entry, history size: {len(self.history)}")
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.tui_logger.debug_input_handling("add_history", f"Trimmed history to max size: {self.max_history}")
        
        # 重置索引
        self.current_index = -1
        self.temp_input = ""
    
    def navigate_up(self, current_input: str) -> str:
        """向上导航历史记录
        
        Args:
            current_input: 当前输入
            
        Returns:
            str: 历史记录或当前输入
        """
        self.tui_logger.debug_input_handling("navigate_up", f"Navigating up, current input: {current_input}, index: {self.current_index}")
        
        if not self.history:
            self.tui_logger.debug_input_handling("navigate_up", "No history available, returning current input")
            return current_input
        
        # 如果当前在最新输入，保存临时输入
        if self.current_index == -1:
            self.temp_input = current_input
            self.tui_logger.debug_input_handling("navigate_up", f"Saved current input as temp: {current_input}")
        
        # 移动到上一条历史记录
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            history_entry = self.history[-(self.current_index + 1)]
            self.tui_logger.debug_input_handling("navigate_up", f"Moved to history entry {self.current_index}, entry: {history_entry}")
            return history_entry
        
        self.tui_logger.debug_input_handling("navigate_up", "At end of history, returning current input")
        return current_input
    
    def navigate_down(self, current_input: str) -> str:
        """向下导航历史记录
        
        Args:
            current_input: 当前输入
            
        Returns:
            str: 历史记录或当前输入
        """
        self.tui_logger.debug_input_handling("navigate_down", f"Navigating down, current input: {current_input}, index: {self.current_index}")
        
        if not self.history or self.current_index == -1:
            self.tui_logger.debug_input_handling("navigate_down", "No history or at current input, returning current input")
            return current_input
        
        # 移动到下一条历史记录
        if self.current_index > 0:
            self.current_index -= 1
            history_entry = self.history[-(self.current_index + 1)]
            self.tui_logger.debug_input_handling("navigate_down", f"Moved to history entry {self.current_index}, entry: {history_entry}")
            return history_entry
        elif self.current_index == 0:
            # 返回到当前输入
            self.current_index = -1
            self.tui_logger.debug_input_handling("navigate_down", f"Returned to current input: {self.temp_input}")
            return self.temp_input
        
        self.tui_logger.debug_input_handling("navigate_down", "At start of navigation, returning current input")
        return current_input
    
    def reset_navigation(self) -> None:
        """重置导航状态"""
        old_index = self.current_index
        old_temp = self.temp_input
        self.current_index = -1
        self.temp_input = ""
        self.tui_logger.debug_ui_state_change("history_navigation", f"index:{old_index},temp:{old_temp}", f"index:{self.current_index},temp:{self.temp_input}", operation="reset_navigation")
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.tui_logger.debug_input_handling("clear_history", f"Clearing history, old size: {len(self.history)}")
        self.history = []
        self.current_index = -1
        self.temp_input = ""
    
    def get_recent_history(self, count: int = 5) -> List[str]:
        """获取最近的历史记录
        
        Args:
            count: 返回数量
            
        Returns:
            List[str]: 最近的历史记录
        """
        return self.history[-count:] if self.history else []