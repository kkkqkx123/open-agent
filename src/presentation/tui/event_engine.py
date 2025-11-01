"""TUI事件处理引擎"""

import sys
import threading
import time
import queue
from typing import Optional, Callable, Dict, Any
from blessed import Terminal
import asyncio

# 导入TUI日志记录器
from .logger import get_tui_silent_logger


class EventEngine:
    """事件处理引擎，负责处理键盘输入、事件分发、线程管理"""
    
    def __init__(self, terminal: Terminal, config: Any) -> None:
        """初始化事件引擎
        
        Args:
            terminal: blessed终端对象
            config: TUI配置对象
        """
        self.terminal = terminal
        self.config = config
        self.running = False
        self.input_queue = queue.Queue()
        self.input_thread: Optional[threading.Thread] = None
        
        # 事件处理器
        self.key_handlers: Dict[str, Callable[[str], bool]] = {}
        self.global_key_handler: Optional[Callable[[str], bool]] = None
        
        # 输入组件处理器
        self.input_component_handler: Optional[Callable[[str], Optional[str]]] = None
        self.input_result_handler: Optional[Callable[[str], None]] = None
        
        # 初始化TUI调试日志记录器
        self.tui_logger = get_tui_silent_logger("event_engine")
        
        # 用于处理Windows终端中Alt+数字键的特殊逻辑
        self._pending_alt_key: Optional[str] = None
        self._alt_key_timeout: float = 0.1  # 100ms超时
        self._last_escape_time: float = 0.0
        self._pending_escape: bool = False  # 标记是否正在等待可能的Alt键组合
    
    def register_key_handler(self, key: str, handler: Callable[[str], bool]) -> None:
        """注册按键处理器
        
        Args:
            key: 按键字符串
            handler: 处理函数，返回True表示已处理
        """
        self.key_handlers[key] = handler
    
    def unregister_key_handler(self, key: str) -> None:
        """取消注册按键处理器
        
        Args:
            key: 按键字符串
        """
        if key in self.key_handlers:
            del self.key_handlers[key]
    
    def set_global_key_handler(self, handler: Callable[[str], bool]) -> None:
        """设置全局按键处理器
        
        Args:
            handler: 全局处理函数
        """
        self.global_key_handler = handler
    
    def set_input_component_handler(self, handler: Callable[[str], Optional[str]]) -> None:
        """设置输入组件处理器
        
        Args:
            handler: 输入组件处理函数，返回处理结果
        """
        self.input_component_handler = handler
    
    def set_input_result_handler(self, handler: Callable[[str], None]) -> None:
        """设置输入结果处理器
        
        Args:
            handler: 输入结果处理函数
        """
        self.input_result_handler = handler
    
    def start_event_loop(self) -> None:
        """启动事件循环"""
        self.running = True
        
        # 启动输入读取线程
        self.input_thread = threading.Thread(target=self._input_reader, daemon=True)
        self.input_thread.start()
        
        # 主事件循环
        while self.running:
            try:
                # 处理队列中的输入
                try:
                    while not self.input_queue.empty():
                        key_str = self.input_queue.get_nowait()
                        self._process_key(key_str)
                except queue.Empty:
                    pass
                
                # 检查ESC键超时
                self._check_escape_timeout()
                
                # 短暂休眠以减少CPU使用率
                time.sleep(0.05)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                # 只显示非编码相关的错误
                if "codec" not in str(e) and "decode" not in str(e):
                    print(f"事件循环错误: {e}")
                break
    
    def stop(self) -> None:
        """停止事件循环"""
        self.running = False
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)
    
    def _check_escape_timeout(self) -> None:
        """检查ESC键是否超时，如果超时则处理为单独的ESC键"""
        import time
        if self._pending_escape:
            current_time = time.time()
            if current_time - self._last_escape_time > self._alt_key_timeout:
                # 超时，处理为单独的ESC键
                self.tui_logger.debug_key_event("escape", True, "timeout_handler")
                self._pending_escape = False
                # 直接调用ESC键处理器，而不是再次进入_process_key
                if "escape" in self.key_handlers:
                    self.key_handlers["escape"]("escape")
                elif self.global_key_handler:
                    self.global_key_handler("escape")
    
    def _input_reader(self) -> None:
        """输入读取线程 - 使用blessed的inkey()方法"""
        try:
            while self.running:
                with self.terminal.cbreak():
                    try:
                        # 使用blessed的inkey()方法，timeout=0表示非阻塞
                        val = self.terminal.inkey(timeout=0.05)
                        if val:
                            # 将blessed的Keystroke对象转换为字符串
                            key_str = self._convert_keystroke_to_string(val)
                            if key_str:
                                self.input_queue.put(key_str)
                    except (UnicodeDecodeError, IOError):
                        # 忽略编码错误，继续读取
                        continue
        except Exception:
            pass
    
    def _convert_keystroke_to_string(self, keystroke) -> str:
        """将blessed的Keystroke对象转换为按键字符串
        
        Args:
            keystroke: blessed的Keystroke对象
            
        Returns:
            str: 按键字符串
        """
        if keystroke.is_sequence:
            # 这是一个序列键（方向键、功能键等）
            if keystroke.name:
                # 使用blessed提供的标准名称
                name = keystroke.name.lower()
                # 特殊处理ESC键
                if name == 'key_escape':
                    return "escape"
                # 特殊处理Alt键组合
                # 在某些终端中，Alt+数字键可能被识别为特定的键名
                if name.startswith('key_') and 'alt' in name.lower():
                    # 尝试提取数字
                    if '1' in name:
                        return "alt_1"
                    elif '2' in name:
                        return "alt_2"
                    elif '3' in name:
                        return "alt_3"
                    elif '4' in name:
                        return "alt_4"
                    elif '5' in name:
                        return "alt_5"
                    elif '6' in name:
                        return "alt_6"
                return name
            else:
                # 如果没有名称，使用code
                return f"key_{keystroke.code}"
        else:
            # 这是一个普通字符
            char = str(keystroke)
            if char == '\r' or char == '\n':
                return "enter"
            elif char == '\t':
                return "tab"
            elif char == '\x7f' or char == '\x08':
                return "backspace"
            elif char == '\x1b':  # ESC字符
                return "escape"
            # 检查是否是Alt+字符的组合，这种情况下字符的ASCII码通常是原始字符+128
            elif len(char) == 1 and 128 <= ord(char) <= 255:
                # 这可能是Alt+字符的组合
                original_char = chr(ord(char) - 128)
                # 对于数字键，转换为alt+数字的格式
                if original_char.isdigit():
                    return f"alt_{original_char}"
                else:
                    return f"alt_{original_char}"
            # 在Windows终端中，Alt+数字键可能直接产生数字字符
            # 但我们无法区分是直接按数字键还是Alt+数字键
            # 所以我们依赖于事件引擎中的特殊处理
            elif len(char) == 1 and char.isdigit():
                # 这里我们暂时不处理，留给事件引擎处理
                return f"char:{char}"
            else:
                return f"char:{char}"
    
    def _process_key(self, key_str: str) -> None:
        """处理按键
        
        Args:
            key_str: 按键字符串
        """
        if not key_str:
            return
        
        # 处理Windows终端中Alt+数字键的特殊逻辑
        # 在Windows终端中，Alt+数字键会产生ESC键+数字键的序列
        if self._pending_escape:
            self._pending_escape = False
            
            # 检查当前按键是否是数字
            if key_str.startswith("char:") and len(key_str) == 6 and key_str[5].isdigit():
                # 构造Alt键组合
                alt_key = f"alt_{key_str[5]}"
                self.tui_logger.debug_key_event(alt_key, False, "alt_key_detected")
                # 检查是否有对应的Alt键处理器
                if alt_key in self.key_handlers:
                    if self.key_handlers[alt_key](alt_key):
                        self.tui_logger.debug_key_event(alt_key, True, "alt_key_handled")
                        return
                # 如果没有处理器，将两个按键分别处理
                # 先处理之前的ESC键
                if "escape" in self.key_handlers:
                    self.key_handlers["escape"]("escape")
                elif self.global_key_handler:
                    self.global_key_handler("escape")
                # 再处理当前的数字键
                if self.input_component_handler:
                    result = self.input_component_handler(key_str)
                    if result is not None and self.input_result_handler:
                        self.input_result_handler(result)
                return
            else:
                # 不是数字键，先处理之前缓存的ESC键
                self.tui_logger.debug_key_event("escape", True, "escape_key_processed")
                if "escape" in self.key_handlers:
                    self.key_handlers["escape"]("escape")
                elif self.global_key_handler:
                    self.global_key_handler("escape")
                # 继续处理当前按键
        
        # 定义应该优先由全局处理器处理的按键（虚拟滚动相关）
        global_priority_keys = {
            "key_up", "key_down", "key_left", "key_right",  # 方向键
            "key_ppage", "key_npage",  # Page Up/Down
            "key_home", "key_end",  # Home/End
            "key_dc", "key_ic",  # Delete/Insert
        }
        
        # 检查是否是ESC键
        if key_str == "escape":
            # 记录ESC键按下的时间
            import time
            current_time = time.time()
            self._last_escape_time = current_time
            self._pending_escape = True
            
            # 在Windows终端中，Alt+数字键会先发送ESC键
            # 我们需要等待下一个按键来判断是否是Alt键组合
            self._pending_alt_key = key_str
            return
        
        # 检查是否以alt开头的组合键
        if key_str.startswith("alt_") or key_str.startswith("key_alt_"):
            # Alt组合键优先由注册的按键处理器处理
            if key_str in self.key_handlers:
                if self.key_handlers[key_str](key_str):
                    return
            
            # 如果注册的处理器没有处理，则继续让全局处理器处理
            if self.global_key_handler:
                self.global_key_handler(key_str)
            return
        
        # 如果是全局优先按键，先让注册的按键处理器处理
        if key_str in global_priority_keys:
            # 处理注册的按键处理器
            if key_str in self.key_handlers:
                if self.key_handlers[key_str](key_str):
                    return
            
            # 最后让全局处理器处理
            if self.global_key_handler:
                self.global_key_handler(key_str)
            return
        
        # 对于其他按键，首先让输入组件处理按键
        if self.input_component_handler:
            result = self.input_component_handler(key_str)
            
            # 如果输入组件返回了结果，处理它
            if result is not None and self.input_result_handler:
                self.input_result_handler(result)
        
        # 处理注册的按键处理器
        if key_str in self.key_handlers:
            if self.key_handlers[key_str](key_str):
                return
        
        # 最后让全局处理器处理
        if self.global_key_handler:
            self.global_key_handler(key_str)