"""Core层触发器函数实现

提供符合ITriggerFunction接口的触发器函数实现，直接在Core层实现业务逻辑。
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.interfaces.workflow.functions import ITriggerFunction, FunctionType, FunctionMetadata
from src.interfaces.state.workflow import IWorkflowState


class TimeTriggerFunction(ITriggerFunction):
    """时间触发器函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:time",
            name="time_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于时间条件的触发器，支持间隔时间和特定时间点两种模式",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "触发器配置，包含trigger_config等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化时间触发器"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理时间触发器资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证触发器配置"""
        errors = []
        trigger_config = config.get("trigger_config", {})
        
        if not trigger_config.get("trigger_time"):
            errors.append("trigger_time是必需的")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发
        
        Args:
            state: 工作流状态
            config: 触发器配置
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = config.get("trigger_config", {})
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


class StateTriggerFunction(ITriggerFunction):
    """状态触发器函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:state",
            name="state_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于状态条件的触发器，支持自定义条件表达式",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "触发器配置，包含condition等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化状态触发器"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理状态触发器资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证触发器配置"""
        errors = []
        trigger_config = config.get("trigger_config", {})
        
        if not trigger_config.get("condition"):
            errors.append("condition是必需的")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发
        
        Args:
            state: 工作流状态
            config: 触发器配置
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = config.get("trigger_config", {})
        condition = trigger_config.get("condition")
        
        if not condition:
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
                "config": config,
            }
            
            # 执行条件表达式
            result = eval(condition, safe_globals)
            return bool(result)
            
        except Exception:
            return False


class EventTriggerFunction(ITriggerFunction):
    """事件触发器函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:event",
            name="event_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于事件类型的触发器，支持事件模式匹配",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "触发器配置，包含event_type等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化事件触发器"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理事件触发器资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证触发器配置"""
        errors = []
        trigger_config = config.get("trigger_config", {})
        
        if not trigger_config.get("event_type"):
            errors.append("event_type是必需的")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发
        
        Args:
            state: 工作流状态
            config: 触发器配置
            
        Returns:
            bool: 是否应该触发
        """
        import re
        
        trigger_config = config.get("trigger_config", {})
        event_type = trigger_config.get("event_type")
        event_pattern = trigger_config.get("event_pattern")
        
        if not event_type:
            return False
        
        # 检查上下文中是否有匹配的事件
        events = config.get("events", [])
        
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


class ToolErrorTriggerFunction(ITriggerFunction):
    """工具错误触发器函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:tool_error",
            name="tool_error_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于工具错误数量的触发器",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "触发器配置，包含error_threshold等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化工具错误触发器"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理工具错误触发器资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证触发器配置"""
        errors = []
        trigger_config = config.get("trigger_config", {})
        
        error_threshold = trigger_config.get("error_threshold")
        if error_threshold is None or not isinstance(error_threshold, int) or error_threshold < 1:
            errors.append("error_threshold必须是大于0的整数")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发
        
        Args:
            state: 工作流状态
            config: 触发器配置
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = config.get("trigger_config", {})
        error_threshold = trigger_config.get("error_threshold", 1)
        
        # 计算工具错误数量
        tool_results = state.get("tool_results", [])
        error_count = sum(1 for result in tool_results if not result.get("success", True))
        return error_count >= error_threshold


class IterationLimitTriggerFunction(ITriggerFunction):
    """迭代限制触发器函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:iteration_limit",
            name="iteration_limit_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于迭代次数限制的触发器",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "config": {
                "type": "Dict[str, Any]",
                "required": True,
                "description": "触发器配置，包含max_iterations等",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化迭代限制触发器"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理迭代限制触发器资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证触发器配置"""
        errors = []
        trigger_config = config.get("trigger_config", {})
        
        max_iterations = trigger_config.get("max_iterations")
        if max_iterations is None or not isinstance(max_iterations, int) or max_iterations < 1:
            errors.append("max_iterations必须是大于0的整数")
        
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        if "config" not in params:
            errors.append("config参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发
        
        Args:
            state: 工作流状态
            config: 触发器配置
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = config.get("trigger_config", {})
        max_iterations = trigger_config.get("max_iterations", 10)
        
        iteration_count = state.get("iteration_count", 0)
        return iteration_count >= max_iterations


class BuiltinTriggerFunctions:
    """内置触发器函数集合"""
    
    @staticmethod
    def get_all_functions():
        """获取所有内置触发器函数"""
        return [
            TimeTriggerFunction(),
            StateTriggerFunction(),
            EventTriggerFunction(),
            ToolErrorTriggerFunction(),
            IterationLimitTriggerFunction(),
        ]
    
    @staticmethod
    def get_function_by_name(name: str):
        """根据名称获取触发器函数"""
        functions = {
            "time": TimeTriggerFunction,
            "state": StateTriggerFunction,
            "event": EventTriggerFunction,
            "tool_error": ToolErrorTriggerFunction,
            "iteration_limit": IterationLimitTriggerFunction,
        }
        
        function_class = functions.get(name)
        return function_class() if function_class else None