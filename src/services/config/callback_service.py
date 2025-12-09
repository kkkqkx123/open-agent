"""配置变更回调服务

提供配置变更事件的订阅、发布和管理功能。
"""

import logging
import threading
from typing import Dict, Any, List, Callable, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

if TYPE_CHECKING:
    from .config_service import ConfigChangeEvent, ConfigChangeType


class CallbackPriority(Enum):
    """回调优先级"""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class CallbackRegistration:
    """回调注册信息"""
    callback: Callable[..., None]  # 接收ConfigChangeEvent参数
    priority: CallbackPriority = CallbackPriority.NORMAL
    filter_config_paths: Optional[Set[str]] = None  # 只监听特定配置路径
    filter_change_types: Optional[Set[Any]] = None  # 只监听特定变更类型
    filter_key_paths: Optional[Set[str]] = None  # 只监听特定键路径
    enabled: bool = True
    registration_time: datetime = field(default_factory=datetime.now)
    call_count: int = 0
    last_called: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None


class CallbackService:
    """配置变更回调服务
    
    管理配置变更事件的订阅和分发。
    """
    
    def __init__(self):
        """初始化回调服务"""
        self.logger = logging.getLogger(__name__)
        
        # 回调注册表，按优先级分组
        self._callbacks: Dict[CallbackPriority, List[CallbackRegistration]] = defaultdict(list)
        self._callback_lock = threading.RLock()
        
        # 回调ID映射
        self._callback_ids: Dict[str, CallbackRegistration] = {}
        self._id_counter = 0
        
        # 统计信息
        self._total_events = 0
        self._total_callbacks_executed = 0
        self._total_callback_errors = 0
        
        # 异步执行配置
        self._async_execution = True
        self._max_worker_threads = 5
        self._worker_threads: List[threading.Thread] = []
        self._task_queue: List[tuple] = []
        self._queue_lock = threading.Lock()
        self._queue_event = threading.Event()
        self._stop_workers = threading.Event()
        
        # 启动工作线程
        if self._async_execution:
            self._start_worker_threads()
    
    def register_callback(
        self,
        callback: Callable[..., None],
        priority: CallbackPriority = CallbackPriority.NORMAL,
        config_paths: Optional[List[str]] = None,
        change_types: Optional[List[Any]] = None,
        key_paths: Optional[List[str]] = None
    ) -> str:
        """注册回调函数
        
        Args:
            callback: 回调函数
            priority: 优先级
            config_paths: 只监听特定配置路径
            change_types: 只监听特定变更类型
            key_paths: 只监听特定键路径
            
        Returns:
            回调ID
        """
        with self._callback_lock:
            # 生成回调ID
            self._id_counter += 1
            callback_id = f"callback_{self._id_counter}"
            
            # 创建注册信息
            registration = CallbackRegistration(
                callback=callback,
                priority=priority,
                filter_config_paths=set(config_paths) if config_paths else None,
                filter_change_types=set(change_types) if change_types else None,
                filter_key_paths=set(key_paths) if key_paths else None
            )
            
            # 添加到注册表
            self._callbacks[priority].append(registration)
            self._callback_ids[callback_id] = registration
            
            self.logger.info(f"注册回调: {callback_id}, 优先级: {priority.name}")
            return callback_id
    
    def unregister_callback(self, callback_id: str) -> bool:
        """注销回调函数
        
        Args:
            callback_id: 回调ID
            
        Returns:
            是否成功注销
        """
        with self._callback_lock:
            registration = self._callback_ids.pop(callback_id, None)
            if registration:
                # 从优先级列表中移除
                priority_list = self._callbacks[registration.priority]
                if registration in priority_list:
                    priority_list.remove(registration)
                
                self.logger.info(f"注销回调: {callback_id}")
                return True
            return False
    
    def enable_callback(self, callback_id: str) -> bool:
        """启用回调
        
        Args:
            callback_id: 回调ID
            
        Returns:
            是否成功启用
        """
        with self._callback_lock:
            registration = self._callback_ids.get(callback_id)
            if registration:
                registration.enabled = True
                self.logger.info(f"启用回调: {callback_id}")
                return True
            return False
    
    def disable_callback(self, callback_id: str) -> bool:
        """禁用回调
        
        Args:
            callback_id: 回调ID
            
        Returns:
            是否成功禁用
        """
        with self._callback_lock:
            registration = self._callback_ids.get(callback_id)
            if registration:
                registration.enabled = False
                self.logger.info(f"禁用回调: {callback_id}")
                return True
            return False
    
    def publish_event(self, event: Any) -> None:
        """发布配置变更事件
        
        Args:
            event: 配置变更事件
        """
        self._total_events += 1
        
        if self._async_execution:
            # 异步执行
            with self._queue_lock:
                self._task_queue.append(('execute_callbacks', event))
                self._queue_event.set()
        else:
            # 同步执行
            self._execute_callbacks(event)
    
    def get_callback_info(self, callback_id: str) -> Optional[Dict[str, Any]]:
        """获取回调信息
        
        Args:
            callback_id: 回调ID
            
        Returns:
            回调信息字典
        """
        with self._callback_lock:
            registration = self._callback_ids.get(callback_id)
            if registration:
                return {
                    'callback_id': callback_id,
                    'priority': registration.priority.name,
                    'enabled': registration.enabled,
                    'filter_config_paths': list(registration.filter_config_paths) if registration.filter_config_paths else None,
                    'filter_change_types': [t.name for t in registration.filter_change_types] if registration.filter_change_types else None,
                    'filter_key_paths': list(registration.filter_key_paths) if registration.filter_key_paths else None,
                    'registration_time': registration.registration_time.isoformat(),
                    'call_count': registration.call_count,
                    'last_called': registration.last_called.isoformat() if registration.last_called else None,
                    'error_count': registration.error_count,
                    'last_error': registration.last_error
                }
            return None
    
    def get_all_callbacks(self) -> List[Optional[Dict[str, Any]]]:
        """获取所有回调信息
        
        Returns:
            回调信息列表
        """
        with self._callback_lock:
            return [self.get_callback_info(callback_id) for callback_id in self._callback_ids.keys()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._callback_lock:
            return {
                'total_events': self._total_events,
                'total_callbacks_executed': self._total_callbacks_executed,
                'total_callback_errors': self._total_callback_errors,
                'registered_callbacks': len(self._callback_ids),
                'enabled_callbacks': sum(1 for reg in self._callback_ids.values() if reg.enabled),
                'disabled_callbacks': sum(1 for reg in self._callback_ids.values() if not reg.enabled),
                'async_execution': self._async_execution,
                'worker_threads': len(self._worker_threads),
                'queue_size': len(self._task_queue)
            }
    
    def clear_all_callbacks(self) -> None:
        """清除所有回调"""
        with self._callback_lock:
            self._callbacks.clear()
            self._callback_ids.clear()
            self.logger.info("清除所有回调")
    
    def set_async_execution(self, async_execution: bool, max_worker_threads: int = 5) -> None:
        """设置异步执行模式
        
        Args:
            async_execution: 是否异步执行
            max_worker_threads: 最大工作线程数
        """
        if self._async_execution == async_execution:
            return
        
        self._async_execution = async_execution
        self._max_worker_threads = max_worker_threads
        
        if async_execution:
            self._start_worker_threads()
        else:
            self._stop_worker_threads()
        
        self.logger.info(f"设置异步执行: {async_execution}, 工作线程数: {max_worker_threads}")
    
    def _execute_callbacks(self, event: Any) -> None:
        """执行回调函数
        
        Args:
            event: 配置变更事件
        """
        with self._callback_lock:
            # 按优先级排序执行
            for priority in sorted(CallbackPriority, key=lambda x: x.value, reverse=True):
                for registration in self._callbacks[priority]:
                    if not registration.enabled:
                        continue
                    
                    # 检查过滤条件
                    if not self._should_execute_callback(registration, event):
                        continue
                    
                    # 执行回调
                    try:
                        registration.callback(event)
                        registration.call_count += 1
                        registration.last_called = datetime.now()
                        self._total_callbacks_executed += 1
                    except Exception as e:
                        registration.error_count += 1
                        registration.last_error = str(e)
                        self._total_callback_errors += 1
                        self.logger.error(f"回调执行失败: {e}")
    
    def _should_execute_callback(self, registration: CallbackRegistration, event: Any) -> bool:
        """检查是否应该执行回调
        
        Args:
            registration: 回调注册信息
            event: 配置变更事件
            
        Returns:
            是否应该执行
        """
        # 检查配置路径过滤
        if registration.filter_config_paths and event.config_path not in registration.filter_config_paths:
            return False
        
        # 检查变更类型过滤
        if registration.filter_change_types and event.change_type not in registration.filter_change_types:
            return False
        
        # 检查键路径过滤
        if registration.filter_key_paths and event.key_path:
            # 检查是否匹配任何键路径模式
            if not any(event.key_path.startswith(pattern) for pattern in registration.filter_key_paths):
                return False
        
        return True
    
    def _start_worker_threads(self) -> None:
        """启动工作线程"""
        self._stop_workers.clear()
        
        for i in range(self._max_worker_threads):
            thread = threading.Thread(target=self._worker_loop, daemon=True)
            thread.start()
            self._worker_threads.append(thread)
        
        self.logger.info(f"启动 {self._max_worker_threads} 个工作线程")
    
    def _stop_worker_threads(self) -> None:
        """停止工作线程"""
        self._stop_workers.set()
        self._queue_event.set()
        
        # 等待所有工作线程结束
        for thread in self._worker_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self._worker_threads.clear()
        self.logger.info("停止所有工作线程")
    
    def _worker_loop(self) -> None:
        """工作线程循环"""
        while not self._stop_workers.is_set():
            try:
                # 等待任务
                self._queue_event.wait(timeout=1.0)
                
                if self._stop_workers.is_set():
                    break
                
                # 获取任务
                task = None
                with self._queue_lock:
                    if self._task_queue:
                        task = self._task_queue.pop(0)
                
                if task:
                    task_type, event = task
                    if task_type == 'execute_callbacks':
                        self._execute_callbacks(event)
                
                # 重置事件
                with self._queue_lock:
                    if not self._task_queue:
                        self._queue_event.clear()
                        
            except Exception as e:
                self.logger.error(f"工作线程异常: {e}")
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, '_async_execution') and self._async_execution:
            self._stop_worker_threads()