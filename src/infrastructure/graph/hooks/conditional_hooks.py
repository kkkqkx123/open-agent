"""条件Hook实现

支持基于上下文条件的Hook执行。
"""

from typing import Any, Dict, Optional

from src.interfaces.workflow.hooks import HookPoint, HookContext, HookExecutionResult, IHook

__all__ = ("ConditionalHook",)


class ConditionalHook:
    """条件Hook，基于上下文条件决定是否执行。"""
    
    def __init__(
        self,
        condition: str,
        hook_point: HookPoint,
        hook_plugin: IHook,
        priority: int = 50
    ):
        """
        初始化条件Hook。
        
        Args:
            condition: 条件表达式
            hook_point: Hook点
            hook_plugin: Hook实例
            priority: 优先级
        """
        self.condition = condition
        self.hook_point = hook_point
        self.hook_plugin = hook_plugin
        self.priority = priority
    
    def should_execute(self, context: HookContext) -> bool:
        """基于上下文评估条件。
        
        Args:
            context: Hook执行上下文
            
        Returns:
            是否应该执行Hook
        """
        try:
            # 简单的条件评估实现
            # 支持的变量：node_type, state中的键, config中的键
            variables = {
                "node_type": context.node_type,
            }
            
            # 添加状态变量
            if context.state is not None and hasattr(context.state, 'to_dict'):
                variables.update(context.state.to_dict())
            
            # 添加配置变量
            if context.config:
                variables.update(context.config)
            
            # 添加元数据变量
            if context.metadata:
                variables.update(context.metadata)
            
            # 评估条件
            return self._evaluate_condition(self.condition, variables)
        except Exception:
            # 如果条件评估失败，默认不执行
            return False
    
    def _evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """评估条件表达式。
        
        Args:
            condition: 条件表达式
            variables: 变量字典
            
        Returns:
            评估结果
        """
        # 简单的条件评估实现
        # 支持基本的比较和逻辑操作
        
        # 替换变量
        for key, value in variables.items():
            if value is None:
                condition = condition.replace(f"${key}", "None")
            elif isinstance(value, str):
                condition = condition.replace(f"${key}", f"'{value}'")
            else:
                condition = condition.replace(f"${key}", str(value))
        
        # 安全评估
        try:
            # 只允许特定的操作和函数
            allowed_names = {
                "__builtins__": {},
                "True": True,
                "False": False,
                "None": None,
                "and": lambda x, y: x and y,
                "or": lambda x, y: x or y,
                "not": lambda x: not x,
                "eq": lambda x, y: x == y,
                "ne": lambda x, y: x != y,
                "lt": lambda x, y: x < y,
                "le": lambda x, y: x <= y,
                "gt": lambda x, y: x > y,
                "ge": lambda x, y: x >= y,
                "in": lambda x, y: x in y,
                "contains": lambda x, y: y in x,
                "startswith": lambda x, y: str(x).startswith(str(y)),
                "endswith": lambda x, y: str(x).endswith(str(y)),
                "isinstance": isinstance,
                "type": type,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "len": len,
            }
            
            # 替换常见的操作符
            condition = condition.replace("==", " eq ")
            condition = condition.replace("!=", " ne ")
            condition = condition.replace("<", " lt ")
            condition = condition.replace("<=", " le ")
            condition = condition.replace(">", " gt ")
            condition = condition.replace(">=", " ge ")
            condition = condition.replace(" in ", " in ")
            
            return eval(condition, allowed_names, {})
        except Exception:
            return False
    
    async def execute(self, context: HookContext) -> HookExecutionResult:
        """执行Hook。
        
        Args:
            context: Hook执行上下文
            
        Returns:
            Hook执行结果
        """
        # 根据Hook点调用相应方法
        if self.hook_point == HookPoint.BEFORE_EXECUTE:
            return self.hook_plugin.before_execute(context)
        elif self.hook_point == HookPoint.AFTER_EXECUTE:
            return self.hook_plugin.after_execute(context)
        elif self.hook_point == HookPoint.ON_ERROR:
            return self.hook_plugin.on_error(context)
        elif self.hook_point == HookPoint.BEFORE_COMPILE:
            return self.hook_plugin.before_compile(context)
        elif self.hook_point == HookPoint.AFTER_COMPILE:
            return self.hook_plugin.after_compile(context)
        else:
            return HookExecutionResult(should_continue=True)