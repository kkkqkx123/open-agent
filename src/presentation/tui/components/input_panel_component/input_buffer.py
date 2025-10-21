"""输入缓冲区组件

负责管理输入缓冲区、多行模式和光标操作
"""

from typing import List


class InputBuffer:
    """输入缓冲区组件"""
    
    def __init__(self):
        """初始化输入缓冲区"""
        self.buffer = ""
        self.cursor_position = 0
        self.multiline_mode = False
        self.lines: List[str] = []
        self.current_line = 0
    
    def insert_text(self, text: str) -> None:
        """插入文本
        
        Args:
            text: 要插入的文本
        """
        if self.multiline_mode:
            # 多行模式
            if self.current_line < len(self.lines):
                line = self.lines[self.current_line]
                self.lines[self.current_line] = line[:self.cursor_position] + text + line[self.cursor_position:]
                self.cursor_position += len(text)
            else:
                self.lines.append(text)
                self.current_line = len(self.lines) - 1
                self.cursor_position = len(text)
        else:
            # 单行模式
            self.buffer = self.buffer[:self.cursor_position] + text + self.buffer[self.cursor_position:]
            self.cursor_position += len(text)
    
    def delete_char(self, backward: bool = True) -> None:
        """删除字符
        
        Args:
            backward: 是否向后删除
        """
        if self.multiline_mode:
            if self.current_line < len(self.lines):
                line = self.lines[self.current_line]
                if backward and self.cursor_position > 0:
                    self.lines[self.current_line] = line[:self.cursor_position-1] + line[self.cursor_position:]
                    self.cursor_position -= 1
                elif not backward and self.cursor_position < len(line):
                    self.lines[self.current_line] = line[:self.cursor_position] + line[self.cursor_position+1:]
        else:
            if backward and self.cursor_position > 0:
                self.buffer = self.buffer[:self.cursor_position-1] + self.buffer[self.cursor_position:]
                self.cursor_position -= 1
            elif not backward and self.cursor_position < len(self.buffer):
                self.buffer = self.buffer[:self.cursor_position] + self.buffer[self.cursor_position+1:]
    
    def move_cursor(self, direction: str) -> None:
        """移动光标
        
        Args:
            direction: 方向 (left, right, up, down, home, end)
        """
        if self.multiline_mode:
            if direction == "left" and self.cursor_position > 0:
                self.cursor_position -= 1
            elif direction == "right" and self.current_line < len(self.lines) and self.cursor_position < len(self.lines[self.current_line]):
                self.cursor_position += 1
            elif direction == "up" and self.current_line > 0:
                self.current_line -= 1
                self.cursor_position = min(self.cursor_position, len(self.lines[self.current_line]))
            elif direction == "down" and self.current_line < len(self.lines) - 1:
                self.current_line += 1
                self.cursor_position = min(self.cursor_position, len(self.lines[self.current_line]))
            elif direction == "home":
                self.cursor_position = 0
            elif direction == "end":
                self.cursor_position = len(self.lines[self.current_line])
        else:
            if direction == "left" and self.cursor_position > 0:
                self.cursor_position -= 1
            elif direction == "right" and self.cursor_position < len(self.buffer):
                self.cursor_position += 1
            elif direction in ["home"]:
                self.cursor_position = 0
            elif direction in ["end"]:
                self.cursor_position = len(self.buffer)
    
    def toggle_multiline(self) -> None:
        """切换多行模式"""
        if not self.multiline_mode:
            # 切换到多行模式
            self.multiline_mode = True
            self.lines = self.buffer.split('\n') if self.buffer else [""]
            self.current_line = len(self.lines) - 1
            self.cursor_position = len(self.lines[self.current_line]) if self.lines else 0
        else:
            # 切换到单行模式
            self.multiline_mode = False
            self.buffer = '\n'.join(self.lines)
            self.cursor_position = len(self.buffer)
    
    def get_text(self) -> str:
        """获取文本
        
        Returns:
            str: 缓冲区文本
        """
        if self.multiline_mode:
            return '\n'.join(self.lines)
        return self.buffer
    
    def set_text(self, text: str) -> None:
        """设置文本
        
        Args:
            text: 文本内容
        """
        if self.multiline_mode:
            self.lines = text.split('\n')
            self.current_line = len(self.lines) - 1
            self.cursor_position = len(self.lines[self.current_line]) if self.lines else 0
        else:
            self.buffer = text
            self.cursor_position = len(text)
    
    def clear(self) -> None:
        """清空缓冲区"""
        self.buffer = ""
        self.cursor_position = 0
        self.multiline_mode = False
        self.lines = []
        self.current_line = 0
    
    def is_empty(self) -> bool:
        """检查是否为空
        
        Returns:
            bool: 是否为空
        """
        if self.multiline_mode:
            return not any(line.strip() for line in self.lines)
        return not self.buffer.strip()