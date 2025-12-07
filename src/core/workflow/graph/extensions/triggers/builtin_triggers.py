"""内置触发器实现

提供常用的触发器实现。
"""

import re
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from .base import BaseTrigger, TriggerType
from ..trigger_functions.impl.time_impl import TimeTriggerImplementation
from ..trigger_functions.impl.state_impl import StateTriggerImplementation
from ..trigger_functions.impl.event_impl import EventTriggerImplementation
from ..trigger_functions.impl.tool_error_impl import ToolErrorTriggerImplementation
from ..trigger_functions.impl.iteration_impl import IterationLimitTriggerImplementation

from src.interfaces.state.workflow import IWorkflowState


class TimeTrigger(BaseTrigger):
    """时间触发器"""

    def __init__(
        self,
        trigger_id: str,
        trigger_time: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化时间触发器

        Args:
            trigger_id: 触发器ID
            trigger_time: 触发时间，格式为 "HH:MM" 或间隔秒数
            config: 额外配置
        """
        super().__init__(
            trigger_id=trigger_id,
            trigger_type=TriggerType.TIME,
            config=config or {}
        )
        self._trigger_time = trigger_time
        self._next_trigger: Optional[datetime] = None
        self._calculate_next_trigger()

    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["trigger_time"] = self._trigger_time
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行评估
        return TimeTriggerImplementation.evaluate(state, context)

    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["trigger_time"] = self._trigger_time
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行执行
        result = TimeTriggerImplementation.execute(state, context)
        result["trigger_id"] = self.trigger_id
        
        # 对于间隔时间触发器，需要计算下一次触发时间
        if self._trigger_time.isdigit():
            self._calculate_next_trigger()
        
        return result

    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        config = super().get_config()
        config["trigger_time"] = self._trigger_time
        config["next_trigger"] = self._next_trigger.isoformat() if self._next_trigger else None
        return config

    def _calculate_next_trigger(self) -> None:
        """计算下一次触发时间"""
        now = datetime.now()
        
        # 检查是否为间隔时间（秒数）
        if self._trigger_time.isdigit():
            interval_seconds = int(self._trigger_time)
            if self._next_trigger is None:
                self._next_trigger = now + timedelta(seconds=interval_seconds)
            else:
                self._next_trigger = self._next_trigger + timedelta(seconds=interval_seconds)
        else:
            # 解析时间格式 "HH:MM"
            try:
                hour, minute = map(int, self._trigger_time.split(":"))
                next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 如果今天的时间已过，则设置为明天
                if next_trigger <= now:
                    next_trigger += timedelta(days=1)
                
                self._next_trigger = next_trigger
            except (ValueError, AttributeError):
                # 如果解析失败，设置为1小时后
                self._next_trigger = now + timedelta(hours=1)


class StateTrigger(BaseTrigger):
    """状态触发器"""

    def __init__(
        self,
        trigger_id: str,
        condition: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化状态触发器

        Args:
            trigger_id: 触发器ID
            condition: 状态条件表达式
            config: 额外配置
        """
        super().__init__(
            trigger_id=trigger_id,
            trigger_type=TriggerType.STATE,
            config=config or {}
        )
        self._condition = condition

    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["condition"] = self._condition
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行评估
        return StateTriggerImplementation.evaluate(state, context)

    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["condition"] = self._condition
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行执行
        result = StateTriggerImplementation.execute(state, context)
        result["trigger_id"] = self.trigger_id
        
        return result

    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        config = super().get_config()
        config["condition"] = self._condition
        return config


class EventTrigger(BaseTrigger):
    """事件触发器"""

    def __init__(
        self,
        trigger_id: str,
        event_type: str,
        event_pattern: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化事件触发器

        Args:
            trigger_id: 触发器ID
            event_type: 事件类型
            event_pattern: 事件模式（正则表达式）
            config: 额外配置
        """
        super().__init__(
            trigger_id=trigger_id,
            trigger_type=TriggerType.EVENT,
            config=config or {}
        )
        self._event_type = event_type
        self._event_pattern = event_pattern
        self._compiled_pattern = re.compile(event_pattern) if event_pattern else None

    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["event_type"] = self._event_type
        trigger_config["event_pattern"] = self._event_pattern
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行评估
        return EventTriggerImplementation.evaluate(state, context)

    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["event_type"] = self._event_type
        trigger_config["event_pattern"] = self._event_pattern
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行执行
        result = EventTriggerImplementation.execute(state, context)
        result["trigger_id"] = self.trigger_id
        
        return result

    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        config = super().get_config()
        config["event_type"] = self._event_type
        config["event_pattern"] = self._event_pattern
        return config


class CustomTrigger(BaseTrigger):
    """自定义触发器"""

    def __init__(
        self,
        trigger_id: str,
        evaluate_func: Callable[["IWorkflowState", Dict[str, Any]], bool],
        execute_func: Callable[["IWorkflowState", Dict[str, Any]], Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化自定义触发器

        Args:
            trigger_id: 触发器ID
            evaluate_func: 评估函数
            execute_func: 执行函数
            config: 额外配置
        """
        super().__init__(
            trigger_id=trigger_id,
            trigger_type=TriggerType.CUSTOM,
            config=config or {}
        )
        self._evaluate_func = evaluate_func
        self._execute_func = execute_func

    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        try:
            return self._evaluate_func(state, context)
        except Exception:
            return False

    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        try:
            result = self._execute_func(state, context)
            result["executed_at"] = datetime.now().isoformat()
            result["trigger_id"] = self.trigger_id
            return result
        except Exception as e:
            return {
                "error": str(e),
                "executed_at": datetime.now().isoformat(),
                "trigger_id": self.trigger_id,
                "message": f"自定义触发器 {self.trigger_id} 执行时出错"
            }


class ToolErrorTrigger(BaseTrigger):
    """工具错误触发器"""

    def __init__(
        self,
        trigger_id: str,
        error_threshold: int = 1,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化工具错误触发器

        Args:
            trigger_id: 触发器ID
            error_threshold: 错误阈值
            config: 额外配置
        """
        super().__init__(
            trigger_id=trigger_id,
            trigger_type=TriggerType.CUSTOM,
            config=config or {}
        )
        self._error_threshold = error_threshold

    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["error_threshold"] = self._error_threshold
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行评估
        return ToolErrorTriggerImplementation.evaluate(state, context)

    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["error_threshold"] = self._error_threshold
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行执行
        result = ToolErrorTriggerImplementation.execute(state, context)
        result["trigger_id"] = self.trigger_id
        
        return result

    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        config = super().get_config()
        config["error_threshold"] = self._error_threshold
        return config


class IterationLimitTrigger(BaseTrigger):
    """迭代限制触发器"""

    def __init__(
        self,
        trigger_id: str,
        max_iterations: int,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化迭代限制触发器

        Args:
            trigger_id: 触发器ID
            max_iterations: 最大迭代次数
            config: 额外配置
        """
        super().__init__(
            trigger_id=trigger_id,
            trigger_type=TriggerType.CUSTOM,
            config=config or {}
        )
        self._max_iterations = max_iterations

    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["max_iterations"] = self._max_iterations
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行评估
        return IterationLimitTriggerImplementation.evaluate(state, context)

    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        # 更新上下文中的触发器配置
        trigger_config = context.get("trigger_config", {})
        trigger_config["max_iterations"] = self._max_iterations
        context["trigger_config"] = trigger_config
        
        # 使用实现类进行执行
        result = IterationLimitTriggerImplementation.execute(state, context)
        result["trigger_id"] = self.trigger_id
        
        return result

    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        config = super().get_config()
        config["max_iterations"] = self._max_iterations
        return config