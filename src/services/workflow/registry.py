"""工作流注册表

管理工作流的注册和查找。
"""

from typing import Dict, Any, List, Optional
import logging

from ..core.workflow.interfaces import IWorkflow, IWorkflowBuilder
from ..core.workflow.entities import Workflow


logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """工作流注册表
    
    管理工作流的注册、查找和版本控制。
    """
    
    def __init__(self):
        """初始化注册表"""
        self._workflows: Dict[str, IWorkflow] = {}
        self._workflow_builders: Dict[str, IWorkflowBuilder] = {}
        self._workflow_versions: Dict[str, str] = {}

    def register_workflow(self, workflow_id: str, workflow: IWorkflow) -> None:
        """注册工作流
        
        Args:
            workflow_id: 工作流ID
            workflow: 工作流实例
        """
        if workflow_id in self._workflows:
            raise ValueError(f"工作流ID已存在: {workflow_id}")
        
        self._workflows[workflow_id] = workflow
        self._workflow_versions[workflow_id] = workflow.version
        logger.info(f"注册工作流: {workflow_id} (版本: {workflow.version})")

    def register_workflow_builder(self, builder_id: str, builder: IWorkflowBuilder) -> None:
        """注册工作流构建器
        
        Args:
            builder_id: 构建器ID
            builder: 构建器实例
        """
        if builder_id in self._workflow_builders:
            raise ValueError(f"构建器ID已存在: {builder_id}")
        
        self._workflow_builders[builder_id] = builder
        logger.info(f"注册工作流构建器: {builder_id}")

    def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """获取工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[IWorkflow]: 工作流实例，如果不存在则返回None
        """
        return self._workflows.get(workflow_id)

    def get_workflow_builder(self, builder_id: str) -> Optional[IWorkflowBuilder]:
        """获取工作流构建器
        
        Args:
            builder_id: 构建器ID
            
        Returns:
            Optional[IWorkflowBuilder]: 构建器实例，如果不存在则返回None
        """
        return self._workflow_builders.get(builder_id)

    def list_workflows(self) -> List[str]:
        """列出所有注册的工作流
        
        Returns:
            List[str]: 工作流ID列表
        """
        return list(self._workflows.keys())

    def list_workflow_builders(self) -> List[str]:
        """列出所有注册的工作流构建器
        
        Returns:
            List[str]: 构建器ID列表
        """
        return list(self._workflow_builders.keys())

    def get_workflow_version(self, workflow_id: str) -> Optional[str]:
        """获取工作流版本
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[str]: 工作流版本，如果不存在则返回None
        """
        return self._workflow_versions.get(workflow_id)

    def validate_workflow(self, workflow_id: str) -> List[str]:
        """验证工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return [f"工作流不存在: {workflow_id}"]
        
        return workflow.validate()

    def unregister_workflow(self, workflow_id: str) -> bool:
        """注销工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否成功注销
        """
        if workflow_id not in self._workflows:
            return False
        
        del self._workflows[workflow_id]
        if workflow_id in self._workflow_versions:
            del self._workflow_versions[workflow_id]
        
        logger.info(f"注销工作流: {workflow_id}")
        return True

    def unregister_workflow_builder(self, builder_id: str) -> bool:
        """注销工作流构建器
        
        Args:
            builder_id: 构建器ID
            
        Returns:
            bool: 是否成功注销
        """
        if builder_id not in self._workflow_builders:
            return False
        
        del self._workflow_builders[builder_id]
        logger.info(f"注销工作流构建器: {builder_id}")
        return True

    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "registered_workflows": len(self._workflows),
            "registered_builders": len(self._workflow_builders),
            "workflow_ids": list(self._workflows.keys()),
            "builder_ids": list(self._workflow_builders.keys()),
            "workflow_versions": dict(self._workflow_versions)
        }

    def clear(self) -> None:
        """清除所有注册"""
        self._workflows.clear()
        self._workflow_builders.clear()
        self._workflow_versions.clear()
        logger.info("清除所有工作流注册")


# 全局注册表实例
_global_registry: Optional[WorkflowRegistry] = None


def get_global_registry() -> WorkflowRegistry:
    """获取全局注册表
    
    Returns:
        WorkflowRegistry: 全局注册表
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = WorkflowRegistry()
    return _global_registry


def register_workflow(workflow_id: str, workflow: IWorkflow) -> None:
    """注册工作流到全局注册表
    
    Args:
        workflow_id: 工作流ID
        workflow: 工作流实例
    """
    get_global_registry().register_workflow(workflow_id, workflow)


def register_workflow_builder(builder_id: str, builder: IWorkflowBuilder) -> None:
    """注册工作流构建器到全局注册表
    
    Args:
        builder_id: 构建器ID
        builder: 构建器实例
    """
    get_global_registry().register_workflow_builder(builder_id, builder)


def get_workflow(workflow_id: str) -> Optional[IWorkflow]:
    """从全局注册表获取工作流
    
    Args:
        workflow_id: 工作流ID
            
    Returns:
        Optional[IWorkflow]: 工作流实例，如果不存在则返回None
    """
    return get_global_registry().get_workflow(workflow_id)


def get_workflow_builder(builder_id: str) -> Optional[IWorkflowBuilder]:
    """从全局注册表获取工作流构建器
    
    Args:
        builder_id: 构建器ID
            
        Returns:
        Optional[IWorkflowBuilder]: 构建器实例，如果不存在则返回None
    """
    return get_global_registry().get_workflow_builder(builder_id)