"""
TUI键盘按键处理 - Key类定义

提供标准化的按键表示和处理机制
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class KeyType(Enum):
    """按键类型枚举"""
    CHARACTER = "character"      # 普通字符
    FUNCTION = "function"        # 功能键 (F1-F12)
    ARROW = "arrow"             # 方向键
    MODIFIER = "modifier"       # 修饰键组合
    SEQUENCE = "sequence"       # 按键序列
    SPECIAL = "special"        # 特殊键


class KeyModifier(Enum):
    """修饰键枚举"""
    NONE = 0
    ALT = 1
    CTRL = 2
    SHIFT = 4
    META = 8


@dataclass
class Key:
    """标准化按键对象
    
    提供统一的按键表示，支持各种按键类型和修饰键组合
    """
    name: str                   # 按键名称
    key_type: KeyType          # 按键类型
    modifiers: int = 0         # 修饰键组合 (位掩码)
    raw_sequence: Optional[str] = None  # 原始按键序列
    code: Optional[int] = None  # 按键代码
    
    def __post_init__(self):
        """初始化后处理"""
        if self.modifiers is None:
            self.modifiers = 0
    
    @property
    def has_alt(self) -> bool:
        """是否包含Alt修饰键"""
        return bool(self.modifiers & KeyModifier.ALT.value)
    
    @property
    def has_ctrl(self) -> bool:
        """是否包含Ctrl修饰键"""
        return bool(self.modifiers & KeyModifier.CTRL.value)
    
    @property
    def has_shift(self) -> bool:
        """是否包含Shift修饰键"""
        return bool(self.modifiers & KeyModifier.SHIFT.value)
    
    @property
    def has_meta(self) -> bool:
        """是否包含Meta修饰键"""
        return bool(self.modifiers & KeyModifier.META.value)
    
    def to_string(self) -> str:
        """转换为字符串表示
        
        Returns:
            str: 按键的字符串表示
        """
        parts = []
        
        # 添加修饰键
        if self.has_ctrl:
            parts.append("ctrl")
        if self.has_alt:
            parts.append("alt")
        if self.has_shift:
            parts.append("shift")
        if self.has_meta:
            parts.append("meta")
        
        # 添加按键名称
        parts.append(self.name)
        
        return "_".join(parts)
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.to_string()
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash((self.name, self.key_type, self.modifiers))
    
    def __eq__(self, other) -> bool:
        """相等比较"""
        if not isinstance(other, Key):
            return False
        return (self.name == other.name and 
                self.key_type == other.key_type and 
                self.modifiers == other.modifiers)


class KeyParser:
    """按键解析器
    
    将各种按键输入格式转换为标准化的Key对象
    """
    
    # 标准按键映射
    STANDARD_KEYS = {
        # 字符键
        'enter': ('enter', KeyType.SPECIAL),
        'tab': ('tab', KeyType.SPECIAL),
        'backspace': ('backspace', KeyType.SPECIAL),
        'escape': ('escape', KeyType.SPECIAL),
        'space': ('space', KeyType.CHARACTER),
        
        # 方向键
        'up': ('up', KeyType.ARROW),
        'down': ('down', KeyType.ARROW),
        'left': ('left', KeyType.ARROW),
        'right': ('right', KeyType.ARROW),
        
        # 功能键
        'f1': ('f1', KeyType.FUNCTION),
        'f2': ('f2', KeyType.FUNCTION),
        'f3': ('f3', KeyType.FUNCTION),
        'f4': ('f4', KeyType.FUNCTION),
        'f5': ('f5', KeyType.FUNCTION),
        'f6': ('f6', KeyType.FUNCTION),
        'f7': ('f7', KeyType.FUNCTION),
        'f8': ('f8', KeyType.FUNCTION),
        'f9': ('f9', KeyType.FUNCTION),
        'f10': ('f10', KeyType.FUNCTION),
        'f11': ('f11', KeyType.FUNCTION),
        'f12': ('f12', KeyType.FUNCTION),
        
        # 编辑键
        'delete': ('delete', KeyType.SPECIAL),
        'insert': ('insert', KeyType.SPECIAL),
        'home': ('home', KeyType.SPECIAL),
        'end': ('end', KeyType.SPECIAL),
        'page_up': ('page_up', KeyType.SPECIAL),
        'page_down': ('page_down', KeyType.SPECIAL),
    }
    
    # blessed库按键名称映射
    BLESSED_NAME_MAP = {
        'KEY_ENTER': 'enter',
        'KEY_TAB': 'tab',
        'KEY_BACKSPACE': 'backspace',
        'KEY_ESCAPE': 'escape',
        'KEY_UP': 'up',
        'KEY_DOWN': 'down',
        'KEY_LEFT': 'left',
        'KEY_RIGHT': 'right',
        'KEY_F1': 'f1',
        'KEY_F2': 'f2',
        'KEY_F3': 'f3',
        'KEY_F4': 'f4',
        'KEY_F5': 'f5',
        'KEY_F6': 'f6',
        'KEY_F7': 'f7',
        'KEY_F8': 'f8',
        'KEY_F9': 'f9',
        'KEY_F10': 'f10',
        'KEY_F11': 'f11',
        'KEY_F12': 'f12',
        'KEY_DC': 'delete',
        'KEY_IC': 'insert',
        'KEY_HOME': 'home',
        'KEY_END': 'end',
        'KEY_PPAGE': 'page_up',
        'KEY_NPAGE': 'page_down',
    }
    
    @classmethod
    def from_string(cls, key_str: str) -> Optional[Key]:
        """从字符串创建Key对象
        
        Args:
            key_str: 按键字符串
            
        Returns:
            Key对象，如果无法解析则返回None
        """
        if not key_str:
            return None
        
        # 处理修饰键组合 (例如: "alt_1", "ctrl_c")
        parts = key_str.lower().split('_')
        modifiers = 0
        name_parts = []
        
        for part in parts:
            if part in ['ctrl', 'control']:
                modifiers |= KeyModifier.CTRL.value
            elif part == 'alt':
                modifiers |= KeyModifier.ALT.value
            elif part == 'shift':
                modifiers |= KeyModifier.SHIFT.value
            elif part == 'meta':
                modifiers |= KeyModifier.META.value
            else:
                name_parts.append(part)
        
        if not name_parts:
            return None
        
        name = '_'.join(name_parts)
        
        # 查找标准按键
        if name in cls.STANDARD_KEYS:
            std_name, key_type = cls.STANDARD_KEYS[name]
            return Key(std_name, key_type, modifiers)
        
        # 处理字符
        if name.startswith('char:'):
            char = name[5:]  # 移除 "char:" 前缀
            if len(char) == 1:
                return Key(char, KeyType.CHARACTER, modifiers)
        
        # 处理数字
        if name.isdigit():
            return Key(name, KeyType.CHARACTER, modifiers)
        
        # 未知按键类型
        return Key(name, KeyType.SPECIAL, modifiers)
    
    @classmethod
    def from_blessed_keystroke(cls, keystroke) -> Optional[Key]:
        """从blessed的Keystroke对象创建Key对象
        
        Args:
            keystroke: blessed的Keystroke对象
            
        Returns:
            Key对象，如果无法解析则返回None
        """
        if not keystroke:
            return None
        
        if keystroke.is_sequence:
            # 处理序列键
            if keystroke.name:
                # 映射blessed名称
                blessed_name = keystroke.name
                if blessed_name in cls.BLESSED_NAME_MAP:
                    name = cls.BLESSED_NAME_MAP[blessed_name]
                    std_name, key_type = cls.STANDARD_KEYS[name]
                    return Key(std_name, key_type, raw_sequence=keystroke.name, code=keystroke.code)
                else:
                    # 检查是否包含Alt修饰键
                    if 'alt' in blessed_name.lower():
                        # 提取数字部分
                        for i in range(1, 10):
                            if str(i) in blessed_name:
                                return Key(str(i), KeyType.CHARACTER, 
                                         modifiers=KeyModifier.ALT.value,
                                         raw_sequence=keystroke.name, code=keystroke.code)
                    
                    # 使用原始名称
                    name = blessed_name.lower().replace('key_', '')
                    return Key(name, KeyType.SPECIAL, 
                             raw_sequence=keystroke.name, code=keystroke.code)
            else:
                # 使用code
                return Key(f"key_{keystroke.code}", KeyType.SEQUENCE, 
                          raw_sequence=keystroke.name, code=keystroke.code)
        else:
            # 处理普通字符
            char = str(keystroke)
            
            # 处理特殊字符
            if char == '\r' or char == '\n':
                return Key('enter', KeyType.SPECIAL, code=ord(char))
            elif char == '\t':
                return Key('tab', KeyType.SPECIAL, code=ord(char))
            elif char == '\x7f' or char == '\x08':
                return Key('backspace', KeyType.SPECIAL, code=ord(char))
            elif char == '\x1b':
                return Key('escape', KeyType.SPECIAL, code=ord(char))
            elif len(char) == 1 and 128 <= ord(char) <= 255:
                # Alt+字符组合
                original_char = chr(ord(char) - 128)
                if original_char.isdigit():
                    return Key(original_char, KeyType.CHARACTER, 
                             modifiers=KeyModifier.ALT.value, code=ord(char))
                else:
                    return Key(original_char, KeyType.CHARACTER, 
                             modifiers=KeyModifier.ALT.value, code=ord(char))
            elif len(char) == 1:
                return Key(char, KeyType.CHARACTER, code=ord(char))
            else:
                return Key(char, KeyType.CHARACTER, code=ord(char[0]) if char else 0)
    
    @classmethod
    def from_sequence(cls, sequence: str) -> Optional[Key]:
        """从按键序列创建Key对象
        
        处理ESC序列，如Alt键组合
        
        Args:
            sequence: 按键序列
            
        Returns:
            Key对象，如果无法解析则返回None
        """
        if not sequence:
            return None
        
        # 处理ESC序列 (Alt键组合)
        if sequence.startswith('\x1b') and len(sequence) > 1:
            # 移除ESC字符
            remaining = sequence[1:]
            
            # 处理Alt+数字
            if len(remaining) == 1 and remaining.isdigit():
                return Key(remaining, KeyType.CHARACTER, 
                          modifiers=KeyModifier.ALT.value,
                          raw_sequence=sequence)
            
            # 处理其他Alt组合
            if len(remaining) == 1:
                return Key(remaining, KeyType.CHARACTER, 
                          modifiers=KeyModifier.ALT.value,
                          raw_sequence=sequence)
        
        # 单个ESC键
        if sequence == '\x1b':
            return Key('escape', KeyType.SPECIAL, raw_sequence=sequence)
        
        return None


# 预定义的常用按键
KEY_ENTER = Key('enter', KeyType.SPECIAL)
KEY_TAB = Key('tab', KeyType.SPECIAL)
KEY_BACKSPACE = Key('backspace', KeyType.SPECIAL)
KEY_ESCAPE = Key('escape', KeyType.SPECIAL)
KEY_SPACE = Key('space', KeyType.CHARACTER)

KEY_UP = Key('up', KeyType.ARROW)
KEY_DOWN = Key('down', KeyType.ARROW)
KEY_LEFT = Key('left', KeyType.ARROW)
KEY_RIGHT = Key('right', KeyType.ARROW)

KEY_DELETE = Key('delete', KeyType.SPECIAL)
KEY_INSERT = Key('insert', KeyType.SPECIAL)
KEY_HOME = Key('home', KeyType.SPECIAL)
KEY_END = Key('end', KeyType.SPECIAL)
KEY_PAGE_UP = Key('page_up', KeyType.SPECIAL)
KEY_PAGE_DOWN = Key('page_down', KeyType.SPECIAL)

# 带修饰键的常用组合
KEY_CTRL_C = Key('c', KeyType.CHARACTER, modifiers=KeyModifier.CTRL.value)
KEY_CTRL_D = Key('d', KeyType.CHARACTER, modifiers=KeyModifier.CTRL.value)
KEY_CTRL_Z = Key('z', KeyType.CHARACTER, modifiers=KeyModifier.CTRL.value)
KEY_ALT_1 = Key('1', KeyType.CHARACTER, modifiers=KeyModifier.ALT.value)
KEY_ALT_2 = Key('2', KeyType.CHARACTER, modifiers=KeyModifier.ALT.value)
KEY_ALT_3 = Key('3', KeyType.CHARACTER, modifiers=KeyModifier.ALT.value)
KEY_ALT_4 = Key('4', KeyType.CHARACTER, modifiers=KeyModifier.ALT.value)
KEY_ALT_5 = Key('5', KeyType.CHARACTER, modifiers=KeyModifier.ALT.value)
KEY_ALT_6 = Key('6', KeyType.CHARACTER, modifiers=KeyModifier.ALT.value)