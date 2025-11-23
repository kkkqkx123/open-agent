"""输入缓冲区组件

负责管理输入缓冲区、多行模式和光标操作
"""

from typing import List

from ...logger import get_tui_silent_logger


class InputBuffer:
    """输入缓冲区组件"""
    
    def __init__(self):
        """初始化输入缓冲区"""
        self.buffer = ""
        self.cursor_position = 0
        self.multiline_mode = False
        self.lines: List[str] = []
        self.current_line = 0
        
        # 初始化TUI调试日志记录器
        self.tui_logger = get_tui_silent_logger("input_buffer")
    
    def insert_text(self, text: str) -> None:
        """插入文本
        
        Args:
            text: 要插入的文本
        """
        self.tui_logger.debug_input_handling("insert_text", f"Inserting text: {text}")
        
        if self.multiline_mode:
            # 多行模式
            if self.current_line < len(self.lines):
                line = self.lines[self.current_line]
                self.lines[self.current_line] = line[:self.cursor_position] + text + line[self.cursor_position:]
                self.cursor_position += len(text)
                self.tui_logger.debug_input_handling("insert_text", f"Inserted in multiline mode, line {self.current_line}, position {self.cursor_position}")
            else:
                self.lines.append(text)
                self.current_line = len(self.lines) - 1
                self.cursor_position = len(text)
                self.tui_logger.debug_input_handling("insert_text", f"Inserted new line in multiline mode, line {self.current_line}, position {self.cursor_position}")
        else:
            # 单行模式
            self.buffer = self.buffer[:self.cursor_position] + text + self.buffer[self.cursor_position:]
            self.cursor_position += len(text)
            self.tui_logger.debug_input_handling("insert_text", f"Inserted in single line mode, position {self.cursor_position}")
    
    def delete_char(self, backward: bool = True) -> None:
        """删除字符
        
        Args:
            backward: 是否向后删除
        """
        self.tui_logger.debug_input_handling("delete_char", f"Deleting character, backward: {backward}, position: {self.cursor_position}")
        
        if self.multiline_mode:
            if self.current_line < len(self.lines):
                line = self.lines[self.current_line]
                if backward and self.cursor_position > 0:
                    self.lines[self.current_line] = line[:self.cursor_position-1] + line[self.cursor_position:]
                    self.cursor_position -= 1
                    self.tui_logger.debug_input_handling("delete_char", f"Deleted backward in multiline mode, line {self.current_line}, position {self.cursor_position}")
                elif not backward and self.cursor_position < len(line):
                    self.lines[self.current_line] = line[:self.cursor_position] + line[self.cursor_position+1:]
                    self.tui_logger.debug_input_handling("delete_char", f"Deleted forward in multiline mode, line {self.current_line}")
        else:
            if backward and self.cursor_position > 0:
                self.buffer = self.buffer[:self.cursor_position-1] + self.buffer[self.cursor_position:]
                self.cursor_position -= 1
                self.tui_logger.debug_input_handling("delete_char", f"Deleted backward in single line mode, position {self.cursor_position}")
            elif not backward and self.cursor_position < len(self.buffer):
                self.buffer = self.buffer[:self.cursor_position] + self.buffer[self.cursor_position+1:]
                self.tui_logger.debug_input_handling("delete_char", f"Deleted forward in single line mode, position {self.cursor_position}")
    
    def move_cursor(self, direction: str) -> None:
        """移动光标
        
        Args:
            direction: 方向 (left, right, up, down, home, end)
        """
        self.tui_logger.debug_input_handling("move_cursor", f"Moving cursor, direction: {direction}, current pos: {self.cursor_position}")
        
        if self.multiline_mode:
            if direction == "left" and self.cursor_position > 0:
                self.cursor_position -= 1
                self.tui_logger.debug_input_handling("move_cursor", f"Moved left in multiline mode, new pos: {self.cursor_position}")
            elif direction == "right" and self.current_line < len(self.lines) and self.cursor_position < len(self.lines[self.current_line]):
                self.cursor_position += 1
                self.tui_logger.debug_input_handling("move_cursor", f"Moved right in multiline mode, new pos: {self.cursor_position}")
            elif direction == "up" and self.current_line > 0:
                self.current_line -= 1
                self.cursor_position = min(self.cursor_position, len(self.lines[self.current_line]))
                self.tui_logger.debug_input_handling("move_cursor", f"Moved up in multiline mode, new line: {self.current_line}, pos: {self.cursor_position}")
            elif direction == "down" and self.current_line < len(self.lines) - 1:
                self.current_line += 1
                self.cursor_position = min(self.cursor_position, len(self.lines[self.current_line]))
                self.tui_logger.debug_input_handling("move_cursor", f"Moved down in multiline mode, new line: {self.current_line}, pos: {self.cursor_position}")
            elif direction == "home":
                self.cursor_position = 0
                self.tui_logger.debug_input_handling("move_cursor", f"Moved to home in multiline mode, new pos: {self.cursor_position}")
            elif direction == "end":
                self.cursor_position = len(self.lines[self.current_line])
                self.tui_logger.debug_input_handling("move_cursor", f"Moved to end in multiline mode, new pos: {self.cursor_position}")
        else:
            if direction == "left" and self.cursor_position > 0:
                self.cursor_position -= 1
                self.tui_logger.debug_input_handling("move_cursor", f"Moved left in single line mode, new pos: {self.cursor_position}")
            elif direction == "right" and self.cursor_position < len(self.buffer):
                self.cursor_position += 1
                self.tui_logger.debug_input_handling("move_cursor", f"Moved right in single line mode, new pos: {self.cursor_position}")
            elif direction in ["home"]:
                self.cursor_position = 0
                self.tui_logger.debug_input_handling("move_cursor", f"Moved to home in single line mode, new pos: {self.cursor_position}")
            elif direction in ["end"]:
                self.cursor_position = len(self.buffer)
                self.tui_logger.debug_input_handling("move_cursor", f"Moved to end in single line mode, new pos: {self.cursor_position}")
    
    def toggle_multiline(self) -> None:
        """切换多行模式"""
        old_mode = self.multiline_mode
        self.tui_logger.debug_input_handling("toggle_multiline", f"Toggling multiline mode, current: {old_mode}")
        
        if not self.multiline_mode:
            # 切换到多行模式
            self.multiline_mode = True
            self.lines = self.buffer.split('\n') if self.buffer else [""]
            self.current_line = len(self.lines) - 1
            self.cursor_position = len(self.lines[self.current_line]) if self.lines else 0
            self.tui_logger.debug_ui_state_change("multiline_mode", old_mode, self.multiline_mode, operation="toggle_to_multiline")
        else:
            # 切换到单行模式
            self.multiline_mode = False
            self.buffer = '\n'.join(self.lines)
            self.cursor_position = len(self.buffer)
            self.tui_logger.debug_ui_state_change("multiline_mode", old_mode, self.multiline_mode, operation="toggle_to_singleline")
    
    def get_text(self) -> str:
        """获取文本
        
        Returns:
            str: 缓冲区文本
        """
        if self.multiline_mode:
            text = '\n'.join(self.lines)
        else:
            text = self.buffer
        
        return text
    
    def set_text(self, text: str) -> None:
        """设置文本
        
        Args:
            text: 文本内容
        """
        self.tui_logger.debug_input_handling("set_text", f"Setting text: {text}")
        
        if self.multiline_mode:
            self.lines = text.split('\n')
            self.current_line = len(self.lines) - 1
            self.cursor_position = len(self.lines[self.current_line]) if self.lines else 0
        else:
            self.buffer = text
            self.cursor_position = len(text)
    
    def clear(self) -> None:
        """清空缓冲区"""
        self.tui_logger.debug_input_handling("clear", f"Clearing buffer, old text: {self.get_text()}")
        
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