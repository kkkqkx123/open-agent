"""工作流注册表 - 统一注册和查找功能

集中所有工作流注册和查找功能，避免注册逻辑分散。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.core import IWorkflow, IWorkflowRegistry
from src.core.workflow.workflow import Workflow

logger = get_logger(__name__)


class WorkflowRegistry(IWorkflowRegistry):
    """工作流注册表实现
    
    集中所有注册和查找功能，提供统一的工作流管理。
    """
    
    def __init__(self):
        """初始化工作流注册表"""
        self._workflows: Dict[str, IWorkflow] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        logger.debug("工作流注册表初始化完成")
    
    def register_workflow(self, workflow_id: str, workflow: IWorkflow) -> None:
        """注册工作流
        
        Args:
            workflow_id: 工作流ID
            workflow: 工作流实例
            
        Raises:
            ValueError: 工作流ID已存在
        """
        if workflow_id in self._workflows:
            raise ValueError(f"工作流ID已存在: {workflow_id}")
        
        if not workflow:
            raise ValueError("工作流实例不能为空")
        
        self._workflows[workflow_id] = workflow
        self._metadata[workflow_id] = {
            "registered_at": datetime.now(),
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version
        }
        
        logger.info(f"注册工作流: {workflow_id} ({workflow.name})")
    
    def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """获取工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[IWorkflow]: 工作流实例，如果不存在则返回None
        """
        return self._workflows.get(workflow_id)
    
    def unregister_workflow(self, workflow_id: str) -> bool:
        """注销工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否成功注销
        """
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            del self._metadata[workflow_id]
            logger.info(f"注销工作流: {workflow_id}")
            return True
        return False
    
    def list_workflows(self) -> List[str]:
        """列出所有已注册的工作流
        
        Returns:
            List[str]: 工作流ID列表
        """
        return list(self._workflows.keys())
    
    def clear(self) -> None:
        """清空注册表"""
        count = len(self._workflows)
        self._workflows.clear()
        self._metadata.clear()
        logger.info(f"清空注册表，移除 {count} 个工作流")
    
    def get_workflow_info(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流信息
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[Dict[str, Any]]: 工作流信息，如果不存在则返回None
        """
        if workflow_id not in self._workflows:
            return None
        
        workflow = self._workflows[workflow_id]
        metadata = self._metadata[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "entry_point": workflow.entry_point,
            "node_count": len(workflow.get_nodes()),
            "edge_count": len(workflow.get_edges()),
            "registered_at": metadata["registered_at"],
            "has_graph": workflow.compiled_graph is not None
        }
    
    def list_workflow_infos(self) -> List[Dict[str, Any]]:
        """列出所有工作流信息
        
        Returns:
            List[Dict[str, Any]]: 工作流信息列表
        """
        return [info for info in (self.get_workflow_info(workflow_id) for workflow_id in self.list_workflows()) if info is not None]
    
    def search_workflows(self, **kwargs) -> List[str]:
        """搜索工作流
        
        Args:
            **kwargs: 搜索条件，支持 name, description, version 等
            
        Returns:
            List[str]: 匹配的工作流ID列表
        """
        results = []
        
        for workflow_id, workflow in self._workflows.items():
            match = True
            
            for key, value in kwargs.items():
                if hasattr(workflow, key):
                    workflow_value = getattr(workflow, key)
                    if isinstance(workflow_value, str) and isinstance(value, str):
                        if value.lower() not in workflow_value.lower():
                            match = False
                            break
                    elif workflow_value != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                results.append(workflow_id)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_workflows = len(self._workflows)
        workflows_with_graph = sum(1 for w in self._workflows.values() if w.compiled_graph is not None)
        
        # 统计版本分布
        version_counts = {}
        for workflow in self._workflows.values():
            version = workflow.version
            version_counts[version] = version_counts.get(version, 0) + 1
        
        return {
            "total_workflows": total_workflows,
            "workflows_with_graph": workflows_with_graph,
            "workflows_without_graph": total_workflows - workflows_with_graph,
            "version_distribution": version_counts,
            "average_nodes_per_workflow": sum(len(w.get_nodes()) for w in self._workflows.values()) / max(total_workflows, 1),
            "average_edges_per_workflow": sum(len(w.get_edges()) for w in self._workflows.values()) / max(total_workflows, 1)
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息（实现IWorkflowRegistry接口）
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.get_statistics()
    
    def validate_workflow_id(self, workflow_id: str) -> bool:
        """验证工作流ID格式
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否有效
        """
        if not workflow_id:
            return False
        
        # 基本格式检查
        if not isinstance(workflow_id, str):
            return False
        
        # 长度检查
        if len(workflow_id) < 1 or len(workflow_id) > 100:
            return False
        
        # 字符检查（只允许字母、数字、下划线、连字符）
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', workflow_id):
            return False
        
        return True
    
    def exists(self, workflow_id: str) -> bool:
        """检查工作流是否存在
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否存在
        """
        return workflow_id in self._workflows
    
    def update_workflow(self, workflow_id: str, workflow: IWorkflow) -> bool:
        """更新工作流
        
        Args:
            workflow_id: 工作流ID
            workflow: 新的工作流实例
            
        Returns:
            bool: 是否成功更新
        """
        if workflow_id not in self._workflows:
            return False
        
        if not workflow:
            return False
        
        self._workflows[workflow_id] = workflow
        
        # 更新元数据
        self._metadata[workflow_id].update({
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "updated_at": datetime.now()
        })
        
        logger.info(f"更新工作流: {workflow_id}")
        return True
    
    def __len__(self) -> int:
        """返回注册的工作流数量"""
        return len(self._workflows)
    
    def __contains__(self, workflow_id: str) -> bool:
        """检查工作流ID是否在注册表中"""
        return workflow_id in self._workflows
    
    def __iter__(self):
        """迭代所有工作流ID"""
        return iter(self._workflows)
    
    def items(self):
        """返回所有工作流ID和工作流实例的键值对"""
        return self._workflows.items()
    
    def values(self):
        """返回所有工作流实例"""
        return self._workflows.values()
    
    def keys(self):
        """返回所有工作流ID"""
        return self._workflows.keys()


# 注意：全局注册表模式已弃用，请使用依赖注入容器
# 以下函数仅为向后兼容保留，建议迁移到依赖注入模式

_global_registry: Optional[WorkflowRegistry] = None


def get_global_registry() -> WorkflowRegistry:
    """获取全局工作流注册表
    
    .. deprecated::
        请使用依赖注入容器获取工作流注册表
    
    Returns:
        WorkflowRegistry: 全局注册表实例
    """
    import warnings
    warnings.warn(
        "get_global_registry() 已弃用，请使用依赖注入容器获取工作流注册表",
        DeprecationWarning,
        stacklevel=2
    )
    
    global _global_registry
    if _global_registry is None:
        _global_registry = WorkflowRegistry()
    return _global_registry


def register_workflow(workflow_id: str, workflow: IWorkflow) -> None:
    """便捷函数：注册工作流到全局注册表
    
    .. deprecated::
        请使用依赖注入容器注册工作流
    
    Args:
        workflow_id: 工作流ID
        workflow: 工作流实例
    """
    import warnings
    warnings.warn(
        "register_workflow() 已弃用，请使用依赖注入容器注册工作流",
        DeprecationWarning,
        stacklevel=2
    )
    
    registry = get_global_registry()
    registry.register_workflow(workflow_id, workflow)


def get_workflow(workflow_id: str) -> Optional[IWorkflow]:
    """便捷函数：从全局注册表获取工作流
    
    .. deprecated::
        请使用依赖注入容器获取工作流
    
    Args:
        workflow_id: 工作流ID
        
    Returns:
        Optional[IWorkflow]: 工作流实例
    """
    import warnings
    warnings.warn(
        "get_workflow() 已弃用，请使用依赖注入容器获取工作流",
        DeprecationWarning,
        stacklevel=2
    )
    
    registry = get_global_registry()
    return registry.get_workflow(workflow_id)


def list_workflows() -> List[str]:
    """便捷函数：列出全局注册表中的所有工作流
    
    .. deprecated::
        请使用依赖注入容器列出工作流
    
    Returns:
        List[str]: 工作流ID列表
    """
    import warnings
    warnings.warn(
        "list_workflows() 已弃用，请使用依赖注入容器列出工作流",
        DeprecationWarning,
        stacklevel=2
    )
    
    registry = get_global_registry()
    return registry.list_workflows()