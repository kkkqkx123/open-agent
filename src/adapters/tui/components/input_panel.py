"""输入栏组件

包含多行输入支持、历史记录导航和命令识别处理
重构为协调器模式，整合多个子组件
"""

from typing import Optional, Dict, Any, List, Callable, Union

from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from ..config import TUIConfig
from ..key import Key, KeyType
from .input_panel_component import (
    InputHistory,
    InputBuffer,
    FileSelectorProcessor,
    WorkflowSelectorProcessor,
    SlashCommandProcessor
)
from ..logger import get_tui_silent_logger


class InputPanel:
    """输入栏组件
    
    作为协调器，整合输入历史、缓冲区和各种命令处理器
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        """初始化输入栏组件
        
        Args:
            config: TUI配置
        """
        self.config = config
        
        # 初始化TUI调试日志记录器
        self.tui_logger = get_tui_silent_logger("input_panel")
        
        # 初始化子组件
        self.input_buffer = InputBuffer()
        self.input_history = InputHistory()
        
        # 初始化命令处理器
        self.command_processors = {
            '@': FileSelectorProcessor(),
            '#': WorkflowSelectorProcessor(),
            '/': SlashCommandProcessor()
        }
        
        # 状态
        self.is_processing = False
        self.show_help = False
        self.placeholder = "在此输入消息... (使用 /help 查看命令, @选择文件, #选择工作流)"
        
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
    
    def handle_key(self, key: Union[Key, str]) -> Optional[str]:
        """处理键盘输入

        Args:
        key: 按键 (Key 对象或字符串)

        Returns:
        Optional[str]: 提交的文本或命令结果
        """
        # 处理Key对象或字符串
        if isinstance(key, Key):
            key_str = key.name
            self.tui_logger.debug_key_event(key.to_string(), True, "input_panel")
        else:
            key_str = str(key)
            self.tui_logger.debug_key_event(key_str, True, "input_panel")

        if self.is_processing:
            self.tui_logger.debug_input_handling("key_handling", f"Processing blocked: {key_str}")
            return None

    # 定义应该由全局处理器处理的按键（虚拟滚动相关）
        global_priority_keys = {"page_up", "page_down", "home", "end"}

        # 如果是全局优先按键，不处理，返回None让全局处理器处理
        if key_str in global_priority_keys:
            self.tui_logger.debug_input_handling("global_priority_key", f"Passing {key_str} to global handler")
            return None
        
        # 处理特殊按键
        if key_str == "enter" or key_str == "key_enter":
            result = self._handle_enter()
            self.tui_logger.debug_input_handling("enter_key", f"Handled enter key, result: {result}")
            return result
        elif key_str == "up":
            self._handle_up()
            self.tui_logger.debug_input_handling("up_key", "Handled up key")
        elif key_str == "down":
            self._handle_down()
            self.tui_logger.debug_input_handling("down_key", "Handled down key")
        elif key_str == "left":
            self.input_buffer.move_cursor("left")
            self.tui_logger.debug_input_handling("left_key", "Handled left key")
        elif key_str == "right":
            self.input_buffer.move_cursor("right")
            self.tui_logger.debug_input_handling("right_key", "Handled right key")
        elif key_str == "backspace":
            self.input_buffer.delete_char(backward=True)
            self.tui_logger.debug_input_handling("backspace_key", "Handled backspace key")
        elif key_str == "delete":
            self.input_buffer.delete_char(backward=False)
            self.tui_logger.debug_input_handling("delete_key", "Handled delete key")
        elif key_str == "tab":
            self._handle_tab()
            self.tui_logger.debug_input_handling("tab_key", "Handled tab key")
        elif key_str == "ctrl+m":
            self.input_buffer.toggle_multiline()
            self.tui_logger.debug_input_handling("ctrl+m_key", "Toggled multiline mode")
        elif key_str.startswith("char:"):
            # 普通字符输入（字符串格式）
            char = key_str[5:]  # 移除 "char:" 前缀
            self.input_buffer.insert_text(char)
            self.tui_logger.debug_input_handling("char_input", f"Inserted character: {char}")
        elif isinstance(key, Key) and key.key_type == KeyType.CHARACTER:
            # 普通字符输入（Key对象格式）
            char = key.name
            self.input_buffer.insert_text(char)
            self.tui_logger.debug_input_handling("char_input", f"Inserted character from Key object: {char}")

        # 对于非提交按键，返回特殊标记表示需要刷新UI
        if key_str != "enter":
            return "REFRESH_UI"
        
        # 对于Enter键，已经在上面的_handle_enter()中返回了结果，不会执行到这里
        # 添加此行以避免静态分析警告
        return None
    
    def _handle_enter(self) -> Optional[str]:
        """处理回车键
        
        Returns:
            Optional[str]: 提交的文本或命令结果
        """
        text = self.input_buffer.get_text()
        self.tui_logger.debug_input_handling("enter_handling", f"Processing text: {text}")
        
        if not text.strip():
            self.tui_logger.debug_input_handling("enter_handling", "Text is empty, returning None")
            return None
        
        # 检查多行输入逻辑
        if text.endswith('\\'):
            # 末尾为'\'，执行换行操作（不忽略空格）
            # 移除末尾的'\'并添加换行符
            text_without_backslash = text[:-1]
            self.input_buffer.set_text(text_without_backslash + '\n')
            self.tui_logger.debug_input_handling("enter_handling", "Processed multiline continuation")
            return None
        elif text.endswith(' '):
            # 末尾是空格，直接提交
            self.tui_logger.debug_input_handling("enter_handling", "Text ends with space, submitting")
            pass  # 继续执行提交逻辑
        elif self.input_buffer.multiline_mode:
            # 在多行模式下，检查当前行是否为空
            # 获取当前行（最后一行）
            if '\n' in text:
                last_line = text.split('\n')[-1]
            else:
                last_line = text
            
            # 如果最后一行为空或只包含空白字符，则提交输入
            if not last_line.strip():
                self.tui_logger.debug_input_handling("enter_handling", "Submitting in multiline mode (last line is empty)")
                # 清除末尾的换行符以准备提交
                text = text.rstrip('\n')
                self.input_buffer.set_text(text)
                # 继续执行到后面的提交逻辑
            else:  # 最后一行非空，插入换行符
                self.input_buffer.insert_text('\n')
                self.tui_logger.debug_input_handling("enter_handling", "Inserted newline in multiline mode")
                return None
        # 移除对包含换行符但不在多行模式的限制
        # 普通文本输入（包括包含换行符的）都应该可以提交
        
        # 检查是否是命令
        command_result = self._process_command(text)
        if command_result is not None:
            self.tui_logger.debug_input_handling("command_processing", f"Command result: {command_result}")
            # 添加到历史记录
            self.input_history.add_entry(text)
            
            # 清空输入
            self.input_buffer.clear()
            self.input_history.reset_navigation()
            
            return command_result
        else:
            # 普通消息
            self.tui_logger.debug_input_handling("message_processing", f"Processing user message: {text}")
            self.input_history.add_entry(text)
            self.input_buffer.clear()
            self.input_history.reset_navigation()
            
            if self.on_submit:
                self.on_submit(text)
            
            # 返回带有特殊前缀的文本，表示这是用户输入
            result = f"USER_INPUT:{text}"
            self.tui_logger.debug_input_handling("message_submit", f"Submitted user input: {result}")
            return result
    
    def _process_command(self, text: str) -> Optional[str]:
        """处理命令
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[str]: 命令结果或None（如果不是命令）
        """
        self.tui_logger.debug_input_handling("command_processing", f"Processing command: {text}")
        
        # 检查是否是命令
        if not text or text[0] not in self.command_processors:
            self.tui_logger.debug_input_handling("command_processing", f"Text is not a command: {text[0] if text else 'empty'}")
            return None
        
        # 获取对应的命令处理器
        processor = self.command_processors[text[0]]
        self.tui_logger.debug_input_handling("command_processing", f"Using processor: {type(processor).__name__}")
        
        # 执行命令
        context = {
            'input_history': self.input_history
        }
        result = processor.execute_command(text, context)
        self.tui_logger.debug_input_handling("command_processing", f"Command result: {result}")
        
        # 处理特殊命令结果
        if result == "CLEAR_SCREEN":
            return "CLEAR_SCREEN"
        elif result == "EXIT":
            return "EXIT"
        elif result and result.startswith("LOAD_SESSION:"):
            session_id = result.split(":", 1)[1]
            self.tui_logger.debug_session_operation("load", session_id)
            if self.on_command:
                self.on_command("load", [session_id])
        elif result and result.startswith("SELECT_WORKFLOW:"):
            # 解析工作流选择结果
            parts = result.split(":", 2)
            workflow_id = parts[1]
            args = parts[2].split("|") if len(parts) > 2 and parts[2] else []
            self.tui_logger.debug_workflow_operation(f"select_workflow: {workflow_id}")
            if self.on_command:
                self.on_command("workflow", [workflow_id] + args)
        elif result and result in ["SAVE_SESSION", "NEW_SESSION", "PAUSE_WORKFLOW",
                      "RESUME_WORKFLOW", "STOP_WORKFLOW", "OPEN_STUDIO",
                      "OPEN_SESSIONS", "OPEN_AGENTS"]:
            self.tui_logger.debug_session_operation(result.lower(), None)
            if self.on_command:
                self.on_command(result.lower(), [])
        else:
            # 显示命令结果
            self.tui_logger.debug_input_handling("command_result", f"Returning command result: {result}")
            return str(result) if result is not None else None
        
        return None
    
    def _handle_up(self) -> None:
        """处理向上键"""
        current_text = self.input_buffer.get_text()
        self.tui_logger.debug_input_handling("history_navigation", f"Handling up key, current text: {current_text}")
        history_text = self.input_history.navigate_up(current_text)
        self.input_buffer.set_text(history_text)
        self.tui_logger.debug_input_handling("history_navigation", f"Set history text: {history_text}")
    
    def _handle_down(self) -> None:
        """处理向下键"""
        current_text = self.input_buffer.get_text()
        self.tui_logger.debug_input_handling("history_navigation", f"Handling down key, current text: {current_text}")
        history_text = self.input_history.navigate_down(current_text)
        self.input_buffer.set_text(history_text)
        self.tui_logger.debug_input_handling("history_navigation", f"Set history text: {history_text}")
    
    def _handle_tab(self) -> None:
        """处理Tab键（命令自动补全）"""
        current_text = self.input_buffer.get_text()
        self.tui_logger.debug_input_handling("tab_completion", f"Handling tab completion, current text: {current_text}")
        
        # 检查是否是命令
        if not current_text or current_text[0] not in self.command_processors:
            self.tui_logger.debug_input_handling("tab_completion", "Not a command, skipping completion")
            return
        
        # 获取对应的命令处理器
        processor = self.command_processors[current_text[0]]
        
        # 获取补全建议
        suggestions = processor.get_suggestions(current_text)
        self.tui_logger.debug_input_handling("tab_completion", f"Got {len(suggestions)} suggestions: {suggestions}")
        
        if len(suggestions) == 1:
            # 唯一匹配，自动补全
            self.input_buffer.set_text(suggestions[0])
            self.tui_logger.debug_input_handling("tab_completion", f"Auto-completed to: {suggestions[0]}")
        elif len(suggestions) > 1:
            # 多个匹配，显示建议（这里可以扩展为显示补全菜单）
            # 暂时选择第一个公共前缀
            common_prefix = self._find_common_prefix([s[1:] for s in suggestions])
            if common_prefix and len(common_prefix) > len(current_text[1:]):
                self.input_buffer.set_text(current_text[0] + common_prefix)
                self.tui_logger.debug_input_handling("tab_completion", f"Completed to common prefix: {current_text[0] + common_prefix}")
    
    def _find_common_prefix(self, strings: List[str]) -> str:
        """查找字符串的公共前缀
        
        Args:
            strings: 字符串列表
            
        Returns:
            str: 公共前缀
        """
        if not strings:
            return ""
        
        prefix = strings[0]
        for s in strings[1:]:
            i = 0
            while i < len(prefix) and i < len(s) and prefix[i] == s[i]:
                i += 1
            prefix = prefix[:i]
            if not prefix:
                break
        
        return prefix
    
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
        # 创建文本对象
        input_text = Text()
        
        # 如果正在处理，显示状态
        if self.is_processing:
            input_text.append("处理中...", style="yellow")
        else:
            # 对于空缓冲区，光标应该在占位符前面
            if self.input_buffer.is_empty():
                # 添加光标和占位符
                input_text.append("|", style="bold green")
                input_text.append(self.placeholder, style="dim")
            else:
                # 获取输入缓冲区的文本
                buffer_text = self.input_buffer.get_text()
                # 添加输入文本
                input_text.append(buffer_text)
                # 添加光标
                input_text.append("|", style="bold green")
        
        # 创建状态信息
        status_text = Text()
        if self.input_buffer.multiline_mode:
            status_text.append("[多行]", style="cyan")
        if self.show_help:
            status_text.append(" [帮助]", style="green")
        
        # 组合内容
        content: Any
        if status_text.plain:
            content = Table.grid()
            content.add_column()
            content.add_column()
            content.add_row(input_text, status_text)
        else:
            content = input_text
        
        return Panel(
            content,
            title="输入",
            border_style="green" if not self.is_processing else "yellow"
        )
    
    def get_command_processor(self, trigger_char: str) -> Optional[Any]:
        """获取指定触发字符的命令处理器
        
        Args:
            trigger_char: 触发字符
            
        Returns:
            BaseCommandProcessor: 命令处理器或None
        """
        return self.command_processors.get(trigger_char)
    
    def register_custom_command(self, trigger_char: str, processor: Any) -> None:
        """注册自定义命令处理器
        
        Args:
            trigger_char: 触发字符
            processor: 命令处理器
        """
        self.command_processors[trigger_char] = processor