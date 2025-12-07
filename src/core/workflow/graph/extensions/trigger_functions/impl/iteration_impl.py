"""迭代限制触发器实现

提供迭代限制触发器的具体实现逻辑。
"""

from typing import Dict, Any

from src.interfaces.state.workflow import IWorkflowState


class IterationLimitTriggerImplementation:
    """迭代限制触发器实现类
    
    提供迭代限制触发器的评估和执行逻辑，支持基于迭代次数的触发。
    """
    
    @staticmethod
    def evaluate(state: IWorkflowState, context: Dict[str, Any]) -> bool:
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
    
    @staticmethod
    def execute(state: IWorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """迭代限制触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        from datetime import datetime
        
        trigger_config = context.get("trigger_config", {})
        max_iterations = trigger_config.get("max_iterations", 10)
        
        iteration_count = state.get("iteration_count", 0)
        
        return {
            "max_iterations": max_iterations,
            "current_iterations": iteration_count,
            "executed_at": datetime.now().isoformat(),
            "message": f"迭代限制触发器执行，当前迭代: {iteration_count}/{max_iterations}"
        }
    
    @staticmethod
    def get_iteration_count(state: IWorkflowState) -> int:
        """获取当前迭代次数
        
        Args:
            state: 工作流状态
            
        Returns:
            int: 迭代次数
        """
        return state.get("iteration_count", 0)
    
    @staticmethod
    def is_iteration_limit_reached(state: IWorkflowState, max_iterations: int) -> bool:
        """检查是否达到迭代限制
        
        Args:
            state: 工作流状态
            max_iterations: 最大迭代次数
            
        Returns:
            bool: 是否达到限制
        """
        iteration_count = state.get("iteration_count", 0)
        return iteration_count >= max_iterations