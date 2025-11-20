"""工作流状态管理器实现

专门处理WorkflowState类型的状态管理。
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime

from src.interfaces.state.interfaces import IState
from src.interfaces.state import (
    IStateHistoryManager,
    IStateSnapshotManager,
    IStateSerializer
)
from .manager import EnhancedStateManager


logger = logging.getLogger(__name__)


class WorkflowStateManager(EnhancedStateManager):
    """工作流状态管理器，专门处理WorkflowState类型的状态"""
    
    def __init__(self, 
                 history_manager: IStateHistoryManager,
                 snapshot_manager: IStateSnapshotManager,
                 serializer: Optional[IStateSerializer] = None):
        super().__init__(history_manager, snapshot_manager, serializer)
    
    def create_workflow_state(self, state_id: str, initial_state: Dict[str, Any], 
                             agent_id: str) -> IState:
        """创建工作流状态，确保包含必要的字段"""
        # 验证和补充必要的工作流字段
        workflow_state = self._ensure_workflow_fields(initial_state)
        return self.create_state_with_history(state_id, workflow_state, agent_id)
    
    def _ensure_workflow_fields(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """确保状态包含工作流必需的字段"""
        default_workflow_state = {
            "messages": [],
            "tool_results": [],
            "current_step": "",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "",
            "start_time": None,
            "errors": [],
            "input": "",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 合并默认值和实际值
        result = default_workflow_state.copy()
        result.update(state)
        
        # 确保时间字段是正确格式
        if result["start_time"] is None:
            result["start_time"] = datetime.now().isoformat()
        
        return result
    
    def validate_workflow_state(self, state: Dict[str, Any]) -> List[str]:
        """验证工作流状态的完整性"""
        errors = []
        
        # 检查必需字段
        required_fields = ["messages", "tool_results", "current_step", "max_iterations", "iteration_count"]
        for field in required_fields:
            if field not in state:
                errors.append(f"工作流状态中缺少必要字段: {field}")
        
        # 检查字段类型
        if not isinstance(state.get("messages", []), list):
            errors.append("messages字段必须是列表类型")
        
        if not isinstance(state.get("tool_results", []), list):
            errors.append("tool_results字段必须是列表类型")
        
        if not isinstance(state.get("max_iterations", 0), int):
            errors.append("max_iterations必须是整数类型")
        
        if not isinstance(state.get("iteration_count", 0), int):
            errors.append("iteration_count必须是整数类型")
        
        # 检查业务逻辑约束
        if state.get("iteration_count", 0) > state.get("max_iterations", 10):
            errors.append("iteration_count不能超过max_iterations")
        
        return errors