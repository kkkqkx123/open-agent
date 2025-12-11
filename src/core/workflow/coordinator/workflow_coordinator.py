"""工作流协调器实现

负责 workflow 层内部的组件协调，不承担全局协调职责。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional, cast

from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.core.workflow.core.builder import IWorkflowBuilder
from src.interfaces.workflow.core import IWorkflowValidator
from src.interfaces.state.workflow import IWorkflowState
from src.core.workflow.graph_entities import GraphConfig
from src.core.workflow.workflow import Workflow
from src.core.workflow.management.lifecycle import WorkflowLifecycleManager

logger = get_logger(__name__)


class WorkflowCoordinator(IWorkflowCoordinator):
    """工作流协调器 - 仅负责 workflow 层内部协调"""
    
    def __init__(self,
                 builder: IWorkflowBuilder,
                 executor: IWorkflowExecutor,
                 validator: IWorkflowValidator,
                 lifecycle_manager: WorkflowLifecycleManager,
                 graph_service: Optional[Any] = None):
        """通过构造函数注入所有依赖
        
        Args:
            builder: 工作流构建器
            executor: 工作流执行器
            validator: 工作流验证器
            lifecycle_manager: 生命周期管理器
            graph_service: 图服务（可选）
        """
        self._builder = builder
        self._executor = executor
        self._validator = validator
        self._lifecycle_manager = lifecycle_manager
        self._graph_service = graph_service
        self._logger = get_logger(f"{__name__}.WorkflowCoordinator")
    
    def create_workflow(self, config: GraphConfig) -> IWorkflow:
        """创建工作流实例
        
        Args:
            config: 工作流配置
            
        Returns:
            IWorkflow: 工作流实例
        """
        try:
            # 验证配置
            validation_errors = self.validate_workflow_config(config)
            if validation_errors:
                raise ValueError(f"工作流配置验证失败: {', '.join(validation_errors)}")
            
            # 创建工作流数据模型
            workflow = Workflow(config)
            
            # 构建图
            if self._graph_service:
                # 使用图服务构建
                graph_config = config.to_dict()
                compiled_graph = self._graph_service.build_graph(graph_config)
            else:
                # 使用构建器构建
                compiled_graph = self._builder.build_graph(workflow)
            
            workflow.set_graph(compiled_graph)
            
            self._logger.info(f"成功创建工作流: {config.name}")
            return workflow
            
        except Exception as e:
            self._logger.error(f"创建工作流失败: {config.name}, 错误: {e}")
            raise
    
    def execute_workflow(self, workflow: IWorkflow, initial_state: IWorkflowState) -> IWorkflowState:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            
        Returns:
            IWorkflowState: 执行后的状态
        """
        try:
            # 执行工作流
            result = self._executor.execute(workflow, initial_state, None)
            
            self._logger.info(f"工作流执行完成: {workflow.name}")
            return result
            
        except Exception as e:
            self._logger.error(f"工作流执行失败: {workflow.name}, 错误: {e}")
            raise
    
    def validate_workflow_config(self, config: GraphConfig) -> List[str]:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        try:
            # 使用验证器验证配置
            # 创建临时工作流用于验证
            temp_workflow = Workflow(config)
            validation_result = self._validator.validate(temp_workflow)
            
            if not validation_result.is_valid:
                errors.extend(validation_result.errors)
            
            # 验证构建要求
            if self._builder and hasattr(self._builder, 'validate_build_requirements'):
                # 安全类型转换到 WorkflowBuilder
                from src.core.workflow.core.builder import WorkflowBuilder
                if isinstance(self._builder, WorkflowBuilder):
                    build_errors = self._builder.validate_build_requirements(temp_workflow)
                    errors.extend(build_errors)
            
        except Exception as e:
            self._logger.error(f"配置验证过程中发生错误: {e}")
            errors.append(f"配置验证失败: {str(e)}")
        
        return errors
    
    def get_workflow_stats(self, workflow: IWorkflow) -> Dict[str, Any]:
        """获取工作流统计信息
        
        Args:
            workflow: 工作流实例
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "node_count": len(workflow.get_nodes()),
            "edge_count": len(workflow.get_edges()),
            "entry_point": workflow.entry_point,
            "created_at": None,  # IWorkflow 接口没有 created_at 属性
        }
        
        # 添加图服务统计
        if self._graph_service and hasattr(self._graph_service, 'get_service_stats'):
            stats["graph_service"] = self._graph_service.get_service_stats()
        
        # 添加生命周期管理器统计
        if hasattr(self._lifecycle_manager, 'get_iteration_stats'):
            stats["lifecycle_manager"] = self._lifecycle_manager.get_iteration_stats(None)  # type: ignore
        
        return stats


# 便捷函数
def create_workflow_coordinator(builder: IWorkflowBuilder,
                               executor: IWorkflowExecutor,
                               validator: IWorkflowValidator,
                               lifecycle_manager: WorkflowLifecycleManager,
                               graph_service: Optional[Any] = None) -> WorkflowCoordinator:
    """创建工作流协调器实例
    
    Args:
        builder: 工作流构建器
        executor: 工作流执行器
        validator: 工作流验证器
        lifecycle_manager: 生命周期管理器
        graph_service: 图服务（可选）
        
    Returns:
        WorkflowCoordinator: 工作流协调器实例
    """
    return WorkflowCoordinator(
        builder=builder,
        executor=executor,
        validator=validator,
        lifecycle_manager=lifecycle_manager,
        graph_service=graph_service
    )


# 导出实现
__all__ = [
    "WorkflowCoordinator",
    "create_workflow_coordinator",
]