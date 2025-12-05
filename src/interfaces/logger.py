"""日志系统接口定义

提供日志记录器、处理器、脱敏器等日志相关组件的接口定义。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.logger.core.log_level import LogLevel


class IBaseHandler(ABC):
    """日志处理器接口
    
    定义日志处理器的基础契约，避免接口层对具体实现的依赖。
    """
    
    @abstractmethod
    def handle(self, record: Dict[str, Any]) -> None:
        """处理日志记录
        
        Args:
            record: 日志记录字典
        """
        pass
    
    @abstractmethod
    def set_level(self, level: "LogLevel") -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        pass
    
    @abstractmethod
    def set_formatter(self, formatter: Any) -> None:
        """设置格式化器
        
        Args:
            formatter: 格式化器实例
        """
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """刷新缓冲区"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭处理器"""
        pass


class ILogRedactor(ABC):
    """日志脱敏器接口
    
    定义日志脱敏功能的基础契约。
    """
    
    @abstractmethod
    def redact(self, text: str, level: "LogLevel | str" = "INFO") -> str:
        """脱敏文本
        
        Args:
            text: 原始文本
            level: 日志级别，可以是字符串或LogLevel枚举
            
        Returns:
            脱敏后的文本
        """
        pass


class ILogger(ABC):
    """日志记录器接口
    
    提供统一的日志记录抽象，支持多种日志输出和格式化。
    """
    
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志
        
        Args:
            message: 日志消息
            **kwargs: 附加参数
        """
        pass
    
    @abstractmethod
    def set_level(self, level: "LogLevel") -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        pass
    
    @abstractmethod
    def add_handler(self, handler: IBaseHandler) -> None:
        """添加日志处理器
        
        Args:
            handler: 日志处理器
        """
        pass
    
    @abstractmethod
    def remove_handler(self, handler: IBaseHandler) -> None:
        """移除日志处理器
        
        Args:
            handler: 日志处理器
        """
        pass
    
    @abstractmethod
    def set_redactor(self, redactor: ILogRedactor) -> None:
        """设置日志脱敏器
        
        Args:
            redactor: 日志脱敏器
        """
        pass


class ILoggerFactory(ABC):
    """日志工厂接口
    
    定义日志创建工厂的基础契约，避免接口层对具体实现的依赖。
    """
    
    @abstractmethod
    def create_logger(self, name: str, **kwargs: Any) -> ILogger:
        """创建日志记录器
        
        Args:
            name: 日志记录器名称
            **kwargs: 额外参数
            
        Returns:
            日志记录器实例
        """
        pass
    
    @abstractmethod
    def create_console_handler(
        self,
        level: "LogLevel | None" = None,
        formatter_name: str = "color",
        use_colors: Any = None,
    ) -> IBaseHandler:
        """创建控制台处理器
        
        Args:
            level: 日志级别
            formatter_name: 格式化器名称
            use_colors: 是否使用颜色
            
        Returns:
            控制台处理器
        """
        pass
    
    @abstractmethod
    def create_file_handler(
        self,
        filename: str,
        level: "LogLevel | None" = None,
        formatter_name: str = "text",
        encoding: str = "utf-8",
        max_bytes: Any = None,
        backup_count: int = 0,
    ) -> IBaseHandler:
        """创建文件处理器
        
        Args:
            filename: 日志文件名
            level: 日志级别
            formatter_name: 格式化器名称
            encoding: 文件编码
            max_bytes: 最大文件字节数
            backup_count: 备份文件数量
            
        Returns:
            文件处理器
        """
        pass
    
    @abstractmethod
    def create_json_handler(
        self,
        filename: str,
        level: "LogLevel | None" = None,
        encoding: str = "utf-8",
        max_bytes: Any = None,
        backup_count: int = 0,
        ensure_ascii: bool = False,
        indent: Any = None,
        sort_keys: bool = False,
    ) -> IBaseHandler:
        """创建JSON处理器
        
        Args:
            filename: 日志文件名
            level: 日志级别
            encoding: 文件编码
            max_bytes: 最大文件字节数
            backup_count: 备份文件数量
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数
            sort_keys: 是否排序键
            
        Returns:
            JSON处理器
        """
        pass


# 为了向后兼容，重新导出LogLevel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.logger.core.log_level import LogLevel
else:
    # 运行时导入以避免循环依赖
    try:
        from src.infrastructure.logger.core.log_level import LogLevel
    except ImportError:
        # 如果基础设施层还未完全就绪，提供临时实现
        from enum import Enum
        
        class LogLevel(str, Enum):
            """临时LogLevel实现"""
            DEBUG = "DEBUG"
            INFO = "INFO"
            WARNING = "WARNING"
            WARN = "WARN"
            ERROR = "ERROR"
            CRITICAL = "CRITICAL"
            FATAL = "FATAL"
            
            @classmethod
            def from_string(cls, level_str: str) -> "LogLevel":
                """从字符串创建日志级别"""
                level_map = {
                    "DEBUG": cls.DEBUG,
                    "INFO": cls.INFO,
                    "WARNING": cls.WARNING,
                    "WARN": cls.WARN,
                    "ERROR": cls.ERROR,
                    "CRITICAL": cls.CRITICAL,
                    "FATAL": cls.FATAL,
                }
                
                upper_level = level_str.upper()
                if upper_level not in level_map:
                    raise ValueError(f"无效的日志级别: {level_str}")
                
                return level_map[upper_level]
            
            def __str__(self) -> str:
                """返回日志级别的字符串表示"""
                return self.value


__all__ = [
    "IBaseHandler",
    "ILogRedactor",
    "ILogger",
    "ILoggerFactory",
    "LogLevel",
]