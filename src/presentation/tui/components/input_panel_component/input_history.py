"""输入历史记录组件

负责管理用户输入的历史记录，支持导航和检索功能
"""

from typing import List


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
    
    def add_entry(self, input_text: str) -> None:
        """添加历史记录
        
        Args:
            input_text: 输入文本
        """
        # 如果输入为空或与上一条相同，则不添加
        if not input_text.strip() or (self.history and input_text == self.history[-1]):
            return
        
        self.history.append(input_text)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
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
        if not self.history:
            return current_input
        
        # 如果当前在最新输入，保存临时输入
        if self.current_index == -1:
            self.temp_input = current_input
        
        # 移动到上一条历史记录
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[-(self.current_index + 1)]
        
        return current_input
    
    def navigate_down(self, current_input: str) -> str:
        """向下导航历史记录
        
        Args:
            current_input: 当前输入
            
        Returns:
            str: 历史记录或当前输入
        """
        if not self.history or self.current_index == -1:
            return current_input
        
        # 移动到下一条历史记录
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[-(self.current_index + 1)]
        elif self.current_index == 0:
            # 返回到当前输入
            self.current_index = -1
            return self.temp_input
        
        return current_input
    
    def reset_navigation(self) -> None:
        """重置导航状态"""
        self.current_index = -1
        self.temp_input = ""
    
    def clear_history(self) -> None:
        """清空历史记录"""
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