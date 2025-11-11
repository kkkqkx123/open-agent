"""配置热重载监听器

监听配置文件变化事件，智能过滤无关变化事件，触发配置重新解析和注册更新。
"""

from typing import Dict, List, Any, Optional, Callable, Set
from pathlib import Path
import threading
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

logger = logging.getLogger(__name__)


class HotReloadEvent:
    """热重载事件"""
    
    def __init__(self, event_type: str, file_path: str, timestamp: float = None):
        """初始化热重载事件
        
        Args:
            event_type: 事件类型
            file_path: 文件路径
            timestamp: 时间戳
        """
        self.event_type = event_type
        self.file_path = file_path
        self.timestamp = timestamp or time.time()
    
    def __str__(self) -> str:
        return f"HotReloadEvent({self.event_type}, {self.file_path})"


class HotReloadListener(FileSystemEventHandler):
    """配置热重载监听器
    
    监听配置文件变化事件，智能过滤无关变化事件。
    """
    
    def __init__(
        self,
        watch_paths: List[str],
        callback: Optional[Callable[[HotReloadEvent], None]] = None,
        debounce_time: float = 1.0,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ):
        """初始化热重载监听器
        
        Args:
            watch_paths: 监听路径列表
            callback: 回调函数
            debounce_time: 防抖时间（秒）
            file_patterns: 文件模式列表
            exclude_patterns: 排除模式列表
        """
        super().__init__()
        
        self.watch_paths = [Path(p) for p in watch_paths]
        self.callback = callback
        self.debounce_time = debounce_time
        
        # 文件模式
        self.file_patterns = file_patterns or [r".*\.ya?ml$", r".*\.json$"]
        self.exclude_patterns = exclude_patterns or [
            r".*\.tmp$",
            r".*\.swp$",
            r".*~$",
            r".*\.bak$",
            r".*\.backup$"
        ]
        
        # 编译正则表达式
        import re
        self.compiled_file_patterns = [re.compile(pattern) for pattern in self.file_patterns]
        self.compiled_exclude_patterns = [re.compile(pattern) for pattern in self.exclude_patterns]
        
        # 监听器状态
        self.observer: Optional[Observer] = None
        self.is_running = False
        self.event_queue: List[HotReloadEvent] = []
        self.queue_lock = threading.Lock()
        self.debounce_timer: Optional[threading.Timer] = None
        
        # 统计信息
        self.stats = {
            "events_received": 0,
            "events_processed": 0,
            "events_filtered": 0,
            "errors": 0
        }
        
        self.logger = logging.getLogger(f"{__name__}.HotReloadListener")
    
    def start(self) -> None:
        """启动监听器"""
        if self.is_running:
            self.logger.warning("监听器已在运行")
            return
        
        try:
            # 创建观察者
            self.observer = Observer()
            
            # 添加监听路径
            for watch_path in self.watch_paths:
                if watch_path.exists():
                    self.observer.schedule(self, str(watch_path), recursive=True)
                    self.logger.info(f"添加监听路径: {watch_path}")
                else:
                    self.logger.warning(f"监听路径不存在: {watch_path}")
            
            # 启动观察者
            self.observer.start()
            self.is_running = True
            
            self.logger.info("热重载监听器已启动")
            
        except Exception as e:
            self.logger.error(f"启动热重载监听器失败: {e}")
            raise
    
    def stop(self) -> None:
        """停止监听器"""
        if not self.is_running:
            return
        
        try:
            # 停止防抖定时器
            if self.debounce_timer:
                self.debounce_timer.cancel()
                self.debounce_timer = None
            
            # 停止观察者
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                self.observer = None
            
            self.is_running = False
            self.logger.info("热重载监听器已停止")
            
        except Exception as e:
            self.logger.error(f"停止热重载监听器失败: {e}")
    
    def on_modified(self, event) -> None:
        """文件修改事件处理
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            self._handle_file_event("modified", event.src_path)
    
    def on_created(self, event) -> None:
        """文件创建事件处理
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            self._handle_file_event("created", event.src_path)
    
    def on_deleted(self, event) -> None:
        """文件删除事件处理
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            self._handle_file_event("deleted", event.src_path)
    
    def _handle_file_event(self, event_type: str, file_path: str) -> None:
        """处理文件事件
        
        Args:
            event_type: 事件类型
            file_path: 文件路径
        """
        try:
            self.stats["events_received"] += 1
            
            # 检查文件模式
            if not self._should_process_file(file_path):
                self.stats["events_filtered"] += 1
                self.logger.debug(f"过滤文件事件: {file_path}")
                return
            
            # 创建热重载事件
            hot_reload_event = HotReloadEvent(event_type, file_path)
            
            # 添加到队列
            with self.queue_lock:
                self.event_queue.append(hot_reload_event)
            
            # 启动防抖定时器
            self._schedule_debounce()
            
            self.logger.debug(f"接收文件事件: {hot_reload_event}")
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"处理文件事件失败: {e}")
    
    def _should_process_file(self, file_path: str) -> bool:
        """检查是否应该处理文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否应该处理
        """
        file_name = Path(file_path).name
        
        # 检查文件模式
        for pattern in self.compiled_file_patterns:
            if pattern.search(file_name):
                break
        else:
            return False
        
        # 检查排除模式
        for pattern in self.compiled_exclude_patterns:
            if pattern.search(file_name):
                return False
        
        return True
    
    def _schedule_debounce(self) -> None:
        """调度防抖处理"""
        # 取消现有定时器
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        # 创建新定时器
        self.debounce_timer = threading.Timer(
            self.debounce_time,
            self._process_event_queue
        )
        self.debounce_timer.start()
    
    def _process_event_queue(self) -> None:
        """处理事件队列"""
        try:
            events_to_process = []
            
            # 获取待处理事件
            with self.queue_lock:
                if self.event_queue:
                    events_to_process = self.event_queue.copy()
                    self.event_queue.clear()
            
            if not events_to_process:
                return
            
            # 去重和合并事件
            merged_events = self._merge_events(events_to_process)
            
            # 处理事件
            for event in merged_events:
                self._process_event(event)
                self.stats["events_processed"] += 1
            
            self.logger.debug(f"处理了 {len(merged_events)} 个热重载事件")
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"处理事件队列失败: {e}")
    
    def _merge_events(self, events: List[HotReloadEvent]) -> List[HotReloadEvent]:
        """合并事件
        
        Args:
            events: 事件列表
            
        Returns:
            List[HotReloadEvent]: 合并后的事件列表
        """
        # 按文件路径分组
        events_by_file = {}
        
        for event in events:
            file_path = event.file_path
            if file_path not in events_by_file:
                events_by_file[file_path] = []
            events_by_file[file_path].append(event)
        
        # 合并每个文件的事件
        merged_events = []
        for file_path, file_events in events_by_file.items():
            # 按时间排序
            file_events.sort(key=lambda e: e.timestamp)
            
            # 获取最新事件
            latest_event = file_events[-1]
            
            # 如果有删除事件，优先处理
            for event in reversed(file_events):
                if event.event_type == "deleted":
                    latest_event = event
                    break
            
            merged_events.append(latest_event)
        
        return merged_events
    
    def _process_event(self, event: HotReloadEvent) -> None:
        """处理单个事件
        
        Args:
            event: 热重载事件
        """
        try:
            self.logger.info(f"处理热重载事件: {event}")
            
            # 调用回调函数
            if self.callback:
                self.callback(event)
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"处理热重载事件失败: {event}, 错误: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            **self.stats,
            "is_running": self.is_running,
            "queue_size": len(self.event_queue),
            "watch_paths": [str(p) for p in self.watch_paths]
        }
    
    def clear_stats(self) -> None:
        """清除统计信息"""
        self.stats = {
            "events_received": 0,
            "events_processed": 0,
            "events_filtered": 0,
            "errors": 0
        }


class HotReloadManager:
    """热重载管理器
    
    管理多个热重载监听器，提供统一的热重载功能。
    """
    
    def __init__(self, base_path: str = "configs"):
        """初始化热重载管理器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(f"{__name__}.HotReloadManager")
        
        # 监听器列表
        self.listeners: List[HotReloadListener] = []
        
        # 回调函数列表
        self.callbacks: List[Callable[[HotReloadEvent], None]] = []
        
        # 管理器状态
        self.is_running = False
    
    def add_listener(
        self,
        watch_paths: List[str],
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> HotReloadListener:
        """添加监听器
        
        Args:
            watch_paths: 监听路径列表
            file_patterns: 文件模式列表
            exclude_patterns: 排除模式列表
            
        Returns:
            HotReloadListener: 监听器实例
        """
        listener = HotReloadListener(
            watch_paths=watch_paths,
            callback=self._handle_event,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns
        )
        
        self.listeners.append(listener)
        
        # 如果管理器正在运行，立即启动监听器
        if self.is_running:
            listener.start()
        
        self.logger.info(f"添加热重载监听器: {watch_paths}")
        return listener
    
    def remove_listener(self, listener: HotReloadListener) -> None:
        """移除监听器
        
        Args:
            listener: 监听器实例
        """
        if listener in self.listeners:
            listener.stop()
            self.listeners.remove(listener)
            self.logger.info("移除热重载监听器")
    
    def add_callback(self, callback: Callable[[HotReloadEvent], None]) -> None:
        """添加回调函数
        
        Args:
            callback: 回调函数
        """
        self.callbacks.append(callback)
        self.logger.debug("添加热重载回调函数")
    
    def remove_callback(self, callback: Callable[[HotReloadEvent], None]) -> None:
        """移除回调函数
        
        Args:
            callback: 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            self.logger.debug("移除热重载回调函数")
    
    def start(self) -> None:
        """启动所有监听器"""
        if self.is_running:
            self.logger.warning("热重载管理器已在运行")
            return
        
        try:
            for listener in self.listeners:
                listener.start()
            
            self.is_running = True
            self.logger.info("热重载管理器已启动")
            
        except Exception as e:
            self.logger.error(f"启动热重载管理器失败: {e}")
            raise
    
    def stop(self) -> None:
        """停止所有监听器"""
        if not self.is_running:
            return
        
        try:
            for listener in self.listeners:
                listener.stop()
            
            self.is_running = False
            self.logger.info("热重载管理器已停止")
            
        except Exception as e:
            self.logger.error(f"停止热重载管理器失败: {e}")
    
    def _handle_event(self, event: HotReloadEvent) -> None:
        """处理热重载事件
        
        Args:
            event: 热重载事件
        """
        try:
            # 调用所有回调函数
            for callback in self.callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"热重载回调函数执行失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"处理热重载事件失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        listener_stats = []
        total_stats = {
            "events_received": 0,
            "events_processed": 0,
            "events_filtered": 0,
            "errors": 0
        }
        
        for listener in self.listeners:
            stats = listener.get_stats()
            listener_stats.append(stats)
            
            # 累计统计信息
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        
        return {
            "is_running": self.is_running,
            "listener_count": len(self.listeners),
            "callback_count": len(self.callbacks),
            "total_stats": total_stats,
            "listener_stats": listener_stats
        }