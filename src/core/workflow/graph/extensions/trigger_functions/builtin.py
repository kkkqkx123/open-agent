"""内置触发器函数

提供系统内置的常用触发器函数。
"""

from typing import Dict, Any, Callable, TYPE_CHECKING

from src.interfaces.state.workflow import IWorkflowState as WorkflowState

# 从实现模块导入具体实现
from .impl.time_impl import TimeTriggerImplementation
from .impl.state_impl import StateTriggerImplementation
from .impl.event_impl import EventTriggerImplementation
from .impl.tool_error_impl import ToolErrorTriggerImplementation
from .impl.iteration_impl import IterationLimitTriggerImplementation


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
        return TimeTriggerImplementation.evaluate(state, context)
    
    @staticmethod
    def state_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """状态触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        return StateTriggerImplementation.evaluate(state, context)
    
    @staticmethod
    def event_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """事件触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        return EventTriggerImplementation.evaluate(state, context)
    
    @staticmethod
    def tool_error_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """工具错误触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        return ToolErrorTriggerImplementation.evaluate(state, context)
    
    @staticmethod
    def iteration_limit_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
        """迭代限制触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        return IterationLimitTriggerImplementation.evaluate(state, context)
    
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
        return TimeTriggerImplementation.execute(state, context)
    
    @staticmethod
    def state_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """状态触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        return StateTriggerImplementation.execute(state, context)
    
    @staticmethod
    def event_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """事件触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        return EventTriggerImplementation.execute(state, context)
    
    @staticmethod
    def tool_error_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """工具错误触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        return ToolErrorTriggerImplementation.execute(state, context)
    
    @staticmethod
    def iteration_limit_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """迭代限制触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        return IterationLimitTriggerImplementation.execute(state, context)
    
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