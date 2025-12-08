"""内置触发器函数实现

提供符合IFunction接口的内置触发器函数实现。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re
from src.interfaces.workflow.functions import ITriggerFunction, FunctionType, FunctionMetadata
from src.interfaces.state.workflow import IWorkflowState


class TimeTriggerFunction(ITriggerFunction):
    """时间触发器函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:time",
            name="time_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于时间条件的触发器",
            category="builtin"
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
                "required": False,
                "description": "触发器配置",
                "properties": {
                    "interval_seconds": {
                        "type": "int",
                        "description": "触发间隔秒数"
                    },
                    "last_triggered": {
                        "type": "str",
                        "description": "上次触发时间"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "interval_seconds" in config:
            try:
                interval = int(config["interval_seconds"])
                if interval <= 0:
                    errors.append("interval_seconds 必须大于0")
            except (ValueError, TypeError):
                errors.append("interval_seconds 必须是有效的整数")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发时间触发器"""
        trigger_config = config.get("trigger_config", {})
        interval_seconds = trigger_config.get("interval_seconds", 60)
        last_triggered = trigger_config.get("last_triggered")
        
        if not last_triggered:
            return True
        
        try:
            last_time = datetime.fromisoformat(last_triggered) if isinstance(last_triggered, str) else last_triggered
            return (datetime.now() - last_time).total_seconds() >= interval_seconds
        except (ValueError, TypeError):
            return True


class StateTriggerFunction(ITriggerFunction):
    """状态触发器函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:state",
            name="state_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于状态条件的触发器",
            category="builtin"
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
                "required": False,
                "description": "触发器配置",
                "properties": {
                    "condition": {
                        "type": "str",
                        "description": "状态条件表达式"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "condition" in config and not config["condition"]:
            errors.append("condition 不能为空")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发状态触发器"""
        trigger_config = config.get("trigger_config", {})
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
                "config": config,
            }
            
            # 执行条件表达式
            result = eval(condition, safe_globals)
            return bool(result)
            
        except Exception:
            return False


class EventTriggerFunction(ITriggerFunction):
    """事件触发器函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:event",
            name="event_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于事件条件的触发器",
            category="builtin"
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
                "required": False,
                "description": "触发器配置",
                "properties": {
                    "event_type": {
                        "type": "str",
                        "description": "事件类型"
                    },
                    "event_pattern": {
                        "type": "str",
                        "description": "事件内容匹配模式"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "event_type" in config and not config["event_type"]:
            errors.append("event_type 不能为空")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发事件触发器"""
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
    """工具错误触发器函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:tool_error",
            name="tool_error_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于工具错误条件的触发器",
            category="builtin"
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
                "required": False,
                "description": "触发器配置",
                "properties": {
                    "error_types": {
                        "type": "List[str]",
                        "description": "错误类型列表"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "error_types" in config:
            if not isinstance(config["error_types"], list):
                errors.append("error_types 必须是列表类型")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发工具错误触发器"""
        trigger_config = config.get("trigger_config", {})
        error_types = trigger_config.get("error_types", [])
        
        # 检查工具结果中的错误
        for result in state.get_data("tool_results", []):
            # 处理字典格式的工具结果
            if isinstance(result, dict):
                if not result.get("success", True):
                    error_type = result.get("error_type", "unknown")
                    if not error_types or error_type in error_types:
                        return True
            # 处理ToolResult对象
            elif hasattr(result, 'success'):
                try:
                    if not result.success:
                        error_type = getattr(result, 'error_type', 'unknown')
                        if not error_types or error_type in error_types:
                            return True
                except:
                    # 如果访问属性失败，忽略这个结果
                    pass
        
        return False


class IterationLimitTriggerFunction(ITriggerFunction):
    """迭代限制触发器函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="trigger:iteration_limit",
            name="iteration_limit_trigger",
            function_type=FunctionType.TRIGGER,
            description="基于迭代次数限制的触发器",
            category="builtin"
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
                "required": False,
                "description": "触发器配置",
                "properties": {
                    "max_iterations": {
                        "type": "int",
                        "description": "最大迭代次数"
                    }
                }
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        if "max_iterations" in config:
            try:
                max_iter = int(config["max_iterations"])
                if max_iter <= 0:
                    errors.append("max_iterations 必须大于0")
            except (ValueError, TypeError):
                errors.append("max_iterations 必须是有效的整数")
        return errors
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def should_trigger(self, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """判断是否应该触发迭代限制触发器"""
        trigger_config = config.get("trigger_config", {})
        max_iterations = trigger_config.get("max_iterations", 10)
        
        # 获取当前迭代次数
        iteration_count = state.get_data("workflow_iteration_count") or state.get_data("iteration_count", 0)
        
        return iteration_count >= max_iterations


class BuiltinTriggerFunctions:
    """内置触发器函数集合"""
    
    @staticmethod
    def get_all_functions() -> Dict[str, ITriggerFunction]:
        """获取所有内置触发器函数
        
        Returns:
            Dict[str, ITriggerFunction]: 触发器函数字典
        """
        return {
            "time": TimeTriggerFunction(),
            "state": StateTriggerFunction(),
            "event": EventTriggerFunction(),
            "tool_error": ToolErrorTriggerFunction(),
            "iteration_limit": IterationLimitTriggerFunction(),
        }
    
    @staticmethod
    def get_function(name: str) -> Optional[ITriggerFunction]:
        """获取指定的内置触发器函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[ITriggerFunction]: 触发器函数，如果不存在返回None
        """
        functions = BuiltinTriggerFunctions.get_all_functions()
        return functions.get(name)
    
    @staticmethod
    def list_functions() -> List[str]:
        """列出所有内置触发器函数名称
        
        Returns:
            List[str]: 函数名称列表
        """
        return list(BuiltinTriggerFunctions.get_all_functions().keys())