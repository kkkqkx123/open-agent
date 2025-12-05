"""文件系统相关接口

定义文件监听和文件操作的通用接口。
"""

from typing import Callable, List, Optional, Any
from abc import ABC, abstractmethod


# 异常类
class FileWatcherError(Exception):
    """文件监听器基础异常"""
    pass


class FileWatchPathError(FileWatcherError):
    """文件监听路径异常"""
    pass


class FileWatchCallbackError(FileWatcherError):
    """文件监听回调异常"""
    pass


class IFileWatcher(ABC):
    """文件监听器接口"""
    
    @abstractmethod
    def start(self) -> None:
        """开始监听文件变化"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """停止监听文件变化"""
        pass
    
    @abstractmethod
    def add_callback(self, pattern: str, callback: Callable[[str], None]) -> None:
        """添加文件变化回调
        
        Args:
            pattern: 文件模式（如 "*.yaml"）
            callback: 回调函数，接收文件路径参数
        """
        pass
    
    @abstractmethod
    def remove_callback(self, pattern: str, callback: Callable[[str], None]) -> None:
        """移除文件变化回调
        
        Args:
            pattern: 文件模式
            callback: 回调函数
        """
        pass
    
    @abstractmethod
    def is_watching(self) -> bool:
        """检查是否正在监听
        
        Returns:
            是否正在监听
        """
        pass


class IFileWatcherFactory(ABC):
    """文件监听器工厂接口"""
    
    @abstractmethod
    def create_watcher(
        self, 
        watch_path: str, 
        patterns: Optional[List[str]] = None
    ) -> IFileWatcher:
        """创建文件监听器
        
        Args:
            watch_path: 监听路径
            patterns: 文件模式列表
            
        Returns:
            文件监听器实例
        """
        pass


__all__ = [
    # 异常类
    "FileWatcherError",
    "FileWatchPathError",
    "FileWatchCallbackError",
    # 接口类
    "IFileWatcher",
    "IFileWatcherFactory",
]
