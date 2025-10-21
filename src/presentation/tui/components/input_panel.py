"""输入栏组件

包含多行输入支持、历史记录导航和命令识别处理
"""

from typing import Optional, Dict, Any, List, Callable, Tuple
from datetime import datetime
import re

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult

from ..config import TUIConfig


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


class CommandProcessor:
    """命令识别处理组件"""
    
    def __init__(self):
        """初始化命令处理器"""
        self.commands: Dict[str, Callable] = {}
        self.command_aliases: Dict[str, str] = {}
        self.command_help: Dict[str, str] = {}
        
        # 注册内置命令
        self._register_builtin_commands()
    
    def _register_builtin_commands(self) -> None:
        """注册内置命令"""
        self.register_command("help", self._cmd_help, "显示帮助信息", ["h", "?"])
        self.register_command("clear", self._cmd_clear, "清空屏幕", ["cls"])
        self.register_command("exit", self._cmd_exit, "退出程序", ["quit", "q"])
        self.register_command("history", self._cmd_history, "显示历史记录", ["hist"])
        self.register_command("save", self._cmd_save, "保存会话")
        self.register_command("load", self._cmd_load, "加载会话")
        self.register_command("new", self._cmd_new, "创建新会话")
        self.register_command("pause", self._cmd_pause, "暂停工作流")
        self.register_command("resume", self._cmd_resume, "恢复工作流")
        self.register_command("stop", self._cmd_stop, "停止工作流")
        self.register_command("studio", self._cmd_studio, "打开Studio", ["sg"])
        self.register_command("sessions", self._cmd_sessions, "打开会话管理", ["sess"])
        self.register_command("agents", self._cmd_agents, "打开Agent选择", ["ag"])
    
    def register_command(
        self,
        name: str,
        handler: Callable,
        help_text: str = "",
        aliases: Optional[List[str]] = None
    ) -> None:
        """注册命令
        
        Args:
            name: 命令名称
            handler: 处理函数
            help_text: 帮助文本
            aliases: 别名列表
        """
        self.commands[name] = handler
        self.command_help[name] = help_text
        
        if aliases:
            for alias in aliases:
                self.command_aliases[alias] = name
    
    def is_command(self, input_text: str) -> bool:
        """检查是否是命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            bool: 是否是命令
        """
        return input_text.startswith('/')
    
    def parse_command(self, input_text: str) -> Tuple[str, List[str]]:
        """解析命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            Tuple[str, List[str]]: 命令名称和参数列表
        """
        if not self.is_command(input_text):
            return "", []
        
        # 移除前导斜杠
        command_text = input_text[1:].strip()
        
        # 分割命令和参数
        parts = command_text.split()
        if not parts:
            return "", []
        
        command_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # 检查别名
        if command_name in self.command_aliases:
            command_name = self.command_aliases[command_name]
        
        return command_name, args
    
    def execute_command(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """执行命令
        
        Args:
            input_text: 输入文本
            context: 执行上下文
            
        Returns:
            Optional[str]: 执行结果或错误信息
        """
        command_name, args = self.parse_command(input_text)
        
        if not command_name:
            return "无效的命令格式"
        
        if command_name not in self.commands:
            return f"未知命令: {command_name}"
        
        try:
            handler = self.commands[command_name]
            if context:
                return handler(args, context)
            else:
                return handler(args)
        except Exception as e:
            return f"命令执行错误: {str(e)}"
    
    def get_command_help(self, command_name: Optional[str] = None) -> str:
        """获取命令帮助
        
        Args:
            command_name: 命令名称，None表示显示所有命令
            
        Returns:
            str: 帮助文本
        """
        if command_name:
            if command_name in self.command_help:
                return f"/{command_name}: {self.command_help[command_name]}"
            else:
                return f"未知命令: {command_name}"
        
        # 显示所有命令
        help_text = "可用命令:\n"
        for name, help_str in self.command_help.items():
            aliases = [k for k, v in self.command_aliases.items() if v == name]
            alias_text = f" (别名: {', '.join(aliases)})" if aliases else ""
            help_text += f"  /{name}{alias_text} - {help_str}\n"
        
        return help_text
    
    # 内置命令处理函数
    def _cmd_help(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """帮助命令"""
        if args:
            return self.get_command_help(args[0])
        return self.get_command_help()
    
    def _cmd_clear(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """清屏命令"""
        return "CLEAR_SCREEN"
    
    def _cmd_exit(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """退出命令"""
        return "EXIT"
    
    def _cmd_history(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """历史记录命令"""
        if context and 'input_history' in context:
            history = context['input_history'].get_recent_history(10)
            if history:
                result = "最近输入历史:\n"
                for i, entry in enumerate(history, 1):
                    result += f"  {i}. {entry}\n"
                return result
        return "无历史记录"
    
    def _cmd_save(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """保存命令"""
        return "SAVE_SESSION"
    
    def _cmd_load(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """加载命令"""
        if args:
            return f"LOAD_SESSION:{args[0]}"
        return "请指定会话ID"
    
    def _cmd_new(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """新建会话命令"""
        return "NEW_SESSION"
    
    def _cmd_pause(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """暂停命令"""
        return "PAUSE_WORKFLOW"
    
    def _cmd_resume(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """恢复命令"""
        return "RESUME_WORKFLOW"
    
    def _cmd_stop(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """停止命令"""
        return "STOP_WORKFLOW"
    
    def _cmd_studio(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """Studio命令"""
        return "OPEN_STUDIO"
    
    def _cmd_sessions(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """会话管理命令"""
        return "OPEN_SESSIONS"
    
    def _cmd_agents(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """Agent选择命令"""
        return "OPEN_AGENTS"


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


class InputPanelComponent:
    """输入栏组件
    
    包含多行输入支持、历史记录导航和命令识别处理
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        """初始化输入栏组件
        
        Args:
            config: TUI配置
        """
        self.config = config
        self.input_buffer = InputBuffer()
        self.input_history = InputHistory()
        self.command_processor = CommandProcessor()
        
        # 状态
        self.is_processing = False
        self.show_help = False
        self.placeholder = "在此输入消息... (使用 /help 查看命令)"
        
        # 回调函数
        self.on_submit: Optional[Callable[[str], None]] = None
        self.on_command: Optional[Callable[[str, List[str]], None]] = None
    
    def set_submit_callback(self, callback: Callable[[str], None]) -> None:
        """设置提交回调
        
        Args:
            callback: 回调函数
        """
        self.on_submit = callback
    
    def set_command_callback(self, callback: Callable[[str, List[str]], None]) -> None:
        """设置命令回调
        
        Args:
            callback: 回调函数
        """
        self.on_command = callback
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理键盘输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 提交的文本或命令结果
        """
        if self.is_processing:
            return None
        
        # 处理特殊按键
        if key == "enter":
            return self._handle_enter()
        elif key == "up":
            self._handle_up()
        elif key == "down":
            self._handle_down()
        elif key == "left":
            self.input_buffer.move_cursor("left")
        elif key == "right":
            self.input_buffer.move_cursor("right")
        elif key == "backspace":
            self.input_buffer.delete_char(backward=True)
        elif key == "delete":
            self.input_buffer.delete_char(backward=False)
        elif key == "home":
            self.input_buffer.move_cursor("home")
        elif key == "end":
            self.input_buffer.move_cursor("end")
        elif key == "tab":
            self._handle_tab()
        elif key == "ctrl+m":
            self.input_buffer.toggle_multiline()
        elif key.startswith("char:"):
            # 普通字符输入
            char = key[5:]  # 移除 "char:" 前缀
            self.input_buffer.insert_text(char)
        
        return None
    
    def _handle_enter(self) -> Optional[str]:
        """处理回车键
        
        Returns:
            Optional[str]: 提交的文本或命令结果
        """
        text = self.input_buffer.get_text()
        
        if not text.strip():
            return None
        
        # 检查是否是命令
        if self.command_processor.is_command(text):
            # 执行命令
            context = {
                'input_history': self.input_history
            }
            result = self.command_processor.execute_command(text, context)
            
            # 添加到历史记录
            self.input_history.add_entry(text)
            
            # 清空输入
            self.input_buffer.clear()
            self.input_history.reset_navigation()
            
            # 处理特殊命令
            if result == "CLEAR_SCREEN":
                return "CLEAR_SCREEN"
            elif result == "EXIT":
                return "EXIT"
            elif result and result.startswith("LOAD_SESSION:"):
                session_id = result.split(":", 1)[1]
                if self.on_command:
                    self.on_command("load", [session_id])
            elif result and result in ["SAVE_SESSION", "NEW_SESSION", "PAUSE_WORKFLOW",
                          "RESUME_WORKFLOW", "STOP_WORKFLOW", "OPEN_STUDIO",
                          "OPEN_SESSIONS", "OPEN_AGENTS"]:
                if self.on_command:
                    self.on_command(result.lower(), [])
            else:
                # 显示命令结果
                return result
        else:
            # 普通消息
            self.input_history.add_entry(text)
            self.input_buffer.clear()
            self.input_history.reset_navigation()
            
            if self.on_submit:
                self.on_submit(text)
        
        return None
    
    def _handle_up(self) -> None:
        """处理向上键"""
        current_text = self.input_buffer.get_text()
        history_text = self.input_history.navigate_up(current_text)
        self.input_buffer.set_text(history_text)
    
    def _handle_down(self) -> None:
        """处理向下键"""
        current_text = self.input_buffer.get_text()
        history_text = self.input_history.navigate_down(current_text)
        self.input_buffer.set_text(history_text)
    
    def _handle_tab(self) -> None:
        """处理Tab键（命令自动补全）"""
        current_text = self.input_buffer.get_text()
        if self.command_processor.is_command(current_text):
            # 简单的命令补全
            command_name, _ = self.command_processor.parse_command(current_text)
            if command_name:
                # 查找匹配的命令
                matches = [cmd for cmd in self.command_processor.commands.keys() 
                          if cmd.startswith(command_name)]
                if len(matches) == 1:
                    # 唯一匹配，自动补全
                    new_text = f"/{matches[0]}"
                    self.input_buffer.set_text(new_text)
    
    def set_processing(self, processing: bool) -> None:
        """设置处理状态
        
        Args:
            processing: 是否正在处理
        """
        self.is_processing = processing
    
    def render(self) -> Panel:
        """渲染输入栏
        
        Returns:
            Panel: 输入栏面板
        """
        # 创建输入显示
        if self.input_buffer.is_empty() and not self.is_processing:
            input_text = Text(self.placeholder, style="dim")
        else:
            input_text = Text(self.input_buffer.get_text())
            
            # 添加光标
            if not self.is_processing:
                input_text.append("▊", style="blink green")
        
        # 如果正在处理，显示状态
        if self.is_processing:
            input_text = Text("处理中...", style="yellow")
        
        # 创建状态信息
        status_text = Text()
        if self.input_buffer.multiline_mode:
            status_text.append("[多行]", style="cyan")
        if self.show_help:
            status_text.append(" [帮助]", style="green")
        
        # 组合内容
        if status_text:
            content = Table.grid()
            content.add_column()
            content.add_column()
            content.add_row(input_text, status_text)
        else:
            content = input_text
        
        return Panel(
            Align.left(content),
            title="输入",
            border_style="green" if not self.is_processing else "yellow"
        )