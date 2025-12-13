"""
工作流服务绑定
"""

from typing import Dict, Any
from src.interfaces.workflow import IWorkflowService
from src.interfaces.container.core import ServiceLifetime

class WorkflowServiceBindings:
    """工作流服务绑定"""
    
    def register_services(self, container, config: Dict[str, Any]):
        """注册工作流服务"""
        # 注册工作流服务
        def workflow_service():
            from src.infrastructure.workflow.workflow_service import WorkflowService
            return WorkflowService(config)
        
        container.register_factory(
            IWorkflowService,
            workflow_service,
            lifetime=ServiceLifetime.SINGLETON
        )