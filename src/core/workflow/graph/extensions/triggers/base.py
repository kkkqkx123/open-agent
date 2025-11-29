"""触发器基类和接口

定义触发器的基本接口和通用功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid

from src.interfaces.state.workflow import IWorkflowState


class TriggerType(Enum):
    """触发器类型枚举"""
    TIME = "time"
    STATE = "state"
    EVENT = "event"
    CUSTOM = "custom"


@dataclass
class TriggerEvent:
    """触发器事件"""
    id: str
    trigger_id: str
    trigger_type: TriggerType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())


class ITrigger(ABC):
    """触发器接口"""

    @property
    @abstractmethod
    def trigger_id(self) -> str:
        """触发器ID"""
        pass

    @property
    @abstractmethod
    def trigger_type(self) -> TriggerType:
        """触发器类型"""
        pass

    @abstractmethod
    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估触发器是否应该触发

        Args:
            state: 当前工作流状态
            context: 上下文信息

        Returns:
            bool: 是否应该触发
        """
        pass

    @abstractmethod
    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作

        Args:
            state: 当前工作流状态
            context: 上下文信息

        Returns:
            Dict[str, Any]: 执行结果
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置

        Returns:
            Dict[str, Any]: 触发器配置
        """
        pass

    @abstractmethod
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置触发器配置

        Args:
            config: 触发器配置
        """
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """检查触发器是否启用

        Returns:
            bool: 是否启用
        """
        pass

    @abstractmethod
    def enable(self) -> None:
        """启用触发器"""
        pass

    @abstractmethod
    def disable(self) -> None:
        """禁用触发器"""
        pass
    @abstractmethod
    def create_event(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> TriggerEvent:
        """创建触发器事件

        Args:
            data: 事件数据
            metadata: 事件元数据

        Returns:
            TriggerEvent: 触发器事件
        """
        pass
    @abstractmethod
    def update_trigger_info(self) -> None:
        """更新触发器信息"""
        pass


class BaseTrigger(ITrigger):
    """触发器基类"""

    def __init__(
        self,
        trigger_id: str,
        trigger_type: TriggerType,
        config: Dict[str, Any],
        enabled: bool = True
    ) -> None:
        """初始化触发器

        Args:
            trigger_id: 触发器ID
            trigger_type: 触发器类型
            config: 触发器配置
            enabled: 是否启用
        """
        self._trigger_id = trigger_id
        self._trigger_type = trigger_type
        self._config = config
        self._enabled = enabled
        self._last_triggered: Optional[datetime] = None
        self._trigger_count = 0

    @property
    def trigger_id(self) -> str:
        """触发器ID"""
        return self._trigger_id

    @property
    def trigger_type(self) -> TriggerType:
        """触发器类型"""
        return self._trigger_type

    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        return self._config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        """设置触发器配置

        Args:
            config: 触发器配置
        """
        self._config = config.copy()

    def is_enabled(self) -> bool:
        """检查触发器是否启用"""
        return self._enabled

    def enable(self) -> None:
        """启用触发器"""
        self._enabled = True

    def disable(self) -> None:
        """禁用触发器"""
        self._enabled = False

    def update_trigger_info(self) -> None:
        """更新触发器信息"""
        self._update_trigger_info()
    def get_last_triggered(self) -> Optional[datetime]:
        """获取最后触发时间

        Returns:
            Optional[datetime]: 最后触发时间
        """
        return self._last_triggered

    def get_trigger_count(self) -> int:
        """获取触发次数

        Returns:
            int: 触发次数
        """
        return self._trigger_count

    def _update_trigger_info(self) -> None:
        """更新触发信息"""
        self._last_triggered = datetime.now()
        self._trigger_count += 1

    def _check_rate_limit(self) -> bool:
        """检查速率限制

        Returns:
            bool: 是否在速率限制内
        """
        rate_limit: Optional[float] = self._config.get("rate_limit")
        if not rate_limit:
            return True

        if self._last_triggered is None:
            return True

        time_since_last = (datetime.now() - self._last_triggered).total_seconds()
        return time_since_last >= rate_limit

    def _check_max_triggers(self) -> bool:
        """检查最大触发次数

        Returns:
            bool: 是否超过最大触发次数
        """
        max_triggers: Optional[int] = self._config.get("max_triggers")
        if not max_triggers:
            return True

        return self._trigger_count < max_triggers

    def can_trigger(self) -> bool:
        """检查是否可以触发

        Returns:
            bool: 是否可以触发
        """
        if not self._enabled:
            return False

        if not self._check_rate_limit():
            return False

        if not self._check_max_triggers():
            return False

        return True

    def create_event(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> TriggerEvent:
        """创建触发器事件

        Args:
            data: 事件数据
            metadata: 事件元数据

        Returns:
            TriggerEvent: 触发器事件
        """
        return TriggerEvent(
            id="",
            trigger_id=self._trigger_id,
            trigger_type=self._trigger_type,
            timestamp=datetime.now(),
            data=data,
            metadata=metadata or {}
        )


class TriggerHandler:
    """触发器处理器"""

    def __init__(self) -> None:
        """初始化触发器处理器"""
        self._handlers: Dict[str, List[Callable[[TriggerEvent], None]]] = {}

    def register_handler(self, trigger_type: str, handler: Callable[[TriggerEvent], None]) -> None:
        """注册触发器处理器

        Args:
            trigger_type: 触发器类型
            handler: 处理器函数
        """
        if trigger_type not in self._handlers:
            self._handlers[trigger_type] = []
        self._handlers[trigger_type].append(handler)

    def unregister_handler(self, trigger_type: str, handler: Callable[[TriggerEvent], None]) -> bool:
        """注销触发器处理器

        Args:
            trigger_type: 触发器类型
            handler: 处理器函数

        Returns:
            bool: 是否成功注销
        """
        if trigger_type in self._handlers:
            try:
                self._handlers[trigger_type].remove(handler)
                return True
            except ValueError:
                pass
        return False

    def handle_event(self, event: TriggerEvent) -> None:
        """处理触发器事件

        Args:
            event: 触发器事件
        """
        trigger_type = event.trigger_type.value
        if trigger_type in self._handlers:
            for handler in self._handlers[trigger_type]:
                try:
                    handler(event)
                except Exception:
                    # 处理器异常不应该影响其他处理器
                    pass

    def list_handlers(self) -> Dict[str, int]:
        """列出所有处理器

        Returns:
            Dict[str, int]: 处理器类型和数量映射
        """
        return {trigger_type: len(handlers) for trigger_type, handlers in self._handlers.items()}