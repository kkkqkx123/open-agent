# TUI键盘处理改进 - 具体实现代码

## Key类实现

```python
# src/presentation/tui/key.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Key:
    """标准化按键对象 - 完全兼容现有字符串处理"""
    name: str                    # 按键名称
    sequence: str               # 原始序列
    ctrl: bool = False         # Ctrl修饰符
    alt: bool = False         # Alt修饰符  
    shift: bool = False      # Shift修饰符
    meta: bool = False       # Meta修饰符
    kitty_protocol: bool = False  # Kitty协议标识
    
    def __str__(self) -> str:
        """返回兼容现有系统的字符串表示"""
        # 优先使用现有字符串格式以保持兼容
        if self.name in ['enter', 'escape', 'tab', 'backspace', 'up', 'down', 'left', 'right']:
            return self.name
        elif self.name.startswith('f') and self.name[1:].isdigit():
            return self.name
        elif self.name.startswith('char:'):
            return self.name
        else:
            # 对于复杂序列，使用现有格式
            return self._to_legacy_format()
    
    def _to_legacy_format(self) -> str:
        """转换为现有系统使用的格式"""
        parts = []
        if self.ctrl:
            parts.append('ctrl')
        if self.alt:
            parts.append('alt')
        if self.shift:
            parts.append('shift')
        if self.meta:
            parts.append('meta')
        
        if parts:
            return '+'.join(parts) + '+' + self.name
        return self.name
    
    def matches(self, name: str, **modifiers) -> bool:
        """检查按键匹配"""
        return (self.name == name and 
                self.ctrl == modifiers.get('ctrl', False) and
                self.alt == modifiers.get('alt', False) and
                self.shift == modifiers.get('shift', False) and
                self.meta == modifiers.get('meta', False))

# 常用按键常量
KEY_ENTER = "enter"
KEY_ESCAPE = "escape"
KEY_TAB = "tab"
KEY_BACKSPACE = "backspace"
KEY_UP = "up"
KEY_DOWN = "down"
KEY_LEFT = "left"
KEY_RIGHT = "right"
```

## 按键解析器实现

```python
# src/presentation/tui/key_parser.py
import re
from typing import Optional, Tuple, Dict
from .key import Key

class KeyParser:
    """按键序列解析器 - 支持多种协议"""
    
    def __init__(self):
        # Kitty协议格式：ESC [ 数字 ; 修饰符 u
        self.kitty_pattern = re.compile(r'^\x1b\[(\d+)(?:;(\d+))?u')
        
        # Kitty协议按键映射
        self.kitty_key_map = {
            13: 'enter', 27: 'escape', 127: 'backspace', 9: 'tab', 32: 'space',
            57417: 'up', 57418: 'down', 57419: 'right', 57420: 'left',
            57428: 'f1', 57429: 'f2', 57430: 'f3', 57431: 'f4',
            57432: 'f5', 57433: 'f6', 57434: 'f7', 57435: 'f8',
            57436: 'f9', 57437: 'f10', 57438: 'f11', 57439: 'f12',
        }
        
        # 传统Escape序列映射
        self.escape_sequences = {
            '\x1b[A': ('up', False, False, False, False),
            '\x1b[B': ('down', False, False, False, False),
            '\x1b[C': ('right', False, False, False, False),
            '\x1b[D': ('left', False, False, False, False),
            '\x1b[H': ('home', False, False, False, False),
            '\x1b[F': ('end', False, False, False, False),
            '\x1b[5~': ('page_up', False, False, False, False),
            '\x1b[6~': ('page_down', False, False, False, False),
            '\x1b[3~': ('delete', False, False, False, False),
            '\x1bOP': ('f1', False, False, False, False),
            '\x1bOQ': ('f2', False, False, False, False),
            '\x1bOR': ('f3', False, False, False, False),
            '\x1bOS': ('f4', False, False, False, False),
        }
        
        # 修饰符位标志
        self.MODIFIER_SHIFT = 0x01
        self.MODIFIER_ALT = 0x02
        self.MODIFIER_CTRL = 0x04
        self.MODIFIER_META = 0x08
    
    def parse_sequence(self, sequence: str) -> Optional[Tuple[Key, int]]:
        """解析按键序列"""
        if not sequence:
            return None
        
        # 1. 尝试Kitty协议
        kitty_result = self._parse_kitty_sequence(sequence)
        if kitty_result:
            return kitty_result
        
        # 2. 尝试传统Escape序列
        escape_result = self._parse_escape_sequence(sequence)
        if escape_result:
            return escape_result
        
        # 3. 单字符处理
        if len(sequence) == 1:
            return self._parse_single_char(sequence)
        
        return None
    
    def _parse_kitty_sequence(self, sequence: str) -> Optional[Tuple[Key, int]]:
        """解析Kitty协议序列"""
        match = self.kitty_pattern.match(sequence)
        if not match:
            return None
            
        key_code = int(match.group(1))
        modifiers = int(match.group(2)) if match.group(2) else 0
        consumed_length = len(match.group(0))
        
        # 获取按键名称
        key_name = self.kitty_key_map.get(key_code)
        if key_name is None:
            # 尝试作为ASCII字符处理
            if 0 <= key_code <= 127:
                if key_code == 32:
                    key_name = 'space'
                elif key_code == 127:
                    key_name = 'backspace'
                elif 0 <= key_code <= 31:
                    key_name = chr(key_code + 64).lower()
                else:
                    key_name = f'char:{chr(key_code)}'
            else:
                key_name = f'unknown_{key_code}'
        
        return Key(
            name=key_name,
            sequence=match.group(0),
            ctrl=bool(modifiers & self.MODIFIER_CTRL),
            alt=bool(modifiers & self.MODIFIER_ALT),
            shift=bool(modifiers & self.MODIFIER_SHIFT),
            meta=bool(modifiers & self.MODIFIER_META),
            kitty_protocol=True
        ), consumed_length
    
    def _parse_escape_sequence(self, sequence: str) -> Optional[Tuple[Key, int]]:
        """解析Escape序列"""
        # 检查完全匹配的序列
        for esc_seq, (name, ctrl, alt, shift, meta) in self.escape_sequences.items():
            if sequence.startswith(esc_seq):
                return Key(
                    name=name,
                    sequence=esc_seq,
                    ctrl=ctrl,
                    alt=alt,
                    shift=shift,
                    meta=meta,
                    kitty_protocol=False
                ), len(esc_seq)
        
        # 处理其他CSI序列
        if sequence.startswith('\x1b['):
            return self._parse_csi_sequence(sequence)
            
        return None
    
    def _parse_csi_sequence(self, sequence: str) -> Optional[Tuple[Key, int]]:
        """解析CSI序列"""
        if len(sequence) < 4:
            return None
            
        # 查找序列结束
        end_pos = 3
        while end_pos < len(sequence) and (sequence[end_pos].isdigit() or sequence[end_pos] == ';'):
            end_pos += 1
            
        if end_pos >= len(sequence):
            return None
            
        terminator = sequence[end_pos]
        full_sequence = sequence[:end_pos + 1]
        
        # 基本的CSI映射
        csi_map = {'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left', 'H': 'home', 'F': 'end'}
        
        if terminator in csi_map:
            return Key(
                name=csi_map[terminator],
                sequence=full_sequence,
                kitty_protocol=False
            ), len(full_sequence)
            
        return None
    
    def _parse_single_char(self, sequence: str) -> Optional[Tuple[Key, int]]:
        """解析单字符"""
        char = sequence[0]
        
        # 控制字符处理
        if char == '\x1b':
            key_name = 'escape'
        elif char == '\r':
            key_name = 'enter'
        elif char == '\t':
            key_name = 'tab'
        elif char == '\x7f':
            key_name = 'backspace'
        elif char == ' ':
            key_name = 'space'
        elif 0 <= ord(char) <= 31:
            key_name = chr(ord(char) + 64).lower()
        else:
            key_name = f'char:{char}'
        
        return Key(
            name=key_name,
            sequence=sequence,
            kitty_protocol=False
        ), 1
```

## 增强的事件引擎

```python
# src/presentation/tui/event_engine.py（增强版）
import sys
import threading
import time
import queue
from typing import Optional, Callable, Dict, Any, Union
from blessed import Terminal

# 新增导入
from .key import Key
from .key_parser import KeyParser

class EventEngine:
    """增强的事件处理引擎 - 支持Key对象和调试"""
    
    def __init__(self, terminal: Terminal, config: Any) -> None:
        """初始化事件引擎"""
        self.terminal = terminal
        self.config = config
        self.running = False
        self.input_queue = queue.Queue()
        self.input_thread: Optional[threading.Thread] = None
        
        # 事件处理器 - 支持字符串和Key对象
        self.key_handlers: Dict[str, Callable[[Union[str, Key]], bool]] = {}
        self.global_key_handler: Optional[Callable[[Union[str, Key]], bool]] = None
        
        # 输入组件处理器
        self.input_component_handler: Optional[Callable[[str], Optional[str]]] = None
        self.input_result_handler: Optional[Callable[[str], None]] = None
        
        # 新增：按键解析器
        self.key_parser = KeyParser()
        self._enable_enhanced_keys = getattr(config, 'enhanced_keyboard_support', True)
        self._debug_key_sequences = getattr(config, 'debug_key_sequences', False)
        
        # 新增：按键序列处理
        self._key_buffer = ""
        self._max_sequence_length = 16
        
        # 新增：调试支持
        if self._debug_key_sequences:
            from .debug.sequence_monitor import SequenceMonitor
            self.sequence_monitor = SequenceMonitor()
        
        # 初始化TUI调试日志记录器
        self.tui_logger = get_tui_silent_logger("event_engine")
        
        # 保持现有逻辑
        self._pending_alt_key: Optional[str] = None
        self._alt_key_timeout: float = 0.1
        self._last_escape_time: float = 0.0
        self._pending_escape: bool = False
    
    def _process_key(self, key_str: str) -> None:
        """处理按键输入（增强版）"""
        if not key_str:
            return
        
        # 如果启用了增强按键支持，尝试解析为Key对象
        if self._enable_enhanced_keys:
            key = self._parse_key_input(key_str)
            if key:
                # 记录调试信息
                if self._debug_key_sequences and hasattr(self, 'sequence_monitor'):
                    self.sequence_monitor.add_sequence(key.sequence, str(key))
                
                # 使用Key对象处理
                self._handle_key_with_object(key)
                return
        
        # 回退到传统字符串处理
        self._handle_key_with_string(key_str)
    
    def _parse_key_input(self, key_str: str) -> Optional[Key]:
        """解析按键输入为Key对象"""
        # 添加到序列缓冲区
        self._key_buffer += key_str
        
        # 尝试解析完整的按键序列
        result = self.key_parser.parse_sequence(self._key_buffer)
        if result:
            key, consumed_length = result
            self._key_buffer = self._key_buffer[consumed_length:]
            return key
        
        # 如果缓冲区过长，清空并返回原始字符串
        if len(self._key_buffer) > self._max_sequence_length:
            self._key_buffer = ""
            return None
        
        return None
    
    def _handle_key_with_object(self, key: Key) -> None:
        """使用Key对象处理按键"""
        # 记录按键事件
        self.tui_logger.debug_key_event(key, True, "key_object_handler")
        
        # 转换为字符串以保持兼容
        key_str = str(key)
        
        # 使用现有的处理逻辑
        self._handle_key_with_string(key_str, key)
    
    def _handle_key_with_string(self, key_str: str, key_obj: Optional[Key] = None) -> None:
        """使用字符串处理按键（增强版）"""
        # 记录按键事件
        self.tui_logger.debug_key_event(key_str, True, "string_handler")
        
        # 检查ESC键超时逻辑（保持现有逻辑）
        if key_str == "escape":
            self._pending_escape = True
            self._last_escape_time = time.time()
            return
        
        # 处理全局按键处理器
        if self.global_key_handler:
            # 优先传递Key对象（如果可用）
            handler_arg = key_obj if key_obj else key_str
            if self.global_key_handler(handler_arg):
                return
        
        # 处理特定按键处理器
        if key_str in self.key_handlers:
            # 优先传递Key对象（如果可用）
            handler_arg = key_obj if key_obj else key_str
            self.key_handlers[key_str](handler_arg)
    
    # 保持其他方法不变，但添加Key对象支持
    def register_key_handler(self, key: str, handler: Callable[[Union[str, Key]], bool]) -> None:
        """注册按键处理器 - 支持字符串和Key对象"""
        self.key_handlers[key] = handler
    
    def set_global_key_handler(self, handler: Callable[[Union[str, Key]], bool]) -> None:
        """设置全局按键处理器 - 支持字符串和Key对象"""
        self.global_key_handler = handler
    
    # 新增调试方法
    def enable_sequence_debugging(self, enabled: bool = True) -> None:
        """启用按键序列调试"""
        self._debug_key_sequences = enabled
        if enabled and not hasattr(self, 'sequence_monitor'):
            from .debug.sequence_monitor import SequenceMonitor
            self.sequence_monitor = SequenceMonitor()
    
    def get_sequence_statistics(self) -> Optional[Dict[str, Any]]:
        """获取按键序列统计"""
        if hasattr(self, 'sequence_monitor'):
            return self.sequence_monitor.get_statistics()
        return None
    
    # 保持现有方法不变...
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
                if "codec" not in str(e) and "decode" not in str(e):
                    print(f"事件循环错误: {e}")
                break
```

## 序列监控器实现

```python
# src/presentation/tui/debug/sequence_monitor.py
import time
from typing import List, Dict, Any, Optional
from collections import defaultdict

class SequenceMonitor:
    """按键序列监控器"""
    
    def __init__(self, max_history: int = 100):
        self.sequences: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.start_time = time.time()
        self.sequence_counts = defaultdict(int)
        self.total_sequences = 0
        self.total_bytes = 0
    
    def add_sequence(self, sequence: str, parsed_key: Optional[str] = None) -> None:
        """添加按键序列"""
        entry = {
            'timestamp': time.time() - self.start_time,
            'sequence': repr(sequence),
            'parsed_key': parsed_key,
            'length': len(sequence),
            'bytes': len(sequence.encode('utf-8'))
        }
        self.sequences.append(entry)
        self.sequence_counts[sequence] += 1
        self.total_sequences += 1
        self.total_bytes += entry['bytes']
        
        # 保持最近的历史记录
        if len(self.sequences) > self.max_history:
            removed = self.sequences.pop(0)
            self.sequence_counts[removed['sequence']] -= 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取序列统计信息"""
        if not self.sequences:
            return {}
            
        unique_sequences = len([k for k, v in self.sequence_counts.items() if v > 0])
        avg_length = self.total_bytes / self.total_sequences if self.total_sequences > 0 else 0
        
        return {
            'total_sequences': self.total_sequences,
            'unique_sequences': unique_sequences,
            'average_length': avg_length,
            'time_span': self.sequences[-1]['timestamp'] - self.sequences[0]['timestamp'] if self.sequences else 0,
            'sequences_per_second': self.total_sequences / (time.time() - self.start_time) if self.total_sequences > 0 else 0
        }
    
    def print_recent(self, count: int = 10) -> None:
        """打印最近的序列"""
        recent = self.sequences[-count:] if len(self.sequences) > count else self.sequences
        for seq in recent:
            print(f"{seq['timestamp']:.3f}s: {seq['sequence']} -> {seq['parsed_key']}")
    
    def get_top_sequences(self, count: int = 5) -> List[tuple]:
        """获取最常用的序列"""
        sorted_sequences = sorted(self.sequence_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_sequences[:count]
```

## 配置增强

```python
# src/presentation/tui/config.py（增强部分）
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class TUIConfig:
    """TUI配置类 - 增强键盘支持"""
    
    # 现有配置...
    
    # 新增：键盘配置
    enhanced_keyboard_support: bool = True      # 启用增强按键支持
    debug_key_sequences: bool = False          # 调试按键序列
    enable_kitty_protocol: bool = True       # 启用Kitty协议支持
    max_sequence_length: int = 16            # 最大序列长度
    alt_key_timeout: float = 0.1             # Alt键超时时间（秒）
    
    # 按键映射配置
    key_mappings: Dict[str, str] = field(default_factory=lambda: {
        'ctrl+c': 'quit',
        'ctrl+q': 'quit',
        'ctrl+h': 'help',
        'ctrl+r': 'refresh',
    })
```

## 使用示例

### 现有代码兼容使用
```python
# 现有代码无需修改
def handle_enter(key_str: str) -> bool:
    if key_str == "enter":
        print("Enter pressed")
        return True
    return False

event_engine.register_key_handler("enter", handle_enter)
```

### 新代码使用Key对象
```python
# 新代码可以使用Key对象
def handle_ctrl_enter(key: Union[str, Key]) -> bool:
    if isinstance(key, Key) and key.matches("enter", ctrl=True):
        print("Ctrl+Enter pressed")
        return True
    elif isinstance(key, str) and key == "enter":
        # 向后兼容
        print("Enter pressed")
        return True
    return False

event_engine.register_key_handler("enter", handle_ctrl_enter)
```

### 调试使用
```python
# 启用调试模式
config = TUIConfig(
    enhanced_keyboard_support=True,
    debug_key_sequences=True,
    enable_kitty_protocol=True
)

# 在应用中查看统计信息
stats = event_engine.get_sequence_statistics()
if stats:
    print(f"总按键数: {stats['total_sequences']}")
    print(f"平均长度: {stats['average_length']:.1f}字节")
    print(f"按键频率: {stats['sequences_per_second']:.1f}/秒")
```

## 测试代码

```python
# tests/test_key_parser.py
import pytest
from src.presentation.tui.key_parser import KeyParser
from src.presentation.tui.key import Key

def test_kitty_protocol_parsing():
    """测试Kitty协议解析"""
    parser = KeyParser()
    
    # 测试基本按键
    result = parser.parse_sequence('\x1b[13u')  # Enter
    assert result is not None
    key, length = result
    assert key.name == 'enter'
    assert not key.ctrl
    assert length == 5
    
    # 测试带修饰符的按键
    result = parser.parse_sequence('\x1b[13;5u')  # Ctrl+Enter
    assert result is not None
    key, length = result
    assert key.name == 'enter'
    assert key.ctrl
    assert length == 7

def test_escape_sequence_parsing():
    """测试Escape序列解析"""
    parser = KeyParser()
    
    # 测试方向键
    result = parser.parse_sequence('\x1b[A')  # Up
    assert result is not None
    key, length = result
    assert key.name == 'up'
    assert length == 3

def test_single_char_parsing():
    """测试单字符解析"""
    parser = KeyParser()
    
    # 测试普通字符
    result = parser.parse_sequence('a')
    assert result is not None
    key, length = result
    assert key.name == 'char:a'
    assert length == 1
    
    # 测试控制字符
    result = parser.parse_sequence('\x1b')  # Escape
    assert result is not None
    key, length = result
    assert key.name == 'escape'
    assert length == 1

def test_key_string_conversion():
    """测试Key对象字符串转换"""
    # 测试基本按键
    key = Key(name='enter', sequence='\r')
    assert str(key) == 'enter'
    
    # 测试带修饰符的按键
    key = Key(name='enter', sequence='\x1b[13;5u', ctrl=True, kitty_protocol=True)
    assert str(key) == 'ctrl+enter'
    
    # 测试字符按键
    key = Key(name='char:a', sequence='a')
    assert str(key) == 'char:a'
```

这个实现提供了完整的TUI键盘处理改进方案，保持了与现有代码的完全兼容性，同时提供了现代化的键盘处理能力。