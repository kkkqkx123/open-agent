"""工具错误触发器实现

提供工具错误触发器的具体实现逻辑。
"""

from typing import Dict, Any

from src.interfaces.state.workflow import IWorkflowState


class ToolErrorTriggerImplementation:
    """工具错误触发器实现类
    
    提供工具错误触发器的评估和执行逻辑，支持基于工具错误数量的触发。
    """
    
    @staticmethod
    def evaluate(state: IWorkflowState, context: Dict[str, Any]) -> bool:
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
    def execute(state: IWorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """工具错误触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        from datetime import datetime
        
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
    def count_tool_errors(state: IWorkflowState) -> int:
        """计算工具错误数量
        
        Args:
            state: 工作流状态
            
        Returns:
            int: 错误数量
        """
        tool_results = state.get("tool_results", [])
        return sum(1 for result in tool_results if not result.get("success", True))
    
    @staticmethod
    def get_error_summary(state: IWorkflowState) -> Dict[str, Dict[str, Any]]:
        """获取错误摘要
        
        Args:
            state: 工作流状态
            
        Returns:
            Dict[str, Dict[str, Any]]: 错误摘要，按工具名称分组
        """
        tool_results = state.get("tool_results", [])
        error_results = [result for result in tool_results if not result.get("success", True)]
        error_summary = {}
        
        for result in error_results:
            tool_name = result.get("tool_name", "unknown")
            if tool_name not in error_summary:
                error_summary[tool_name] = {"count": 0, "errors": []}
            error_summary[tool_name]["count"] += 1
            error_summary[tool_name]["errors"].append(result.get("error", "Unknown error"))
        
        return error_summary