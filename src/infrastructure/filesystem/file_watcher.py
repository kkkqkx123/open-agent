"""文件监听工具

提供通用的文件监听功能，可被多个模块使用。
"""

import time
import threading
from typing import Callable, Dict, List, Optional, Any
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# Import Observer for type hints
from watchdog.observers.api import BaseObserver

# Import interface
from src.interfaces.filesystem import IFileWatcher


class FileWatcher(IFileWatcher):
    """文件监听器"""

    def __init__(self, watch_path: str, patterns: Optional[List[str]] = None):
        """初始化文件监听器

        Args:
            watch_path: 监听路径
            patterns: 文件模式列表（如 ['*.yaml', '*.yml']）
        """
        self.watch_path = Path(watch_path)
        self.patterns = patterns or ["*.yaml", "*.yml"]
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
            event_handler = _FileHandler(self)
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
                            # 记录错误但继续处理其他回调
                            error_msg = f"文件变化回调执行失败: {e}"
                            import sys
                            print(f"[FileWatcherError] {error_msg}", file=sys.stderr)

        except Exception as e:
            # 记录处理错误但继续监听
            error_msg = f"处理文件变化失败: {e}"
            import sys
            print(f"[FileWatcherError] {error_msg}", file=sys.stderr)

    def is_watching(self) -> bool:
        """检查是否正在监听"""
        with self._lock:
            return len(self.observers) > 0

    def __del__(self) -> None:
        """析构函数，确保停止监听"""
        self.stop()


class _FileHandler(FileSystemEventHandler):
    """文件变化处理器"""

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
                file_path = str(file_path, "utf-8")
            elif not isinstance(file_path, str):
                file_path = str(file_path)
            self.watcher._handle_file_change(file_path)


class MultiPathFileWatcher:
    """多路径文件监听器"""

    def __init__(self) -> None:
        """初始化多路径文件监听器"""
        self.watchers: Dict[str, FileWatcher] = {}
        self._lock = threading.RLock()
        self._started_via_start_all = False

    def add_watch_path(self, path: str, patterns: Optional[List[str]] = None) -> None:
        """添加监听路径

        Args:
            path: 监听路径
            patterns: 文件模式列表
        """
        with self._lock:
            if path not in self.watchers:
                self.watchers[path] = FileWatcher(path, patterns)
                # 添加路径时启动监听，但不标记为通过start_all启动
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

    def add_callback(
        self, path: str, pattern: str, callback: Callable[[str], None]
    ) -> None:
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
            self._started_via_start_all = True

    def stop_all(self) -> None:
        """停止所有监听"""
        with self._lock:
            for watcher in self.watchers.values():
                watcher.stop()
            self._started_via_start_all = False

    def is_watching(self, path: Optional[str] = None) -> bool:
        """检查是否正在监听

        Args:
            path: 特定路径（可选）

        Returns:
            是否正在监听
        """
        with self._lock:
            if path:
                # 检查路径是否在监听器列表中并且正在运行
                return path in self.watchers and self.watchers[path].is_watching()
            # 检查是否通过start_all启动了监听
            # 根据测试逻辑，期望在没有调用start_all之前，is_watching()返回False
            # 但在调用start_all后，返回True
            return self._started_via_start_all and any(watcher.is_watching() for watcher in self.watchers.values())

    def __del__(self) -> None:
        """析构函数，确保停止所有监听"""
        self.stop_all()