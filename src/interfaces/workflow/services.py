"""
工作流服务接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IWorkflowService(ABC):
    """工作流服务接口"""
    
    @abstractmethod
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        pass
    
    @abstractmethod
    def get_workflow_status(self, workflow_id: str) -> str:
        """获取工作流状态"""
        pass
    
    @abstractmethod
    def list_workflows(self) -> list:
        """列出所有工作流"""
        pass

__all__ = ["IWorkflowService"]