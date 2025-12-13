"""
工作流服务绑定

遵循正确的架构原则，避免在服务注册时创建不必要的对象。
"""

from typing import Dict, Any, Optional
from src.interfaces.workflow.services import IWorkflowService
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.interfaces.workflow.core import IWorkflowValidator
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime
from src.interfaces.logger import ILogger

class WorkflowServiceBindings:
    """工作流服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册工作流服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册工作流构建器 - 使用接口层的接口
        def workflow_builder_factory():
            from src.core.workflow.core.builder import WorkflowBuilder
            return WorkflowBuilder()
        
        # 使用接口层的接口
        from src.interfaces.workflow.builders import IWorkflowBuilder
        container.register_factory(
            IWorkflowBuilder,
            workflow_builder_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流执行器
        def workflow_executor_factory():
            from src.core.workflow.execution.executor import WorkflowExecutor
            return WorkflowExecutor()
        
        container.register_factory(
            IWorkflowExecutor,
            workflow_executor_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流验证器
        def workflow_validator_factory():
            from src.core.workflow.validation import WorkflowValidator
            return WorkflowValidator()
        
        container.register_factory(
            IWorkflowValidator,
            workflow_validator_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流协调器 - 使用现有的工厂函数
        def workflow_coordinator_factory():
            from src.core.workflow.coordinator.workflow_coordinator import create_workflow_coordinator
            from src.core.workflow.core.builder import IWorkflowBuilder as CoreIWorkflowBuilder
            from src.core.workflow.management.lifecycle import WorkflowLifecycleManager
            from src.core.workflow.graph_entities import Graph
            
            # 从容器获取依赖
            builder = container.get(CoreIWorkflowBuilder)
            executor = container.get(IWorkflowExecutor)
            validator = container.get(IWorkflowValidator)
            
            # 创建一个默认的图用于生命周期管理器
            graph = Graph(graph_id="default", name="Default Graph")
            lifecycle_manager = WorkflowLifecycleManager(graph)
            
            # 使用工厂函数创建协调器
            return create_workflow_coordinator(
                builder=builder,
                executor=executor,
                validator=validator,
                lifecycle_manager=lifecycle_manager
            )
        
        container.register_factory(
            IWorkflowCoordinator,
            workflow_coordinator_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册工作流编排器
        def workflow_orchestrator_factory():
            from src.services.workflow.workflow_orchestrator import WorkflowOrchestrator
            
            workflow_coordinator = container.get(IWorkflowCoordinator)
            
            # 获取日志实例
            logger = None
            try:
                logger = container.get(ILogger)
            except:
                pass
            
            return WorkflowOrchestrator(workflow_coordinator, logger)
        
        container.register_factory(
            IWorkflowService,
            workflow_orchestrator_factory,
            lifetime=ServiceLifetime.SINGLETON
        )


class DynamicWorkflowCoordinator:
    """动态工作流协调器 - 延迟创建生命周期管理器"""
    
    def __init__(self, builder, executor, validator, lifecycle_manager_factory):
        """初始化动态协调器
        
        Args:
            builder: 工作流构建器
            executor: 工作流执行器
            validator: 工作流验证器
            lifecycle_manager_factory: 生命周期管理器工厂
        """
        self._builder = builder
        self._executor = executor
        self._validator = validator
        self._lifecycle_manager_factory = lifecycle_manager_factory
        self._logger = None
        
        # 缓存已创建的生命周期管理器
        self._lifecycle_managers = {}
    
    def get_lifecycle_manager(self, workflow_id: str):
        """获取特定工作流的生命周期管理器
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            WorkflowLifecycleManager: 生命周期管理器实例
        """
        if workflow_id not in self._lifecycle_managers:
            # 延迟创建生命周期管理器
            self._lifecycle_managers[workflow_id] = (
                self._lifecycle_manager_factory.create_for_workflow(workflow_id)
            )
        
        return self._lifecycle_managers[workflow_id]
    
    def create_workflow(self, config):
        """创建工作流"""
        from src.core.workflow.workflow import Workflow
        from src.core.workflow.graph_entities import Graph
        
        # 创建图实体
        graph = Graph(
            graph_id=config.get('workflow_id', 'default'),
            name=config.get('name', 'Default Workflow'),
            description=config.get('description', ''),
            version=config.get('version', '1.0'),
            entry_point=config.get('entry_point')
        )
        
        # 创建工作流实例
        workflow = Workflow(graph=graph)
        
        # 获取对应的生命周期管理器
        lifecycle_manager = self.get_lifecycle_manager(workflow.workflow_id)
        
        # 构建图
        compiled_graph = self._builder.build_graph(workflow)
        workflow.set_graph(compiled_graph)
        
        return workflow
    
    def execute_workflow(self, workflow, initial_state):
        """执行工作流"""
        return self._executor.execute(workflow, initial_state, None)
    
    def validate_workflow_config(self, config):
        """验证工作流配置"""
        from src.core.workflow.workflow import Workflow
        from src.core.workflow.graph_entities import Graph
        
        # 创建临时图和工作流用于验证
        temp_graph = Graph(
            graph_id=config.get('workflow_id', 'temp'),
            name=config.get('name', 'Temp Workflow')
        )
        temp_workflow = Workflow(graph=temp_graph)
        validation_result = self._validator.validate(temp_workflow)
        
        if not validation_result.is_valid:
            return validation_result.errors
        
        return []


class WorkflowLifecycleManagerFactory:
    """工作流生命周期管理器工厂"""
    
    def create_for_workflow(self, workflow_id: str):
        """为特定工作流创建生命周期管理器
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            WorkflowLifecycleManager: 生命周期管理器实例
        """
        from src.core.workflow.management.lifecycle import WorkflowLifecycleManager
        from src.core.workflow.graph_entities import Graph
        
        # 创建一个最小化的图，只包含必要的信息
        graph = Graph(
            graph_id=workflow_id,
            name=f"Workflow-{workflow_id}",
            description=f"Lifecycle manager for workflow {workflow_id}"
        )
        
        return WorkflowLifecycleManager(graph)