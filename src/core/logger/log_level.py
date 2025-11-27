"""日志级别定义"""

from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def from_string(cls, level_str: str) -> "LogLevel":
        """从字符串创建日志级别"""
        level_map = {
            "DEBUG": cls.DEBUG,
            "INFO": cls.INFO,
            "WARNING": cls.WARNING,
            "WARN": cls.WARNING,
            "ERROR": cls.ERROR,
            "CRITICAL": cls.CRITICAL,
            "FATAL": cls.CRITICAL,
        }

        upper_level = level_str.upper()
        if upper_level not in level_map:
            raise ValueError(f"无效的日志级别: {level_str}")

        return level_map[upper_level]

    def __str__(self) -> str:
        """返回日志级别的字符串表示"""
        return self.name

    def __lt__(self, other: "LogLevel") -> bool:
        """比较日志级别大小"""
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: "LogLevel") -> bool:
        """比较日志级别大小"""
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: "LogLevel") -> bool:
        """比较日志级别大小"""
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: "LogLevel") -> bool:
        """比较日志级别大小"""
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.value >= other.value