"""内置触发器实现

提供常用的触发器实现。
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import time
import re

from .base import BaseTrigger, TriggerType
from src.domain.agent.state import AgentState


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

    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        now = datetime.now()
        
        # 检查是否到了触发时间
        if self._next_trigger and now >= self._next_trigger:
            # 计算下一次触发时间
            self._calculate_next_trigger()
            return True
        
        return False

    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        return {
            "trigger_time": self._trigger_time,
            "executed_at": datetime.now().isoformat(),
            "message": f"时间触发器 {self.trigger_id} 执行"
        }

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

    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        try:
            # 创建安全的执行环境
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "any": any,
                    "all": all,
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "sum": sum,
                },
                "state": state,
                "context": context,
            }
            
            # 执行条件表达式
            result = eval(self._condition, safe_globals)
            return bool(result)
            
        except Exception:
            return False

    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        return {
            "condition": self._condition,
            "executed_at": datetime.now().isoformat(),
            "state_summary": {
                "messages_count": len(state.messages),
                "tool_results_count": len(state.tool_results),
                "current_step": getattr(state, 'current_step', ''),
                "iteration_count": getattr(state, 'iteration_count', 0)
            },
            "message": f"状态触发器 {self.trigger_id} 执行"
        }

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

    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        # 检查上下文中是否有匹配的事件
        events = context.get("events", [])
        
        for event in events:
            if event.get("type") == self._event_type:
                if self._event_pattern:
                    # 检查事件内容是否匹配模式
                    event_data = str(event.get("data", ""))
                    if self._compiled_pattern and self._compiled_pattern.search(event_data):
                        return True
                else:
                    # 没有模式，只要事件类型匹配就触发
                    return True
        
        return False

    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        # 查找匹配的事件
        matching_events = []
        events = context.get("events", [])
        
        for event in events:
            if event.get("type") == self._event_type:
                if self._event_pattern:
                    event_data = str(event.get("data", ""))
                    if self._compiled_pattern and self._compiled_pattern.search(event_data):
                        matching_events.append(event)
                else:
                    matching_events.append(event)
        
        return {
            "event_type": self._event_type,
            "event_pattern": self._event_pattern,
            "matching_events": matching_events,
            "executed_at": datetime.now().isoformat(),
            "message": f"事件触发器 {self.trigger_id} 执行"
        }

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
        evaluate_func: Callable[[AgentState, Dict[str, Any]], bool],
        execute_func: Callable[[AgentState, Dict[str, Any]], Dict[str, Any]],
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

    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        try:
            return self._evaluate_func(state, context)
        except Exception:
            return False

    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
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

    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        # 计算工具错误数量
        error_count = sum(1 for result in state.tool_results if not result.success)
        return error_count >= self._error_threshold

    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        # 统计错误信息
        error_results = [result for result in state.tool_results if not result.success]
        error_summary = {}
        
        for result in error_results:
            tool_name = result.tool_name
            if tool_name not in error_summary:
                error_summary[tool_name] = {"count": 0, "errors": []}
            error_summary[tool_name]["count"] += 1
            error_summary[tool_name]["errors"].append(result.error)
        
        return {
            "error_threshold": self._error_threshold,
            "error_count": len(error_results),
            "error_summary": error_summary,
            "executed_at": datetime.now().isoformat(),
            "message": f"工具错误触发器 {self.trigger_id} 执行"
        }

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

    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发"""
        if not self.can_trigger():
            return False

        iteration_count = getattr(state, 'iteration_count', 0)
        return iteration_count >= self._max_iterations

    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        self._update_trigger_info()
        
        iteration_count = getattr(state, 'iteration_count', 0)
        
        return {
            "max_iterations": self._max_iterations,
            "current_iterations": iteration_count,
            "executed_at": datetime.now().isoformat(),
            "message": f"迭代限制触发器 {self.trigger_id} 执行"
        }

    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        config = super().get_config()
        config["max_iterations"] = self._max_iterations
        return config