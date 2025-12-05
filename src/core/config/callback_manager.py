"""配置回调管理器

为配置系统提供回调管理功能，支持配置变化事件通知。
"""

from src.services.logger.injection import get_logger
import threading
from typing import Dict, Any, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.interfaces.configuration import ConfigError
from src.infrastructure.error_management import handle_error, ErrorCategory, ErrorSeverity

logger = get_logger(__name__)


class CallbackPriority(Enum):
    """回调优先级"""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class ConfigChangeContext:
    """配置变更上下文"""

    config_path: str
    old_config: Optional[Dict[str, Any]]
    new_config: Dict[str, Any]
    timestamp: datetime
    source: str = "file_watcher"  # 变更来源

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config_path": self.config_path,
            "old_config": self.old_config,
            "new_config": self.new_config,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }


@dataclass
class ConfigCallback:
    """配置回调"""

    id: str
    callback: Callable[[ConfigChangeContext], None]
    priority: CallbackPriority = CallbackPriority.NORMAL
    once: bool = False  # 是否只执行一次
    filter_paths: Optional[List[str]] = None  # 路径过滤器
    enabled: bool = True
    _executed: bool = False  # 是否已经执行过（内部使用）

    def should_execute(self, config_path: str) -> bool:
        """检查是否应该执行回调"""
        if not self.enabled:
            return False

        # 如果是一次性回调且已经执行过，则不再执行
        if self.once and self._executed:
            return False

        if self.filter_paths:
            import fnmatch
            import os

            # 获取文件名（不含路径）
            filename = os.path.basename(config_path)

            for path_pattern in self.filter_paths:
                # 如果模式包含路径分隔符，使用完整路径匹配
                if "/" in path_pattern or "\\" in path_pattern:
                    if fnmatch.fnmatch(
                        config_path.replace("\\", "/"), path_pattern.replace("\\", "/")
                    ):
                        return True
                else:
                    # 如果模式只是文件名模式，只匹配文件名，且路径不能包含目录分隔符
                    if "/" not in config_path and "\\" not in config_path:
                        if fnmatch.fnmatch(filename, path_pattern):
                            return True
            return False

        return True


class ConfigCallbackManager:
    """配置回调管理器"""

    def __init__(self) -> None:
        """初始化回调管理器"""
        self._callbacks: Dict[str, ConfigCallback] = {}
        self._execution_order: List[str] = []
        self._lock = threading.RLock()
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history = 1000

    def register_callback(
        self,
        callback_id: str,
        callback: Callable[[ConfigChangeContext], None],
        priority: CallbackPriority = CallbackPriority.NORMAL,
        once: bool = False,
        filter_paths: Optional[List[str]] = None,
    ) -> None:
        """注册配置变更回调

        Args:
            callback_id: 回调ID
            callback: 回调函数
            priority: 优先级
            once: 是否只执行一次
            filter_paths: 路径过滤器

        Raises:
            ConfigError: 回调ID已存在
        """
        with self._lock:
            if callback_id in self._callbacks:
                raise ConfigError(f"回调ID已存在: {callback_id}")

            # 创建回调对象
            config_callback = ConfigCallback(
                id=callback_id,
                callback=callback,
                priority=priority,
                once=once,
                filter_paths=filter_paths,
            )

            # 添加回调
            self._callbacks[callback_id] = config_callback

            # 更新执行顺序
            self._update_execution_order()

    def unregister_callback(self, callback_id: str) -> bool:
        """注销配置变更回调

        Args:
            callback_id: 回调ID

        Returns:
            是否成功注销
        """
        with self._lock:
            if callback_id in self._callbacks:
                del self._callbacks[callback_id]
                self._update_execution_order()
                return True
            return False

    def enable_callback(self, callback_id: str) -> bool:
        """启用回调

        Args:
            callback_id: 回调ID

        Returns:
            是否成功启用
        """
        with self._lock:
            if callback_id in self._callbacks:
                self._callbacks[callback_id].enabled = True
                return True
            return False

    def disable_callback(self, callback_id: str) -> bool:
        """禁用回调

        Args:
            callback_id: 回调ID

        Returns:
            是否成功禁用
        """
        with self._lock:
            if callback_id in self._callbacks:
                self._callbacks[callback_id].enabled = False
                return True
            return False

    def trigger_callbacks(
        self,
        config_path: str,
        old_config: Optional[Dict[str, Any]],
        new_config: Dict[str, Any],
        source: str = "file_watcher",
    ) -> None:
        """触发配置变更回调

        Args:
            config_path: 配置文件路径
            old_config: 旧配置
            new_config: 新配置
            source: 变更来源
        """
        # 创建变更上下文
        context = ConfigChangeContext(
            config_path=config_path,
            old_config=old_config,
            new_config=new_config,
            timestamp=datetime.now(),
            source=source,
        )

        # 记录执行历史
        self._record_execution_start(context)

        # 按优先级顺序执行回调
        callbacks_to_remove = []

        with self._lock:
            # 首先检查并移除已执行的一次性回调
            for callback_id in list(self._execution_order):
                if callback_id in self._callbacks:
                    callback = self._callbacks[callback_id]
                    if callback.once and callback._executed:
                        callbacks_to_remove.append(callback_id)

            # 移除已执行的一次性回调
            for callback_id in callbacks_to_remove:
                self.unregister_callback(callback_id)

            callbacks_to_remove = []  # 重置列表

            # 然后执行剩余的回调
            for callback_id in self._execution_order:
                callback = self._callbacks[callback_id]

                # 检查是否应该执行
                if not callback.should_execute(config_path):
                    continue

                try:
                    # 执行回调
                    callback.callback(context)

                    # 记录成功执行
                    self._record_execution_success(callback_id, context)

                    # 如果是一次性回调，标记为已执行
                    if callback.once:
                        callback._executed = True

                except Exception as e:
                    # 记录执行失败
                    self._record_execution_error(callback_id, context, e)
                    
                    # 使用统一错误处理，添加配置相关的上下文信息
                    error_context = {
                        "callback_id": callback_id,
                        "config_path": config_path,
                        "callback_priority": callback.priority.name,
                        "callback_once": callback.once,
                        "execution_order": self._execution_order.index(callback_id) if callback_id in self._execution_order else -1,
                        "total_callbacks": len(self._execution_order),
                        "module": "config_callback_manager",
                        "operation": "callback_execution",
                        "error_category": "configuration" if isinstance(e, ConfigError) else "callback"
                    }
                    
                    handle_error(e, error_context)
                    
                    # 根据错误严重程度决定是否继续执行其他回调
                    if isinstance(e, (KeyboardInterrupt, SystemExit, MemoryError)):
                        # 严重错误，停止执行后续回调
                        logger.error(f"回调 {callback_id} 遇到严重错误，停止执行后续回调: {e}")
                        break
                    else:
                        # 一般错误，记录但继续执行
                        logger.warning(f"回调 {callback_id} 执行失败，继续执行下一个回调: {e}")

    def _update_execution_order(self) -> None:
        """更新回调执行顺序（按优先级排序）"""
        # 按优先级降序排序
        sorted_callbacks = sorted(
            self._callbacks.items(), key=lambda x: x[1].priority.value, reverse=True
        )
        self._execution_order = [callback_id for callback_id, _ in sorted_callbacks]

    def _record_execution_start(self, context: ConfigChangeContext) -> None:
        """记录执行开始"""
        execution_record = {
            "timestamp": context.timestamp.isoformat(),
            "config_path": context.config_path,
            "source": context.source,
            "status": "started",
            "callbacks": [],
        }

        with self._lock:
            self._execution_history.append(execution_record)
            self._trim_history()

    def _record_execution_success(
        self, callback_id: str, context: ConfigChangeContext
    ) -> None:
        """记录执行成功"""
        with self._lock:
            if self._execution_history:
                last_record = self._execution_history[-1]
                if (
                    last_record["config_path"] == context.config_path
                    and last_record["timestamp"] == context.timestamp.isoformat()
                ):
                    last_record["callbacks"].append(
                        {"callback_id": callback_id, "status": "success"}
                    )

    def _record_execution_error(
        self, callback_id: str, context: ConfigChangeContext, error: Exception
    ) -> None:
        """记录执行错误"""
        with self._lock:
            if self._execution_history:
                last_record = self._execution_history[-1]
                if (
                    last_record["config_path"] == context.config_path
                    and last_record["timestamp"] == context.timestamp.isoformat()
                ):
                    last_record["callbacks"].append(
                        {
                            "callback_id": callback_id,
                            "status": "error",
                            "error": str(error),
                        }
                    )

    def _trim_history(self) -> None:
        """修剪历史记录"""
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history :]

    def get_callback_info(self, callback_id: str) -> Optional[Dict[str, Any]]:
        """获取回调信息

        Args:
            callback_id: 回调ID

        Returns:
            回调信息字典
        """
        with self._lock:
            if callback_id in self._callbacks:
                callback = self._callbacks[callback_id]
                return {
                    "id": callback.id,
                    "priority": callback.priority.name,
                    "once": callback.once,
                    "filter_paths": callback.filter_paths,
                    "enabled": callback.enabled,
                }
            return None

    def list_callbacks(self) -> List[Dict[str, Any]]:
        """列出所有回调

        Returns:
            回调信息列表
        """
        with self._lock:
            return [
                {
                    "id": callback.id,
                    "priority": callback.priority.name,
                    "once": callback.once,
                    "filter_paths": callback.filter_paths,
                    "enabled": callback.enabled,
                }
                for callback in self._callbacks.values()
            ]

    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取执行历史

        Args:
            limit: 返回记录数限制

        Returns:
            执行历史列表
        """
        with self._lock:
            return self._execution_history[-limit:]

    def clear_execution_history(self) -> None:
        """清除执行历史"""
        with self._lock:
            self._execution_history.clear()


# 全局回调管理器实例
_global_callback_manager: Optional[ConfigCallbackManager] = None


def get_global_callback_manager() -> ConfigCallbackManager:
    """获取全局回调管理器实例

    Returns:
        全局回调管理器实例
    """
    global _global_callback_manager
    if _global_callback_manager is None:
        _global_callback_manager = ConfigCallbackManager()
    return _global_callback_manager


def register_config_callback(
    callback_id: str,
    callback: Callable[[ConfigChangeContext], None],
    priority: CallbackPriority = CallbackPriority.NORMAL,
    once: bool = False,
    filter_paths: Optional[List[str]] = None,
) -> None:
    """注册配置变更回调的便捷函数

    Args:
        callback_id: 回调ID
        callback: 回调函数
        priority: 优先级
        once: 是否只执行一次
        filter_paths: 路径过滤器
    """
    get_global_callback_manager().register_callback(
        callback_id, callback, priority, once, filter_paths
    )


def unregister_config_callback(callback_id: str) -> bool:
    """注销配置变更回调的便捷函数

    Args:
        callback_id: 回调ID

    Returns:
        是否成功注销
    """
    return get_global_callback_manager().unregister_callback(callback_id)


def trigger_config_callbacks(
    config_path: str,
    old_config: Optional[Dict[str, Any]],
    new_config: Dict[str, Any],
    source: str = "file_watcher",
) -> None:
    """触发配置变更回调的便捷函数

    Args:
        config_path: 配置文件路径
        old_config: 旧配置
        new_config: 新配置
        source: 变更来源
    """
    get_global_callback_manager().trigger_callbacks(
        config_path, old_config, new_config, source
    )


# 便捷函数
def create_callback_manager() -> ConfigCallbackManager:
    """创建回调管理器的便捷函数
    
    Returns:
        回调管理器实例
    """
    return ConfigCallbackManager()