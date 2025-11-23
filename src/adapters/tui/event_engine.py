"""
TUI事件引擎 - 重构版本

提供统一的按键事件处理机制，支持Key对象和增强的按键识别
"""

import threading
import queue
import time
from typing import Dict, Callable, Optional, Any, List
from blessed import Terminal

from .key import Key, KeyType, KeyModifier, KeyParser, KEY_ENTER, KEY_ESCAPE
from .config import TUIConfig


class KeySequenceBuffer:
    """按键序列缓冲区
    
    处理按键序列，如ESC序列、Alt键组合等
    """
    
    def __init__(self, timeout: float = 0.1):
        """初始化按键序列缓冲区
        
        Args:
            timeout: 序列超时时间（秒）
        """
        self.timeout = timeout
        self.buffer: List[Key] = []
        self.last_key_time = 0.0
        self.pending_escape = False
        self.escape_start_time = 0.0
    
    def add_key(self, key: Key) -> bool:
        """添加按键到缓冲区
        
        Args:
            key: 按键对象
            
        Returns:
            如果缓冲区准备好处理则返回True
        """
        current_time = time.time()
        
        # 检查是否是ESC键
        if key == KEY_ESCAPE:
            self.pending_escape = True
            self.escape_start_time = current_time
            self.buffer.append(key)
            return False  # 需要等待后续按键
        
        # 如果有待处理的ESC键
        if self.pending_escape:
            # 检查是否超时
            if current_time - self.escape_start_time > self.timeout:
                # ESC键超时，处理为单独的ESC键
                self.pending_escape = False
                return True  # 缓冲区准备好
            
            # 在超时时间内收到按键，可能是Alt组合
            self.buffer.append(key)
            self.pending_escape = False
            return True  # 缓冲区准备好
        
        # 普通按键，直接处理
        self.buffer.append(key)
        self.last_key_time = current_time
        return True
    
    def get_sequence(self) -> Optional[List[Key]]:
        """获取按键序列
        
        Returns:
            按键序列，如果没有准备好的序列则返回None
        """
        if not self.buffer:
            return None
        
        current_time = time.time()
        
        # 检查ESC键超时
        if self.pending_escape:
            if current_time - self.escape_start_time > self.timeout:
                # ESC键超时，返回单独的ESC键
                self.pending_escape = False
                escape_key = self.buffer[0]
                self.buffer.clear()
                return [escape_key]
        
        # 检查普通按键超时
        if self.buffer and current_time - self.last_key_time > self.timeout:
            sequence = self.buffer.copy()
            self.buffer.clear()
            return sequence
        
        # 如果有完整的序列（ESC+后续键）
        if len(self.buffer) >= 2 and self.buffer[0] == KEY_ESCAPE:
            sequence = self.buffer.copy()
            self.buffer.clear()
            return sequence
        
        return None
    
    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()
        self.pending_escape = False
        self.last_key_time = 0.0
        self.escape_start_time = 0.0


class EventEngine:
    """TUI事件引擎
    
    统一处理键盘输入事件，支持Key对象和增强的按键识别
    """
    
    def __init__(self, terminal: Terminal, config: Optional[Any] = None):
        """初始化事件引擎

        Args:
            terminal: blessed终端对象
            config: 配置选项 (TUIConfig 或 Dict[str, Any])
        """
        self.terminal = terminal

        # 处理配置参数
        if isinstance(config, TUIConfig):
            self.config_obj = config
            self.config_dict = config.to_dict()
        elif isinstance(config, dict):
            self.config_obj = None
            self.config_dict = config
        else:
            self.config_obj = None
            self.config_dict = {}

        # 按键处理器
        self.key_handlers: Dict[str, Callable[[Key], bool]] = {}
        self.global_key_handler: Optional[Callable[[Key], bool]] = None
        self.input_component_handler: Optional[Callable[[Key], Any]] = None
        self.input_result_handler: Optional[Callable[[Any], None]] = None

        # 输入队列和线程
        self.input_queue = queue.Queue()
        self.running = False
        self.input_thread: Optional[threading.Thread] = None
        self.processing_thread: Optional[threading.Thread] = None

        # 按键序列缓冲区
        key_sequence_timeout = self._get_config_value('key_sequence_timeout', 0.1)
        self.sequence_buffer = KeySequenceBuffer(timeout=key_sequence_timeout)

        # 调试和监控
        self.debug_enabled = self._get_config_value('debug_keyboard', False)
        self.key_stats = {
            'total_keys': 0,
            'sequence_detected': 0,
            'alt_combinations': 0,
            'errors': 0
        }

        # 序列监控器
        self.sequence_monitor = None
        if self._get_keyboard_config_value('debug_key_sequences', False):
            from .debug.sequence_monitor import SequenceMonitor
            self.sequence_monitor = SequenceMonitor()
        
        # 获取TUI日志记录器
        from .logger import get_tui_silent_logger
        self.tui_logger = get_tui_silent_logger("event_engine")

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self.config_dict.get(key, default)

    def _get_keyboard_config_value(self, key: str, default: Any = None) -> Any:
        """获取键盘配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        keyboard_config = self.config_dict.get('keyboard', {})
        return keyboard_config.get(key, default)
    
    def register_key_handler(self, key: Key, handler: Callable[[Key], bool]) -> None:
        """注册按键处理器
        
        Args:
            key: 按键对象
            handler: 处理器函数，返回True表示已处理
        """
        key_str = key.to_string()
        self.key_handlers[key_str] = handler
        if self.debug_enabled:
            self.tui_logger.debug(f"Registered key handler: {key_str}")
    
    def unregister_key_handler(self, key: Key) -> None:
        """取消注册按键处理器
        
        Args:
            key: 按键对象
        """
        key_str = key.to_string()
        if key_str in self.key_handlers:
            del self.key_handlers[key_str]
            if self.debug_enabled:
                self.tui_logger.debug(f"Unregistered key handler: {key_str}")
    
    def set_global_key_handler(self, handler: Callable[[Key], bool]) -> None:
        """设置全局按键处理器
        
        Args:
            handler: 全局处理器函数，返回True表示已处理
        """
        self.global_key_handler = handler
    
    def set_input_component_handler(self, handler: Callable[[Key], Any]) -> None:
        """设置输入组件处理器
        
        Args:
            handler: 输入组件处理器函数
        """
        self.input_component_handler = handler
    
    def set_input_result_handler(self, handler: Callable[[Any], None]) -> None:
        """设置输入结果处理器
        
        Args:
            handler: 输入结果处理器函数
        """
        self.input_result_handler = handler
    
    def start(self) -> None:
        """启动事件引擎"""
        if self.running:
            return
        
        self.running = True
        self.input_thread = threading.Thread(target=self._input_reader, daemon=True)
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        
        self.input_thread.start()
        self.processing_thread.start()
        
        if self.debug_enabled:
            self.tui_logger.debug("Event engine started")
    
    def stop(self) -> None:
        """停止事件引擎"""
        if not self.running:
            return
        
        self.running = False
        
        # 清空队列
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except queue.Empty:
                break
        
        # 等待线程结束
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        
        # 保存序列监控数据
        if self.sequence_monitor:
            # 导出数据到文件 (需要实现保存逻辑)
            import json
            data = self.sequence_monitor.export_data()
            with open('key_sequences.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        if self.debug_enabled:
            self.tui_logger.debug("Event engine stopped")
            self._log_statistics()

            # 打印序列监控结果
            if self.sequence_monitor:
                self.tui_logger.info("Key sequence statistics:")
                self.sequence_monitor.print_recent(count=20)

                # 显示常用序列
                common_sequences = self.sequence_monitor.get_top_sequences(count=10)
                if common_sequences:
                    self.tui_logger.info("Most common sequences:")
                    for seq, count in common_sequences:
                        self.tui_logger.info(f"  {seq}: {count} times")
    
    def _input_reader(self) -> None:
        """输入读取线程"""
        try:
            while self.running:
                with self.terminal.cbreak():
                    try:
                        # 使用blessed的inkey()方法
                        val = self.terminal.inkey(timeout=0.05)
                        if val:
                            # 记录原始按键序列
                            raw_sequence = str(val)
                            
                            # 转换为Key对象
                            key = KeyParser.from_blessed_keystroke(val)
                            if key:
                                self.input_queue.put(key)
                                
                                # 记录到序列监控器
                                if self.sequence_monitor:
                                    self.sequence_monitor.add_sequence(raw_sequence, key.to_string())
                                
                                # 增强按键支持
                                if self._get_keyboard_config_value('enhanced_keyboard_support', True):
                                    # 处理增强按键功能
                                    pass

                                # Kitty键盘协议支持
                                if self._get_keyboard_config_value('enable_kitty_protocol', True):
                                    # 处理Kitty协议
                                    pass
                                
                                if self.debug_enabled:
                                    self.tui_logger.debug(f"Key detected: {key}")
                    except (UnicodeDecodeError, IOError):
                        # 忽略编码错误
                        continue
                    except Exception as e:
                        if self.debug_enabled:
                            self.tui_logger.error(f"Input reader error: {e}")
                        self.key_stats['errors'] += 1
        except Exception as e:
            if self.debug_enabled:
                self.tui_logger.error(f"Input reader thread error: {e}")
    
    def _processing_loop(self) -> None:
        """按键处理主循环"""
        try:
            while self.running:
                try:
                    # 从队列获取按键
                    key = self.input_queue.get(timeout=0.1)
                    self.key_stats['total_keys'] += 1
                    
                    # 添加到序列缓冲区
                    ready = self.sequence_buffer.add_key(key)
                    
                    if ready:
                        # 获取处理序列
                        sequence = self.sequence_buffer.get_sequence()
                        if sequence:
                            self._process_sequence(sequence)
                    
                except queue.Empty:
                    # 检查缓冲区超时
                    sequence = self.sequence_buffer.get_sequence()
                    if sequence:
                        self._process_sequence(sequence)
                    continue
                    
        except Exception as e:
            if self.debug_enabled:
                self.tui_logger.error(f"Processing loop error: {e}")
    
    def _process_sequence(self, sequence: List[Key]) -> None:
        """处理按键序列
        
        Args:
            sequence: 按键序列
        """
        if self.debug_enabled:
            self.tui_logger.debug(f"Processing sequence: {[str(k) for k in sequence]}")
        
        # 处理Alt键组合 (ESC + 字符)
        if len(sequence) == 2 and sequence[0] == KEY_ESCAPE:
            second_key = sequence[1]
            if second_key.key_type == KeyType.CHARACTER:
                # 创建Alt组合键
                alt_key = Key(
                    name=second_key.name,
                    key_type=second_key.key_type,
                    modifiers=KeyModifier.ALT.value,
                    raw_sequence=f"\x1b{second_key.name}"
                )
                self._process_key(alt_key)
                self.key_stats['alt_combinations'] += 1
                return
        
        # 处理ESC键超时
        if len(sequence) == 1 and sequence[0] == KEY_ESCAPE:
            self._process_key(KEY_ESCAPE)
            return
        
        # 处理普通序列
        for key in sequence:
            self._process_key(key)
    
    def _process_key(self, key: Key) -> None:
        """处理单个按键
        
        Args:
            key: 按键对象
        """
        if self.debug_enabled:
            self.tui_logger.debug_key_event(key.to_string(), False, "key_processing")
        
        # 定义全局优先按键
        global_priority_keys = {
            'up', 'down', 'left', 'right',
            'page_up', 'page_down', 'home', 'end',
            'delete', 'insert'
        }
        
        handled = False
        key_str = key.to_string()
        
        # 处理注册的按键处理器
        if key_str in self.key_handlers:
            if self.key_handlers[key_str](key):
                handled = True
        
        # 处理全局优先按键
        if not handled and key.name in global_priority_keys:
            if self.global_key_handler:
                if self.global_key_handler(key):
                    handled = True
        
        # 处理输入组件
        if not handled and self.input_component_handler:
            result = self.input_component_handler(key)
            if result is not None and self.input_result_handler:
                self.input_result_handler(result)
                handled = True
        
        # 最后处理全局处理器
        if not handled and self.global_key_handler:
            if self.global_key_handler(key):
                handled = True
        
        if self.debug_enabled:
            self.tui_logger.debug_key_event(key.to_string(), handled, "key_processed")
    
    def _log_statistics(self) -> None:
        """记录统计信息"""
        if self.debug_enabled:
            self.tui_logger.info(f"Key statistics: {self.key_stats}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        stats: Dict[str, Any] = dict(self.key_stats)

        # 添加序列监控统计
        if self.sequence_monitor:
            stats['sequence_stats'] = self.sequence_monitor.get_statistics()

        return stats
    
    def clear_statistics(self) -> None:
        """清空统计信息"""
        self.key_stats = {
            'total_keys': 0,
            'sequence_detected': 0,
            'alt_combinations': 0,
            'errors': 0
        }
        
        # 清除序列监控统计
        if self.sequence_monitor:
            self.sequence_monitor.clear()