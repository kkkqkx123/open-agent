"""触发器系统

管理和协调所有触发器的执行。
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .base import ITrigger, TriggerEvent, TriggerHandler, TriggerType

from src.interfaces.state.workflow import IWorkflowState


class TriggerSystem:
    """触发器系统"""

    def __init__(self, max_workers: int = 4) -> None:
        """初始化触发器系统

        Args:
            max_workers: 最大工作线程数
        """
        self._triggers: Dict[str, ITrigger] = {}
        self._handler = TriggerHandler()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._system_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._event_history: List[TriggerEvent] = []
        self._max_history_size = 1000

    def register_trigger(self, trigger: ITrigger) -> bool:
        """注册触发器

        Args:
            trigger: 触发器实例

        Returns:
            bool: 是否成功注册
        """
        with self._lock:
            if trigger.trigger_id in self._triggers:
                return False
            
            self._triggers[trigger.trigger_id] = trigger
            return True

    def unregister_trigger(self, trigger_id: str) -> bool:
        """注销触发器

        Args:
            trigger_id: 触发器ID

        Returns:
            bool: 是否成功注销
        """
        with self._lock:
            if trigger_id in self._triggers:
                del self._triggers[trigger_id]
                return True
            return False

    def get_trigger(self, trigger_id: str) -> Optional[ITrigger]:
        """获取触发器

        Args:
            trigger_id: 触发器ID

        Returns:
            Optional[ITrigger]: 触发器实例
        """
        with self._lock:
            return self._triggers.get(trigger_id)

    def list_triggers(self) -> List[Dict[str, Any]]:
        """列出所有触发器

        Returns:
            List[Dict[str, Any]]: 触发器信息列表
        """
        with self._lock:
            return [
                {
                    "id": trigger.trigger_id,
                    "type": trigger.trigger_type.value,
                    "enabled": trigger.is_enabled(),
                    "config": trigger.get_config(),
                    "last_triggered": getattr(trigger, 'get_last_triggered', lambda: None)(),
                    "trigger_count": getattr(trigger, 'get_trigger_count', lambda: 0)()
                }
                for trigger in self._triggers.values()
            ]

    def enable_trigger(self, trigger_id: str) -> bool:
        """启用触发器

        Args:
            trigger_id: 触发器ID

        Returns:
            bool: 是否成功启用
        """
        with self._lock:
            trigger = self._triggers.get(trigger_id)
            if trigger:
                trigger.enable()
                return True
            return False

    def disable_trigger(self, trigger_id: str) -> bool:
        """禁用触发器

        Args:
            trigger_id: 触发器ID

        Returns:
            bool: 是否成功禁用
        """
        with self._lock:
            trigger = self._triggers.get(trigger_id)
            if trigger:
                trigger.disable()
                return True
            return False

    def evaluate_triggers(self, state: "IWorkflowState", context: Dict[str, Any]) -> List[TriggerEvent]:
        """评估所有触发器

        Args:
            state: 当前工作流状态
            context: 上下文信息

        Returns:
            List[TriggerEvent]: 触发的事件列表
        """
        events = []
        
        with self._lock:
            for trigger in self._triggers.values():
                if not trigger.is_enabled():
                    continue
                
                try:
                    if trigger.evaluate(state, context):
                        # 执行触发器
                        result = trigger.execute(state, context)
                        
                        # 创建事件
                        event = trigger.create_event(
                            data={"result": result},
                            metadata={
                                "state_id": id(state),
                                "context_keys": list(context.keys())
                            }
                        )
                        
                        events.append(event)
                        self._add_event_to_history(event)
                        
                        # 更新触发器信息
                        trigger.update_trigger_info()
                    
                except Exception as e:
                    # 记录错误但不中断其他触发器
                    from .base import TriggerEvent
                    error_event = TriggerEvent(
                        id="",
                        trigger_id=trigger.trigger_id,
                        trigger_type=trigger.trigger_type,
                        timestamp=datetime.now(),
                        data={"error": str(e)},
                        metadata={"error_type": type(e).__name__}
                    )
                    events.append(error_event)
                    self._add_event_to_history(error_event)
        
        return events

    def start(self) -> None:
        """启动触发器系统"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._system_thread = threading.Thread(target=self._system_loop, daemon=True)
            self._system_thread.start()

    def stop(self) -> None:
        """停止触发器系统"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._system_thread:
                self._system_thread.join(timeout=5)
                self._system_thread = None

    def is_running(self) -> bool:
        """检查系统是否正在运行

        Returns:
            bool: 是否正在运行
        """
        return self._running

    def register_event_handler(self, trigger_type: TriggerType, handler: Callable[[TriggerEvent], None]) -> None:
        """注册事件处理器

        Args:
            trigger_type: 触发器类型
            handler: 处理器函数
        """
        self._handler.register_handler(trigger_type.value, handler)

    def unregister_event_handler(self, trigger_type: TriggerType, handler: Callable[[TriggerEvent], None]) -> bool:
        """注销事件处理器

        Args:
            trigger_type: 触发器类型
            handler: 处理器函数

        Returns:
            bool: 是否成功注销
        """
        return self._handler.unregister_handler(trigger_type.value, handler)

    def get_event_history(self, limit: Optional[int] = None) -> List[TriggerEvent]:
        """获取事件历史

        Args:
            limit: 限制返回的事件数量

        Returns:
            List[TriggerEvent]: 事件历史列表
        """
        with self._lock:
            history = self._event_history.copy()
            if limit:
                history = history[-limit:]
            return history

    def clear_event_history(self) -> None:
        """清除事件历史"""
        with self._lock:
            self._event_history.clear()

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total_triggers = len(self._triggers)
            enabled_triggers = sum(1 for t in self._triggers.values() if t.is_enabled())
            total_events = len(self._event_history)
            
            # 按类型统计触发器
            trigger_types = {}
            for trigger in self._triggers.values():
                trigger_type = trigger.trigger_type.value
                if trigger_type not in trigger_types:
                    trigger_types[trigger_type] = {"total": 0, "enabled": 0}
                trigger_types[trigger_type]["total"] += 1
                if trigger.is_enabled():
                    trigger_types[trigger_type]["enabled"] += 1
            
            # 按类型统计事件
            event_types = {}
            for event in self._event_history:
                event_type = event.trigger_type.value
                if event_type not in event_types:
                    event_types[event_type] = 0
                event_types[event_type] += 1
            
            return {
                "system_running": self._running,
                "total_triggers": total_triggers,
                "enabled_triggers": enabled_triggers,
                "total_events": total_events,
                "trigger_types": trigger_types,
                "event_types": event_types,
                "max_history_size": self._max_history_size,
                "handlers": self._handler.list_handlers()
            }

    def _system_loop(self) -> None:
        """系统主循环"""
        while self._running:
            try:
                # 这里可以添加定期检查逻辑
                # 例如检查时间触发器等
                time.sleep(1)
            except Exception:
                # 系统循环异常不应该停止系统
                pass

    def _add_event_to_history(self, event: TriggerEvent) -> None:
        """添加事件到历史记录

        Args:
            event: 触发器事件
        """
        self._event_history.append(event)
        
        # 限制历史记录大小
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
        
        # 处理事件
        self._handler.handle_event(event)

    def __enter__(self) -> "TriggerSystem":
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口"""
        self.stop()


class WorkflowTriggerSystem(TriggerSystem):
    """工作流触发器系统"""

    def __init__(self, workflow_manager: Any, max_workers: int = 4) -> None:
        """初始化工作流触发器系统

        Args:
            workflow_manager: 工作流管理器
            max_workers: 最大工作线程数
        """
        super().__init__(max_workers)
        self.workflow_manager = workflow_manager

    def evaluate_workflow_triggers(self, workflow_id: str, state: "IWorkflowState") -> List[TriggerEvent]:
        """评估工作流触发器

        Args:
            workflow_id: 工作流ID
            state: 当前工作流状态

        Returns:
            List[TriggerEvent]: 触发的事件列表
        """
        context = {
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.evaluate_triggers(state, context)

    def register_workflow_trigger(self, workflow_id: str, trigger: ITrigger) -> bool:
        """注册工作流触发器

        Args:
            workflow_id: 工作流ID
            trigger: 触发器实例

        Returns:
            bool: 是否成功注册
        """
        # 为触发器添加工作流上下文
        config = trigger.get_config()
        config["workflow_id"] = workflow_id
        trigger.set_config(config)
        return self.register_trigger(trigger)

    def unregister_workflow_trigger(self, workflow_id: str, trigger_id: str) -> bool:
        """注销工作流触发器

        Args:
            workflow_id: 工作流ID
            trigger_id: 触发器ID

        Returns:
            bool: 是否成功注销
        """
        trigger = self.get_trigger(trigger_id)
        if trigger and trigger.get_config().get("workflow_id") == workflow_id:
            return self.unregister_trigger(trigger_id)
        return False

    def get_workflow_triggers(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取工作流触发器

        Args:
            workflow_id: 工作流ID

        Returns:
            List[Dict[str, Any]]: 触发器列表
        """
        return [
            trigger_info
            for trigger_info in self.list_triggers()
            if trigger_info["config"].get("workflow_id") == workflow_id
        ]