"""触发器工厂

提供基于函数组合创建触发器的工厂方法。
"""

from typing import Dict, Any, Optional, List, cast
from src.interfaces.dependency_injection import get_logger

from .base import ITrigger, TriggerType
from .builtin_triggers import (
    TimeTrigger,
    StateTrigger,
    EventTrigger,
    CustomTrigger,
    ToolErrorTrigger,
    IterationLimitTrigger
)
# 导入新的监控触发器
from .timing import (
    ToolExecutionTimingTrigger,
    LLMResponseTimingTrigger,
    WorkflowStateTimingTrigger
)
from .state_monitoring import (
    WorkflowStateCaptureTrigger,
    WorkflowStateChangeTrigger,
    WorkflowErrorStateTrigger
)
from .pattern_matching import (
    UserInputPatternTrigger,
    LLMOutputPatternTrigger,
    ToolOutputPatternTrigger,
    StatePatternTrigger
)
from src.core.workflow.graph.extensions.trigger_functions import get_trigger_function_manager, TriggerCompositionConfig

logger = get_logger(__name__)


class TriggerFactory:
    """触发器工厂
    
    提供创建各种类型触发器的工厂方法，支持基于函数组合的灵活创建。
    """
    
    def __init__(self) -> None:
        """初始化触发器工厂"""
        self.function_manager = get_trigger_function_manager()
    
    def create_trigger(
        self,
        trigger_id: str,
        trigger_type: TriggerType,
        config: Dict[str, Any],
        evaluate_function: Optional[str] = None,
        execute_function: Optional[str] = None
    ) -> ITrigger:
        """创建触发器
        
        Args:
            trigger_id: 触发器ID
            trigger_type: 触发器类型
            config: 触发器配置
            evaluate_function: 评估函数名称（可选）
            execute_function: 执行函数名称（可选）
            
        Returns:
            ITrigger: 触发器实例
            
        Raises:
            ValueError: 创建失败时抛出异常
        """
        if trigger_type == TriggerType.TIME:
            return cast(ITrigger, self._create_time_trigger(trigger_id, config))
        elif trigger_type == TriggerType.STATE:
            return cast(ITrigger, self._create_state_trigger(trigger_id, config))
        elif trigger_type == TriggerType.EVENT:
            return cast(ITrigger, self._create_event_trigger(trigger_id, config))
        elif trigger_type == TriggerType.CUSTOM:
            return cast(ITrigger, self._create_custom_trigger(trigger_id, config, evaluate_function, execute_function))
        else:
            raise ValueError(f"不支持的触发器类型: {trigger_type}")
    
    def create_monitoring_trigger(
        self,
        trigger_id: str,
        trigger_class: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ITrigger:
        """创建监控触发器
        
        Args:
            trigger_id: 触发器ID
            trigger_class: 触发器类名
            config: 触发器配置
            
        Returns:
            ITrigger: 触发器实例
            
        Raises:
            ValueError: 创建失败时抛出异常
        """
        if config is None:
            config = {}
        
        # 计时触发器
        if trigger_class == "ToolExecutionTimingTrigger":
            return ToolExecutionTimingTrigger(trigger_id, config)
        elif trigger_class == "LLMResponseTimingTrigger":
            return LLMResponseTimingTrigger(trigger_id, config)
        elif trigger_class == "WorkflowStateTimingTrigger":
            return WorkflowStateTimingTrigger(trigger_id, config)
        
        # 状态监控触发器
        elif trigger_class == "WorkflowStateCaptureTrigger":
            return WorkflowStateCaptureTrigger(trigger_id, config)
        elif trigger_class == "WorkflowStateChangeTrigger":
            return WorkflowStateChangeTrigger(trigger_id, config)
        elif trigger_class == "WorkflowErrorStateTrigger":
            return WorkflowErrorStateTrigger(trigger_id, config)
        
        # 模式匹配触发器
        elif trigger_class == "UserInputPatternTrigger":
            return UserInputPatternTrigger(trigger_id, config)
        elif trigger_class == "LLMOutputPatternTrigger":
            return LLMOutputPatternTrigger(trigger_id, config)
        elif trigger_class == "ToolOutputPatternTrigger":
            return ToolOutputPatternTrigger(trigger_id, config)
        elif trigger_class == "StatePatternTrigger":
            return StatePatternTrigger(trigger_id, config)
        
        else:
            raise ValueError(f"不支持的监控触发器类: {trigger_class}")
    
    def create_trigger_from_composition(
        self,
        trigger_id: str,
        composition_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ITrigger:
        """从组合创建触发器
        
        Args:
            trigger_id: 触发器ID
            composition_name: 组合名称
            config: 触发器配置（可选）
            
        Returns:
            ITrigger: 触发器实例
            
        Raises:
            ValueError: 创建失败时抛出异常
        """
        trigger = self.function_manager.create_trigger_from_composition(
            composition_name, trigger_id, config
        )
        
        if not trigger:
            raise ValueError(f"无法从组合创建触发器: {composition_name}")
        
        return cast(ITrigger, trigger)
    
    def _create_time_trigger(self, trigger_id: str, config: Dict[str, Any]) -> TimeTrigger:
        """创建时间触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
            
        Returns:
            TimeTrigger: 时间触发器实例
        """
        trigger_time = config.get("trigger_time", "60")  # 默认60秒间隔
        
        return TimeTrigger(
            trigger_id=trigger_id,
            trigger_time=trigger_time,
            config=config
        )
    
    def _create_state_trigger(self, trigger_id: str, config: Dict[str, Any]) -> ITrigger:
        """创建状态触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
            
        Returns:
            ITrigger: 状态触发器实例
        """
        # 检查是否是特殊的状态触发器
        special_type = config.get("special_type")
        
        if special_type == "state_capture":
            return cast(ITrigger, WorkflowStateCaptureTrigger(trigger_id, config))
        elif special_type == "state_change":
            return cast(ITrigger, WorkflowStateChangeTrigger(trigger_id, config))
        elif special_type == "error_state":
            return cast(ITrigger, WorkflowErrorStateTrigger(trigger_id, config))
        elif special_type == "state_timing":
            return cast(ITrigger, WorkflowStateTimingTrigger(trigger_id, config))
        elif special_type == "state_pattern":
            return cast(ITrigger, StatePatternTrigger(trigger_id, config))
        
        # 默认状态触发器
        condition = config.get("condition", "True")
        return cast(ITrigger, StateTrigger(
            trigger_id=trigger_id,
            condition=condition,
            config=config
        ))
    
    def _create_event_trigger(self, trigger_id: str, config: Dict[str, Any]) -> ITrigger:
        """创建事件触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
            
        Returns:
            ITrigger: 事件触发器实例
        """
        # 检查是否是特殊的事件触发器
        special_type = config.get("special_type")
        
        if special_type == "user_input_pattern":
            return cast(ITrigger, UserInputPatternTrigger(trigger_id, config))
        elif special_type == "llm_output_pattern":
            return cast(ITrigger, LLMOutputPatternTrigger(trigger_id, config))
        elif special_type == "tool_output_pattern":
            return cast(ITrigger, ToolOutputPatternTrigger(trigger_id, config))
        
        # 默认事件触发器
        event_type = config.get("event_type", "")
        event_pattern = config.get("event_pattern")
        
        return cast(ITrigger, EventTrigger(
            trigger_id=trigger_id,
            event_type=event_type,
            event_pattern=event_pattern,
            config=config
        ))
    
    def _create_custom_trigger(
        self,
        trigger_id: str,
        config: Dict[str, Any],
        evaluate_function: Optional[str] = None,
        execute_function: Optional[str] = None
    ) -> ITrigger:
        """创建自定义触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
            evaluate_function: 评估函数名称
            execute_function: 执行函数名称
            
        Returns:
            ITrigger: 自定义触发器实例
        """
        # 检查是否使用预定义的特殊触发器
        special_type = config.get("special_type")
        
        if special_type == "tool_error":
            error_threshold = config.get("error_threshold", 1)
            return cast(ITrigger, ToolErrorTrigger(
                trigger_id=trigger_id,
                error_threshold=error_threshold,
                config=config
            ))
        elif special_type == "iteration_limit":
            max_iterations = config.get("max_iterations", 10)
            return cast(ITrigger, IterationLimitTrigger(
                trigger_id=trigger_id,
                max_iterations=max_iterations,
                config=config
            ))
        elif special_type == "tool_timing":
            return cast(ITrigger, ToolExecutionTimingTrigger(trigger_id, config))
        elif special_type == "llm_timing":
            return cast(ITrigger, LLMResponseTimingTrigger(trigger_id, config))
        
        # 使用函数管理器创建自定义触发器
        if evaluate_function and execute_function:
            eval_func = self.function_manager.get_evaluate_function(evaluate_function)
            exec_func = self.function_manager.get_execute_function(execute_function)
            
            if not eval_func:
                raise ValueError(f"评估函数不存在: {evaluate_function}")
            
            if not exec_func:
                raise ValueError(f"执行函数不存在: {execute_function}")
            
            return cast(ITrigger, CustomTrigger(
                trigger_id=trigger_id,
                evaluate_func=eval_func,
                execute_func=exec_func,
                config=config
            ))
        
        # 如果没有指定函数，尝试从配置中获取
        evaluate_func_name = config.get("evaluate_function")
        execute_func_name = config.get("execute_function")
        
        if evaluate_func_name and execute_func_name:
            eval_func = self.function_manager.get_evaluate_function(evaluate_func_name)
            exec_func = self.function_manager.get_execute_function(execute_func_name)
            
            if not eval_func:
                raise ValueError(f"评估函数不存在: {evaluate_func_name}")
            
            if not exec_func:
                raise ValueError(f"执行函数不存在: {execute_func_name}")
            
            return cast(ITrigger, CustomTrigger(
                trigger_id=trigger_id,
                evaluate_func=eval_func,
                execute_func=exec_func,
                config=config
            ))
        
        raise ValueError("自定义触发器必须指定评估函数和执行函数")
    
    def create_batch_triggers(self, trigger_configs: List[Dict[str, Any]]) -> List[ITrigger]:
        """批量创建触发器
        
        Args:
            trigger_configs: 触发器配置列表
            
        Returns:
            List[ITrigger]: 触发器列表
            
        Raises:
            ValueError: 创建失败时抛出异常
        """
        triggers = []
        errors = []
        
        for i, config in enumerate(trigger_configs):
            try:
                trigger = self._create_trigger_from_config(config)
                triggers.append(trigger)
            except Exception as e:
                errors.append(f"触发器 {i}: {e}")
        
        if errors:
            raise ValueError(f"批量创建触发器失败:\n" + "\n".join(errors))
        
        return triggers
    
    def _create_trigger_from_config(self, config: Dict[str, Any]) -> ITrigger:
        """从配置创建触发器
        
        Args:
            config: 触发器配置
            
        Returns:
            ITrigger: 触发器实例
        """
        trigger_id = config.get("trigger_id")
        if not trigger_id:
            raise ValueError("触发器配置必须包含trigger_id")
        
        # 检查是否是监控触发器
        trigger_class = config.get("trigger_class")
        if trigger_class:
            return self.create_monitoring_trigger(trigger_id, trigger_class, config.get("config", {}))
        
        trigger_type_str = config.get("trigger_type", "custom")
        trigger_type = TriggerType(trigger_type_str)
        
        trigger_config = config.get("config", {})
        evaluate_function = config.get("evaluate_function")
        execute_function = config.get("execute_function")
        
        return self.create_trigger(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            config=trigger_config,
            evaluate_function=evaluate_function,
            execute_function=execute_function
        )
    
    def list_available_compositions(self) -> List[str]:
        """列出可用的触发器组合
        
        Returns:
            List[str]: 组合名称列表
        """
        return self.function_manager.list_compositions()
    
    def list_available_monitoring_triggers(self) -> List[str]:
        """列出可用的监控触发器
        
        Returns:
            List[str]: 监控触发器类名列表
        """
        return [
            # 计时触发器
            "ToolExecutionTimingTrigger",
            "LLMResponseTimingTrigger",
            "WorkflowStateTimingTrigger",
            # 状态监控触发器
            "WorkflowStateCaptureTrigger",
            "WorkflowStateChangeTrigger",
            "WorkflowErrorStateTrigger",
            # 模式匹配触发器
            "UserInputPatternTrigger",
            "LLMOutputPatternTrigger",
            "ToolOutputPatternTrigger",
            "StatePatternTrigger",
            # 系统监控触发器
            "MemoryMonitoringTrigger",
            "PerformanceMonitoringTrigger",
            "ResourceMonitoringTrigger"
        ]
    
    def get_composition_info(self, composition_name: str) -> Optional[Dict[str, Any]]:
        """获取触发器组合信息
        
        Args:
            composition_name: 组合名称
            
        Returns:
            Optional[Dict[str, Any]]: 组合信息，如果不存在返回None
        """
        composition = self.function_manager.get_composition(composition_name)
        if not composition:
            return None
        
        return {
            "name": composition.name,
            "description": composition.description,
            "trigger_type": composition.trigger_type,
            "evaluate_function": {
                "name": composition.evaluate_function.name,
                "description": composition.evaluate_function.description,
                "function_type": composition.evaluate_function.function_type
            },
            "execute_function": {
                "name": composition.execute_function.name,
                "description": composition.execute_function.description,
                "function_type": composition.execute_function.function_type
            },
            "default_config": composition.default_config,
            "metadata": composition.metadata
        }
    
    def validate_trigger_config(self, config: Dict[str, Any]) -> List[str]:
        """验证触发器配置
        
        Args:
            config: 触发器配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查必需字段
        if not config.get("trigger_id"):
            errors.append("缺少必需字段: trigger_id")
        
        # 检查监控触发器配置
        trigger_class = config.get("trigger_class")
        if trigger_class:
            if trigger_class not in self.list_available_monitoring_triggers():
                errors.append(f"不支持的监控触发器类: {trigger_class}")
            return errors
        
        # 检查传统触发器配置
        trigger_type_str = config.get("trigger_type")
        if not trigger_type_str:
            errors.append("缺少必需字段: trigger_type")
        else:
            try:
                TriggerType(trigger_type_str)
            except ValueError:
                errors.append(f"无效的触发器类型: {trigger_type_str}")
        
        # 验证自定义触发器的函数配置
        if trigger_type_str == "custom":
            evaluate_function = config.get("evaluate_function")
            execute_function = config.get("execute_function")
            
            if not evaluate_function:
                errors.append("自定义触发器必须指定evaluate_function")
            elif not self.function_manager.get_function(evaluate_function):
                errors.append(f"评估函数不存在: {evaluate_function}")
            
            if not execute_function:
                errors.append("自定义触发器必须指定execute_function")
            elif not self.function_manager.get_function(execute_function):
                errors.append(f"执行函数不存在: {execute_function}")
        
        return errors


# 全局触发器工厂实例
_global_factory: Optional[TriggerFactory] = None


def get_trigger_factory() -> TriggerFactory:
    """获取全局触发器工厂实例
    
    Returns:
        TriggerFactory: 触发器工厂实例
    """
    global _global_factory
    
    if _global_factory is None:
        _global_factory = TriggerFactory()
    
    return _global_factory


def reset_trigger_factory() -> None:
    """重置全局触发器工厂实例（用于测试）"""
    global _global_factory
    _global_factory = None