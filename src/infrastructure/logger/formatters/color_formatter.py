"""彩色日志格式化器"""

import sys
from typing import Any, Dict, Optional
from .text_formatter import TextFormatter


class ColorFormatter(TextFormatter):
    """彩色格式化器"""

    # ANSI颜色代码
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
    }

    # 日志级别对应的颜色
    LEVEL_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bright_red',
    }

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_colors: Optional[bool] = None,
    ):
        """初始化彩色格式化器

        Args:
            fmt: 格式字符串
            datefmt: 日期格式
            use_colors: 是否使用颜色，None表示自动检测
        """
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors if use_colors is not None else self._detect_color_support()

    def _detect_color_support(self) -> bool:
        """检测终端是否支持颜色

        Returns:
            是否支持颜色
        """
        # 检查是否是TTY终端
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False

        # 检查环境变量
        import os
        if os.environ.get('NO_COLOR'):
            return False
        if os.environ.get('FORCE_COLOR'):
            return True

        # 检查TERM环境变量
        term = os.environ.get('TERM', '')
        if 'color' in term or term in ('xterm', 'xterm-256color', 'screen', 'tmux'):
            return True

        # Windows检测
        if sys.platform == 'win32':
            try:
                import colorama
                return True
            except ImportError:
                return False

        return False

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录，添加颜色

        Args:
            record: 日志记录字典

        Returns:
            带颜色的格式化字符串
        """
        if not self.use_colors:
            # 不使用颜色时回退到普通文本格式
            return super().format(record)

        # 获取日志级别
        level = self._get_field_value(record, 'level', 'INFO')
        
        # 为不同级别添加颜色
        if level in self.LEVEL_COLORS:
            color_name = self.LEVEL_COLORS[level]
            color_code = self.COLORS[color_name]
            reset_code = self.COLORS['reset']
            
            # 创建带颜色的格式字符串
            colored_fmt = self.fmt.replace('{level}', f'{color_code}{{level}}{reset_code}')
            
            # 临时替换fmt进行格式化
            original_fmt = self.fmt
            self.fmt = colored_fmt
            try:
                result = super().format(record)
            finally:
                self.fmt = original_fmt
            
            return result
        else:
            # 未知级别使用默认格式
            return super().format(record)

    def colorize(self, text: str, color_name: str) -> str:
        """为文本添加颜色

        Args:
            text: 要着色的文本
            color_name: 颜色名称

        Returns:
            带颜色的文本
        """
        if not self.use_colors or color_name not in self.COLORS:
            return text
        
        color_code = self.COLORS[color_name]
        reset_code = self.COLORS['reset']
        return f"{color_code}{text}{reset_code}"

    def get_level_color(self, level: str) -> str:
        """获取日志级别对应的颜色

        Args:
            level: 日志级别

        Returns:
            颜色名称
        """
        return self.LEVEL_COLORS.get(level.upper(), 'white')