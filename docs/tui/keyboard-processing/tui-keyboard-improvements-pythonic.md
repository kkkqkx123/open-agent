# TUI键盘处理改进方案（Python简洁版）

## 改进目标

基于gemini-cli项目的优秀实践，为open-agent项目设计一个简洁实用的TUI键盘处理系统，重点聚焦四个核心方面：

1. **标准化Key对象系统** - 替代字符串处理，提供类型安全和丰富功能
2. **Kitty键盘协议支持** - 支持现代终端的高级按键功能  
3. **分层架构设计** - 清晰的职责分离，提高可维护性
4. **增强调试工具** - 实时监控、序列分析、性能统计

## 核心设计原则

- **简洁性**：保持Pythonic风格，避免过度设计
- **兼容性**：完全向后兼容现有代码
- **可测试性**：每个组件都可以独立测试
- **性能优先**：最小化性能开销

---

## 1. 标准化Key对象系统

### Key类设计

```python
# src/presentation/tui/key.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Key:
    """标准化按键对象
    
    提供统一的按键表示，支持复杂的修饰符组合和
    现代终端协议。
    """
    name: str                    # 按键名称（如 'enter', 'tab', 'f1'）
    sequence: str                # 原始按键序列
    ctrl: bool = False          # Ctrl修饰符
    alt: bool = False          # Alt修饰符  
    shift: bool = False       # Shift修饰符
    meta: bool = False        # Meta修饰符（Windows/Cmd键）
    kitty_protocol: bool = False  # 是否来自Kitty协议
    
    def __str__(self) -> str:
        """返回按键的字符串表示"""
        modifiers = []
        if self.ctrl:
            modifiers.append('Ctrl')
        if self.alt:
            modifiers.append('Alt')
        if self.shift:
            modifiers.append('Shift')
        if self.meta:
            modifiers.append('Meta')
            
        mod_str = '+'.join(modifiers) + '+' if modifiers else ''
        return f"{mod_str}{self.name}"
    
    def matches(self, name: str, ctrl: bool = False, alt: bool = False, 
                shift: bool = False, meta: bool = False) -> bool:
        """检查按键是否匹配指定条件"""
        return (self.name == name and 
                self.ctrl == ctrl and 
                self.alt == alt and 
                self.shift == shift and 
                self.meta == meta)

# 常用按键常量
KEY_ENTER = "enter"
KEY_ESCAPE = "escape"
KEY_TAB = "tab"
KEY_BACKSPACE = "backspace"
KEY_UP = "up"
KEY_DOWN = "down"
KEY_LEFT = "left"
KEY_RIGHT = "right"

# 功能键常量
KEY_F1 = "f1"
KEY_F2 = "f2"
# ... 更多功能键
```

### 使用示例

```python
# 传统方式（字符串）
def handle_key_old(key_str: str) -> bool:
    if key_str == "ctrl+enter":
        print("Submit form")
        return True
    return False

# 新方式（Key对象）
def handle_key_new(key: Key) -> bool:
    if key.matches(KEY_ENTER, ctrl=True):
        print("Submit form")
        return True
    return False

# 混合使用（向后兼容）
def handle_key_mixed(key_input) -> bool:
    if isinstance(key_input, Key):
        return handle_key_new(key_input)
    else:
        return handle_key_old(key_input)
```

---

## 2. Kitty键盘协议支持

### Kitty协议解析器

```python
# src/presentation/tui/kitty_parser.py
import re
from typing import Optional, Tuple
from .key import Key

class KittyProtocolParser:
    """Kitty键盘协议解析器
    
    支持Kitty终端的扩展键盘协议，格式为：
    \\x1b[数字;修饰符u
    """
    
    # Kitty协议格式：ESC [ 数字 ; 修饰符 u
    KITTY_PATTERN = re.compile(r'^\x1b\[(\d+)(?:;(\d+))?u')
    
    # Kitty协议按键码映射
    KITTY_KEY_MAP = {
        13: 'enter',
        27: 'escape',
        127: 'backspace',
        9: 'tab',
        32: 'space',
        # 方向键
        57417: 'up',
        57418: 'down', 
        57419: 'right',
        57420: 'left',
        # 功能键 F1-F12
        57428: 'f1',
        57429: 'f2',
        57430: 'f3',
        57431: 'f4',
        57432: 'f5',
        57433: 'f6',
        57434: 'f7',
        57435: 'f8',
        57436: 'f9',
        57437: 'f10',
        57438: 'f11',
        57439: 'f12',
    }
    
    # 修饰符位标志
    MODIFIER_SHIFT = 0x01
    MODIFIER_ALT = 0x02
    MODIFIER_CTRL = 0x04
    MODIFIER_META = 0x08
    
    def parse_sequence(self, sequence: str) -> Optional[Tuple[Key, int]]:
        """解析Kitty协议序列
        
        Returns:
            (Key, consumed_length) 或 None
        """
        match = self.KITTY_PATTERN.match(sequence)
        if not match:
            return None
            
        key_code = int(match.group(1))
        modifiers = int(match.group(2)) if match.group(2) else 0
        consumed_length = len(match.group(0))
        
        # 获取按键名称
        key_name = self.KITTY_KEY_MAP.get(key_code)
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
    
    def is_kitty_sequence(self, sequence: str) -> bool:
        """检查是否为Kitty协议序列"""
        return self.KITTY_PATTERN.match(sequence) is not None
```

### 传统Escape序列解析器

```python
# src/presentation/tui/escape_parser.py
from typing import Optional, Tuple
from .key import Key

class EscapeSequenceParser:
    """传统Escape序列解析器"""
    
    # 常见Escape序列映射
    ESCAPE_SEQUENCES = {
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
    
    def parse_sequence(self, sequence: str) -> Optional[Tuple[Key, int]]:
        """解析Escape序列"""
        # 检查完全匹配的序列
        for esc_seq, (name, ctrl, alt, shift, meta) in self.ESCAPE_SEQUENCES.items():
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
        # 简化实现，实际可以更完整
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
        csi_map = {
            'A': 'up',
            'B': 'down',
            'C': 'right',
            'D': 'left',
            'H': 'home',
            'F': 'end',
        }
        
        if terminator in csi_map:
            return Key(
                name=csi_map[terminator],
                sequence=full_sequence,
                kitty_protocol=False
            ), len(full_sequence)
            
        return None
    
    def is_escape_sequence(self, sequence: str) -> bool:
        """检查是否为Escape序列"""
        return sequence.startswith('\x1b')
```

---

## 3. 分层架构设计

### 架构层次

```
┌─────────────────────────────────────┐
│         应用接口层                  │
│     Key对象、事件处理器              │
├─────────────────────────────────────┤
│         协议解析层                  │
│   KittyParser、EscapeParser        │
├─────────────────────────────────────┤
│         事件引擎层                  │
│      EventEngine (增强版)           │
├─────────────────────────────────────┤
│         终端接口层                  │
│        Terminal (Blessed)           │
└─────────────────────────────────────┘
```

### 增强的事件引擎

```python
# src/presentation/tui/event_engine.py（增强版）
from typing import Optional, Any
from blessed import Terminal

from .key import Key
from .kitty_parser import KittyProtocolParser
from .escape_parser import EscapeSequenceParser

class EventEngine:
    """增强的事件处理引擎
    
    在保持向后兼容的同时，支持新的标准化按键对象。
    """
    
    def __init__(self, terminal: Terminal, config: Any) -> None:
        self.terminal = terminal
        self.config = config
        self.tui_logger = get_tui_logger(__name__)
        
        # 新增：按键解析器
        self.kitty_parser = KittyProtocolParser()
        self.escape_parser = EscapeSequenceParser()
        self._enable_enhanced_keys = config.get('enhanced_keyboard_support', True)
        
        # 新增：按键序列缓冲区
        self._key_buffer = ""
        self._max_sequence_length = 16
        
        # 新增：调试支持
        self._debug_key_sequences = config.get('debug_key_sequences', False)
        if self._debug_key_sequences:
            from .debug.sequence_monitor import SequenceMonitor
            self.sequence_monitor = SequenceMonitor()
    
    def process_key(self, key_str: str) -> None:
        """处理按键输入（主入口）"""
        if not key_str:
            return
        
        # 添加到序列缓冲区
        self._key_buffer += key_str
        
        # 尝试解析完整的按键序列
        if self._enable_enhanced_keys:
            result = self._parse_key_sequence(self._key_buffer)
            if result:
                key, consumed_length = result
                self._key_buffer = self._key_buffer[consumed_length:]
                
                # 调试监控
                if self._debug_key_sequences:
                    self.sequence_monitor.add_sequence(key.sequence, str(key))
                
                # 使用新的按键对象处理
                self._handle_parsed_key(key)
                return
        
        # 回退到传统处理（单字符）
        if len(self._key_buffer) <= 2 and not self._key_buffer.startswith('\x1b'):
            self._handle_traditional_key(key_str)
            self._key_buffer = ""
    
    def _parse_key_sequence(self, sequence: str) -> Optional[tuple[Key, int]]:
        """解析按键序列"""
        # 1. 尝试Kitty协议
        if self.kitty_parser.is_kitty_sequence(sequence):
            result = self.kitty_parser.parse_sequence(sequence)
            if result:
                return result
        
        # 2. 尝试传统Escape序列
        if self.escape_parser.is_escape_sequence(sequence):
            result = self.escape_parser.parse_sequence(sequence)
            if result:
                return result
        
        # 3. 单字符处理
        if len(sequence) == 1:
            char = sequence[0]
            key = Key(
                name=f"char:{char}",
                sequence=sequence,
                kitty_protocol=False
            )
            return key, 1
        
        return None
    
    def _handle_parsed_key(self, key: Key) -> None:
        """处理解析后的按键对象"""
        # 记录按键事件
        self.tui_logger.debug_key_event(key, True, "parsed_key_handler")
        
        # 转换回字符串格式以保持向后兼容
        key_str = self._key_to_string(key)
        
        # 使用现有的处理逻辑
        self._handle_traditional_key(key_str)
    
    def _key_to_string(self, key: Key) -> str:
        """将Key对象转换为字符串格式（向后兼容）"""
        # 优先使用传统字符串格式以保持兼容
        if key.name.startswith('char:'):
            return key.name
        elif key.name in ['enter', 'escape', 'tab', 'backspace', 'delete']:
            return key.name
        elif key.name in ['up', 'down', 'left', 'right', 'home', 'end', 'page_up', 'page_down']:
            return key.name
        elif key.name.startswith('f') and key.name[1:].isdigit():
            return key.name
        else:
            # 未知按键，使用序列表示
            return f"sequence:{key.sequence}"
    
    def _handle_traditional_key(self, key_str: str) -> None:
        """传统的字符串按键处理（保持现有逻辑不变）"""
        # 这里保持原有的所有处理代码
        # ... 现有逻辑 ...
        pass
```

---

## 4. 增强调试工具

### 序列监控器

```python
# src/presentation/tui/debug/sequence_monitor.py
import time
from typing import List, Dict, Any

class SequenceMonitor:
    """按键序列监控器"""
    
    def __init__(self, max_history: int = 100):
        self.sequences = []
        self.max_history = max_history
        self.start_time = time.time()
    
    def add_sequence(self, sequence: str, parsed_key=None) -> None:
        """添加按键序列"""
        entry = {
            'timestamp': time.time() - self.start_time,
            'sequence': repr(sequence),
            'parsed_key': str(parsed_key) if parsed_key else None,
            'length': len(sequence)
        }
        self.sequences.append(entry)
        
        # 保持最近的历史记录
        if len(self.sequences) > self.max_history:
            self.sequences.pop(0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取序列统计信息"""
        if not self.sequences:
            return {}
            
        total_sequences = len(self.sequences)
        unique_sequences = len(set(s['sequence'] for s in self.sequences))
        avg_length = sum(s['length'] for s in self.sequences) / total_sequences
        
        return {
            'total_sequences': total_sequences,
            'unique_sequences': unique_sequences,
            'average_length': avg_length,
            'time_span': self.sequences[-1]['timestamp'] - self.sequences[0]['timestamp']
        }
    
    def export_to_file(self, filepath: str) -> None:
        """导出序列数据到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for seq in self.sequences:
                f.write(f"{seq['timestamp']:.3f}: {seq['sequence']}")
                if seq['parsed_key']:
                    f.write(f" -> {seq['parsed_key']}")
                f.write('\n')
    
    def print_recent(self, count: int = 10) -> None:
        """打印最近的序列"""
        recent = self.sequences[-count:] if len(self.sequences) > count else self.sequences
        for seq in recent:
            print(f"{seq['timestamp']:.3f}s: {seq['sequence']} -> {seq['parsed_key']}")
```

### 增强日志系统

```python
# src/presentation/tui/logger/tui_logger_strategies.py（增强版）
class EnhancedDebugLoggingStrategy(TUILoggingStrategy):
    """增强调试日志记录策略"""
    
    def __init__(self):
        self.key_history = []
        self.max_history = 100
    
    def format_key_event(self, key) -> str:
        """格式化按键事件显示"""
        # 处理Key对象
        if hasattr(key, 'name'):
            return self._format_key_object(key)
        # 处理传统字符串
        elif isinstance(key, str):
            return self._format_string_key(key)
        else:
            return str(key)
    
    def _format_key_object(self, key) -> str:
        """格式化Key对象"""
        modifiers = []
        if getattr(key, 'ctrl', False):
            modifiers.append('Ctrl')
        if getattr(key, 'alt', False):
            modifiers.append('Alt')
        if getattr(key, 'shift', False):
            modifiers.append('Shift')
        if getattr(key, 'meta', False):
            modifiers.append('Meta')
        
        mod_str = '+'.join(modifiers) + '+' if modifiers else ''
        sequence_info = f" seq:{repr(getattr(key, 'sequence', ''))}" if hasattr(key, 'sequence') else ''
        protocol = " Kitty" if getattr(key, 'kitty_protocol', False) else ""
        
        return f"{mod_str}{getattr(key, 'name', 'unknown')}{sequence_info}{protocol}"
    
    def _format_string_key(self, key: str) -> str:
        """格式化字符串按键"""
        if key.startswith("char:"):
            char_value = key[5:]
            special_chars = {
                '\n': 'Enter/Newline',
                '\x1b': 'Escape', 
                '\x7f': 'Backspace',
                '\t': 'Tab',
                ' ': 'Space'
            }
            
            if char_value in special_chars:
                return f"{key} ({special_chars[char_value]})"
            elif char_value and ord(char_value) < 32:
                return f"{key} (Ctrl+{chr(ord(char_value) + 64)})"
            else:
                return f"{key} (ASCII: {ord(char_value) if char_value else 0})"
        
        return key
```

### 调试命令接口

```python
# src/presentation/tui/debug/commands.py
class DebugCommands:
    """调试命令接口"""
    
    def __init__(self, event_engine):
        self.event_engine = event_engine
    
    def enable_key_debugging(self, enabled: bool = True) -> None:
        """启用按键调试"""
        self.event_engine.enable_sequence_debugging(enabled)
        print(f"按键调试: {'启用' if enabled else '禁用'}")
    
    def show_key_stats(self) -> None:
        """显示按键统计"""
        stats = self.event_engine.get_sequence_statistics()
        if stats:
            print("按键序列统计:")
            print(f"  总序列数: {stats['total_sequences']}")
            print(f"  唯一序列: {stats['unique_sequences']}")
            print(f"  平均长度: {stats['average_length']:.1f}")
            print(f"  时间跨度: {stats['time_span']:.1f}s")
        else:
            print("暂无按键序列数据")
    
    def show_recent_keys(self, count: int = 10) -> None:
        """显示最近的按键"""
        if hasattr(self.event_engine, 'sequence_monitor'):
            print(f"最近 {count} 个按键序列:")
            self.event_engine.sequence_monitor.print_recent(count)
        else:
            print("按键监控未启用，使用 debug_keys on 启用")
    
    def export_key_log(self, filepath: str = "key_sequences.log") -> None:
        """导出按键日志"""
        if hasattr(self.event_engine, 'sequence_monitor'):
            self.event_engine.sequence_monitor.export_to_file(filepath)
            print(f"按键序列已导出到: {filepath}")
        else:
            print("按键监控未启用")
    
    def test_key_parsing(self, sequence: str) -> None:
        """测试按键解析"""
        print(f"测试序列: {repr(sequence)}")
        
        # 测试Kitty协议
        if self.event_engine.kitty_parser.is_kitty_sequence(sequence):
            result = self.event_engine.kitty_parser.parse_sequence(sequence)
            if result:
                key, length = result
                print(f"Kitty协议解析: {key} (消耗长度: {length})")
                return
        
        # 测试Escape序列
        if self.event_engine.escape_parser.is_escape_sequence(sequence):
            result = self.event_engine.escape_parser.parse_sequence(sequence)
            if result:
                key, length = result
                print(f"Escape序列解析: {key} (消耗长度: {length})")
                return
        
        print("无法识别的序列")
```

---

## 实施计划

### 阶段一：基础组件（第1周）
- [ ] 实现Key类
- [ ] 实现Kitty协议解析器
- [ ] 实现Escape序列解析器
- [ ] 基础单元测试

### 阶段二：引擎集成（第2周）
- [ ] 增强事件引擎
- [ ] 实现向后兼容
- [ ] 添加调试工具
- [ ] 集成测试

### 阶段三：优化完善（第3周）
- [ ] 性能优化
- [ ] 完善测试覆盖
- [ ] 文档编写
- [ ] 生产验证

### 关键特性

✅ **类型安全**：Key对象提供编译时检查
✅ **协议支持**：同时支持Kitty协议和传统Escape序列
✅ **向后兼容**：现有代码无需修改即可工作
✅ **调试友好**：实时监控和详细的解析信息
✅ **性能优化**：缓存机制和高效解析
✅ **可扩展**：清晰的架构便于后续扩展

这个方案保持了Python的简洁风格，同时提供了现代化的键盘处理能力，特别适合TUI应用的需求。