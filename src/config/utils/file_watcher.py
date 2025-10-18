"""文件监听器"""

import os
import time
import threading
from typing import Callable, Dict, List, Optional, Any
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# Import Observer for type hints
from watchdog.observers.api import BaseObserver


class FileWatcher:
    """文件监听器"""
    
    def __init__(self, watch_path: str, patterns: Optional[List[str]] = None):
        """初始化文件监听器
        
        Args:
            watch_path: 监听路径
            patterns: 文件模式列表（如 ['*.yaml', '*.yml']）
        """
        self.watch_path = Path(watch_path)
        self.patterns = patterns or ['*.yaml', '*.yml']
        self.observers: List[BaseObserver] = []
        self.callbacks: Dict[str, List[Callable[[str], None]]] = {}
        self._lock = threading.RLock()
        self._debounce_time = 0.1  # 100ms防抖时间
        self._last_processed: Dict[str, float] = {}
    
    def start(self) -> None:
        """开始监听"""
        with self._lock:
            if self.observers:
                return  # 已经在监听
            
            observer = Observer()
            event_handler = _ConfigFileHandler(self)
            observer.schedule(event_handler, str(self.watch_path), recursive=True)
            observer.start()
            self.observers.append(observer)
    
    def stop(self) -> None:
        """停止监听"""
        with self._lock:
            for observer in self.observers:
                observer.stop()
                observer.join()
            self.observers.clear()
    
    def add_callback(self, pattern: str, callback: Callable[[str], None]) -> None:
        """添加文件变化回调
        
        Args:
            pattern: 文件模式
            callback: 回调函数，接收文件路径参数
        """
        with self._lock:
            if pattern not in self.callbacks:
                self.callbacks[pattern] = []
            self.callbacks[pattern].append(callback)
    
    def remove_callback(self, pattern: str, callback: Callable[[str], None]) -> None:
        """移除文件变化回调
        
        Args:
            pattern: 文件模式
            callback: 回调函数
        """
        with self._lock:
            if pattern in self.callbacks and callback in self.callbacks[pattern]:
                self.callbacks[pattern].remove(callback)
    
    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化
        
        Args:
            file_path: 文件路径
        """
        try:
            current_time = time.time()
            
            # 检查是否在防抖时间内已经处理过此文件
            if file_path in self._last_processed:
                if current_time - self._last_processed[file_path] < self._debounce_time:
                    return  # 忽略过于频繁的事件
            
            # 更新最后处理时间
            self._last_processed[file_path] = current_time
            
            # 检查文件是否匹配模式
            file_path_obj = Path(file_path)
            matched_patterns = []
            
            for pattern in self.patterns:
                if file_path_obj.match(pattern):
                    matched_patterns.append(pattern)
            
            # 调用匹配的回调
            for pattern in matched_patterns:
                if pattern in self.callbacks:
                    for callback in self.callbacks[pattern]:
                        try:
                            callback(file_path)
                        except Exception as e:
                            print(f"文件变化回调执行失败: {e}")
        
        except Exception as e:
            print(f"处理文件变化失败: {e}")
    
    def is_watching(self) -> bool:
        """检查是否正在监听"""
        with self._lock:
            return len(self.observers) > 0
    
    def __del__(self) -> None:
        """析构函数，确保停止监听"""
        self.stop()


class _ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化处理器"""
    
    def __init__(self, watcher: FileWatcher) -> None:
        """初始化处理器
        
        Args:
            watcher: 文件监听器实例
        """
        self.watcher = watcher
    
    def on_modified(self, event: Any) -> None:
        """文件修改事件处理
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory and isinstance(event, FileModifiedEvent):
            file_path = event.src_path
            if isinstance(file_path, (bytes, bytearray)):
                file_path = str(file_path, 'utf-8')
            elif not isinstance(file_path, str):
                file_path = str(file_path)
            self.watcher._handle_file_change(file_path)


class MultiPathFileWatcher:
    """多路径文件监听器"""
    
    def __init__(self) -> None:
        """初始化多路径文件监听器"""
        self.watchers: Dict[str, FileWatcher] = {}
        self._lock = threading.RLock()
    
    def add_watch_path(self, path: str, patterns: Optional[List[str]] = None) -> None:
        """添加监听路径
        
        Args:
            path: 监听路径
            patterns: 文件模式列表
        """
        with self._lock:
            if path not in self.watchers:
                self.watchers[path] = FileWatcher(path, patterns)
                self.watchers[path].start()
    
    def remove_watch_path(self, path: str) -> None:
        """移除监听路径
        
        Args:
            path: 监听路径
        """
        with self._lock:
            if path in self.watchers:
                self.watchers[path].stop()
                del self.watchers[path]
    
    def add_callback(self, path: str, pattern: str, callback: Callable[[str], None]) -> None:
        """添加文件变化回调
        
        Args:
            path: 监听路径
            pattern: 文件模式
            callback: 回调函数
        """
        with self._lock:
            if path in self.watchers:
                self.watchers[path].add_callback(pattern, callback)
    
    def start_all(self) -> None:
        """开始所有监听"""
        with self._lock:
            for watcher in self.watchers.values():
                watcher.start()
    
    def stop_all(self) -> None:
        """停止所有监听"""
        with self._lock:
            for watcher in self.watchers.values():
                watcher.stop()
    
    def is_watching(self, path: Optional[str] = None) -> bool:
        """检查是否正在监听
        
        Args:
            path: 特定路径（可选）
            
        Returns:
            是否正在监听
        """
        with self._lock:
            if path:
                return path in self.watchers and self.watchers[path].is_watching()
            return any(watcher.is_watching() for watcher in self.watchers.values())
    
    def __del__(self) -> None:
        """析构函数，确保停止所有监听"""
        self.stop_all()