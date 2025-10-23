"""TUI事件处理引擎"""

import sys
import threading
import time
import queue
from typing import Optional, Callable, Dict, Any
from blessed import Terminal


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
    
    def _input_reader(self) -> None:
        """输入读取线程"""
        try:
            while self.running:
                with self.terminal.cbreak():
                    try:
                        # 读取单个字符
                        char = sys.stdin.read(1)
                        if char:
                            self.input_queue.put(char)
                    except (UnicodeDecodeError, IOError):
                        # 忽略编码错误，继续读取
                        continue
        except Exception:
            pass
    
    def _process_key(self, key_str: str) -> None:
        """处理按键
        
        Args:
            key_str: 按键字符串
        """
        # 处理特殊字符和序列
        processed_key = self._convert_key_sequence(key_str)
        if not processed_key:
            return
        
        # 首先让输入组件处理按键
        if self.input_component_handler:
            result = self.input_component_handler(processed_key)
            
            # 如果输入组件返回了结果，处理它
            if result is not None and self.input_result_handler:
                self.input_result_handler(result)
        
        # 处理注册的按键处理器
        if processed_key in self.key_handlers:
            if self.key_handlers[processed_key](processed_key):
                return
        
        # 最后让全局处理器处理
        if self.global_key_handler:
            self.global_key_handler(processed_key)
    
    def _convert_key_sequence(self, char: str) -> str:
        """将字符转换为按键字符串
        
        Args:
            char: 输入字符
            
        Returns:
            str: 按键字符串
        """
        # 处理特殊字符
        if char == '\x1b':  # ESC
            return "escape"
        elif char == '\x0d':  # Enter (CR)
            return "enter"
        elif char == '\n':  # Enter (LF)
            return "enter"
        elif char == '\x7f':  # Backspace
            return "backspace"
        elif char == '\x09':  # Tab
            return "tab"
        
        # 尝试读取ESC序列
        if char == '\x1b':
            try:
                if not self.input_queue.empty():
                    next_char = self.input_queue.get_nowait()
                    if next_char == '[':
                        # 方向键序列
                        if not self.input_queue.empty():
                            direction = self.input_queue.get_nowait()
                            if direction == 'A':
                                return "up"
                            elif direction == 'B':
                                return "down"
                            elif direction == 'C':
                                return "right"
                            elif direction == 'D':
                                return "left"
            except queue.Empty:
                return "escape"
        
        # 普通字符（包括中文）
        return f"char:{char}"