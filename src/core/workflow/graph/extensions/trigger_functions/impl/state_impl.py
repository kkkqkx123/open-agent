"""状态触发器实现

提供状态触发器的具体实现逻辑。
"""

from typing import Dict, Any

from src.interfaces.state.workflow import IWorkflowState


class StateTriggerImplementation:
    """状态触发器实现类
    
    提供状态触发器的评估和执行逻辑，支持基于状态条件的触发。
    """
    
    @staticmethod
    def evaluate(state: IWorkflowState, context: Dict[str, Any]) -> bool:
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
    def execute(state: IWorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """状态触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        from datetime import datetime
        
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