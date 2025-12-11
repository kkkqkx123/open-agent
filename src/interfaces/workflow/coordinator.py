"""工作流协调器接口

定义工作流内部协调器的接口，负责 workflow 层内部的组件协调。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state.workflow import IWorkflowState
from src.core.workflow.graph_entities import GraphConfig


class IWorkflowCoordinator(ABC):
    """工作流协调器接口"""
    
    @abstractmethod
    def create_workflow(self, config: GraphConfig) -> IWorkflow:
        """创建工作流实例
        
        Args:
            config: 工作流配置
            
        Returns:
            IWorkflow: 工作流实例
        """
        pass
    
    @abstractmethod
    def execute_workflow(self, workflow: IWorkflow, initial_state: IWorkflowState) -> IWorkflowState:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            
        Returns:
            IWorkflowState: 执行后的状态
        """
        pass
    
    @abstractmethod
    def validate_workflow_config(self, config: GraphConfig) -> List[str]:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def get_workflow_stats(self, workflow: IWorkflow) -> Dict[str, Any]:
        """获取工作流统计信息
        
        Args:
            workflow: 工作流实例
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass


# 导出接口
__all__ = [
    "IWorkflowCoordinator",
]