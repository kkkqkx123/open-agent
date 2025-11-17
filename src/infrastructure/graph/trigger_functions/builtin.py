"""内置触发器函数

提供系统内置的常用触发器函数。
"""

from typing import Dict, Any, Callable
from datetime import datetime, timedelta
import time
import re

from ..states import WorkflowState


class BuiltinTriggerFunctions:
    """内置触发器函数集合"""
    
    # ==================== 评估函数 ====================
    
    @staticmethod
    def time_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """时间触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = context.get("trigger_config", {})
        trigger_time = trigger_config.get("trigger_time")
        
        if not trigger_time:
            return False
        
        now = datetime.now()
        
        # 检查是否为间隔时间（秒数）
        if trigger_time.isdigit():
            interval_seconds = int(trigger_time)
            last_triggered = trigger_config.get("last_triggered")
            
            if not last_triggered:
                return True
            
            last_time = datetime.fromisoformat(last_triggered) if isinstance(last_triggered, str) else last_triggered
            return (now - last_time).total_seconds() >= interval_seconds
        else:
            # 解析时间格式 "HH:MM"
            try:
                hour, minute = map(int, trigger_time.split(":"))
                next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 如果今天的时间已过，则设置为明天
                if next_trigger <= now:
                    next_trigger += timedelta(days=1)
                
                last_triggered = trigger_config.get("last_triggered")
                if not last_triggered:
                    return True
                
                last_time = datetime.fromisoformat(last_triggered) if isinstance(last_triggered, str) else last_triggered
                return now >= next_trigger and now.date() >= last_time.date()
            except (ValueError, AttributeError):
                return False
    
    @staticmethod
    def state_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """状态触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = context.get("trigger_config", {})
        condition = trigger_config.get("condition")
        
        if not condition:
            return False
        
        try:
            # 创建安全的执行环境
            safe_globals = {
                "__rests__": {
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
            result = eval(condition, safe_globals)
            return bool(result)
            
        except Exception:
            return False
    
    @staticmethod
    def event_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """事件触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = context.get("trigger_config", {})
        event_type = trigger_config.get("event_type")
        event_pattern = trigger_config.get("event_pattern")
        
        if not event_type:
            return False
        
        # 检查上下文中是否有匹配的事件
        events = context.get("events", [])
        
        for event in events:
            if event.get("type") == event_type:
                if event_pattern:
                    # 检查事件内容是否匹配模式
                    event_data = str(event.get("data", ""))
                    if re.search(event_pattern, event_data):
                        return True
                else:
                    # 没有模式，只要事件类型匹配就触发
                    return True
        
        return False
    
    @staticmethod
    def tool_error_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """工具错误触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = context.get("trigger_config", {})
        error_threshold = trigger_config.get("error_threshold", 1)
        
        # 计算工具错误数量
        tool_results = state.get("tool_results", [])
        error_count = sum(1 for result in tool_results if not result.get("success", True))
        return error_count >= error_threshold
    
    @staticmethod
    def iteration_limit_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """迭代限制触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = context.get("trigger_config", {})
        max_iterations = trigger_config.get("max_iterations", 10)
        
        iteration_count = state.get("iteration_count", 0)
        return iteration_count >= max_iterations
    
    # ==================== 执行函数 ====================
    
    @staticmethod
    def time_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """时间触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        trigger_config = context.get("trigger_config", {})
        trigger_time = trigger_config.get("trigger_time")
        
        return {
            "trigger_time": trigger_time,
            "executed_at": datetime.now().isoformat(),
            "message": f"时间触发器执行，触发时间: {trigger_time}"
        }
    
    @staticmethod
    def state_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """状态触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        trigger_config = context.get("trigger_config", {})
        condition = trigger_config.get("condition")
        
        return {
            "condition": condition,
            "executed_at": datetime.now().isoformat(),
            "state_summary": {
                "messages_count": len(state.get("messages", [])),
                "tool_results_count": len(state.get("tool_results", [])),
                "current_step": state.get("current_step", ""),
                "iteration_count": state.get("iteration_count", 0)
            },
            "message": "状态触发器执行"
        }
    
    @staticmethod
    def event_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """事件触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        trigger_config = context.get("trigger_config", {})
        event_type = trigger_config.get("event_type")
        event_pattern = trigger_config.get("event_pattern")
        
        # 查找匹配的事件
        matching_events = []
        events = context.get("events", [])
        
        for event in events:
            if event.get("type") == event_type:
                if event_pattern:
                    event_data = str(event.get("data", ""))
                    if re.search(event_pattern, event_data):
                        matching_events.append(event)
                else:
                    matching_events.append(event)
        
        return {
            "event_type": event_type,
            "event_pattern": event_pattern,
            "matching_events": matching_events,
            "executed_at": datetime.now().isoformat(),
            "message": f"事件触发器执行，匹配事件数: {len(matching_events)}"
        }
    
    @staticmethod
    def tool_error_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """工具错误触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        trigger_config = context.get("trigger_config", {})
        error_threshold = trigger_config.get("error_threshold", 1)
        
        # 统计错误信息
        tool_results = state.get("tool_results", [])
        error_results = [result for result in tool_results if not result.get("success", True)]
        error_summary = {}
        
        for result in error_results:
            tool_name = result.get("tool_name", "unknown")
            if tool_name not in error_summary:
                error_summary[tool_name] = {"count": 0, "errors": []}
            error_summary[tool_name]["count"] += 1
            error_summary[tool_name]["errors"].append(result.get("error", "Unknown error"))
        
        return {
            "error_threshold": error_threshold,
            "error_count": len(error_results),
            "error_summary": error_summary,
            "executed_at": datetime.now().isoformat(),
            "message": f"工具错误触发器执行，错误数: {len(error_results)}"
        }
    
    @staticmethod
    def iteration_limit_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """迭代限制触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        trigger_config = context.get("trigger_config", {})
        max_iterations = trigger_config.get("max_iterations", 10)
        
        iteration_count = state.get("iteration_count", 0)
        
        return {
            "max_iterations": max_iterations,
            "current_iterations": iteration_count,
            "executed_at": datetime.now().isoformat(),
            "message": f"迭代限制触发器执行，当前迭代: {iteration_count}/{max_iterations}"
        }
    
    @classmethod
    def get_all_evaluate_functions(cls) -> Dict[str, Callable]:
        """获取所有评估函数
        
        Returns:
            Dict[str, Callable]: 评估函数字典
        """
        return {
            "time_evaluate": cls.time_evaluate,
            "state_evaluate": cls.state_evaluate,
            "event_evaluate": cls.event_evaluate,
            "tool_error_evaluate": cls.tool_error_evaluate,
            "iteration_limit_evaluate": cls.iteration_limit_evaluate,
        }
    
    @classmethod
    def get_all_execute_functions(cls) -> Dict[str, Callable]:
        """获取所有执行函数
        
        Returns:
            Dict[str, Callable]: 执行函数字典
        """
        return {
            "time_execute": cls.time_execute,
            "state_execute": cls.state_execute,
            "event_execute": cls.event_execute,
            "tool_error_execute": cls.tool_error_execute,
            "iteration_limit_execute": cls.iteration_limit_execute,
        }
    
    @classmethod
    def get_all_functions(cls) -> Dict[str, Callable]:
        """获取所有函数
        
        Returns:
            Dict[str, Callable]: 函数字典
        """
        all_functions = {}
        all_functions.update(cls.get_all_evaluate_functions())
        all_functions.update(cls.get_all_execute_functions())
        return all_functions