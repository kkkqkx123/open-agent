"""工作流服务依赖注入绑定配置

使用基础设施层组件，通过继承BaseServiceBindings简化代码。
将工作流注册表迁移到依赖注入容器模式，提高测试性和配置灵活性。
"""

import sys
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环依赖
    from src.core.workflow.core.registry import WorkflowRegistry
    from src.core.workflow.workflow import Workflow
    from src.interfaces.workflow.core import IWorkflow
    from src.interfaces.workflow.registry import IWorkflowRegistry
    from src.interfaces.workflow.builders import IWorkflowBuilder
    from src.interfaces.workflow.execution import IWorkflowExecutor
    from src.interfaces.workflow.core import IWorkflowValidator
    from src.core.workflow.management.lifecycle import WorkflowLifecycleManager
    from src.core.workflow.coordinator import WorkflowCoordinator

# 接口导入 - 集中化的接口定义
from src.interfaces.workflow.core import IWorkflowRegistry  # 工作流实例注册表接口
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.workflow.builders import IWorkflowBuilder
from src.interfaces.workflow.execution import IWorkflowExecutor
from src.interfaces.workflow.core import IWorkflowValidator
from src.interfaces.logger import ILogger
from src.interfaces.container.core import ServiceLifetime
from src.services.container.core.base_service_bindings import BaseServiceBindings


class WorkflowServiceBindings(BaseServiceBindings):
    """工作流服务绑定类
    
    负责注册所有工作流相关服务，包括：
    - 工作流注册表
    - 工作流构建器
    - 工作流执行器
    - 工作流验证器
    - 工作流生命周期管理器
    - 工作流协调器
    - 具体工作流实例
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证工作流配置"""
        workflow_config = config.get("workflow", {})
        if not isinstance(workflow_config, dict):
            raise ValueError("工作流配置必须是一个字典")
        
        # 验证工作流定义
        workflow_definitions = workflow_config.get("workflows", {})
        if not isinstance(workflow_definitions, dict):
            raise ValueError("工作流定义必须是一个字典")
    
    def _do_register_services(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行工作流服务注册"""
        _register_workflow_registry(container, config, environment)
        _register_workflow_builder(container, config, environment)
        _register_workflow_executor(container, config, environment)
        _register_workflow_validator(container, config, environment)
        _register_workflow_lifecycle_manager(container, config, environment)
        _register_workflow_coordinator(container, config, environment)
        _register_workflow_instances(container, config, environment)
    
    def _post_register(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 为工作流服务设置注入层
            service_types = [
                IWorkflowRegistry,
                IWorkflowBuilder,
                IWorkflowExecutor,
                IWorkflowValidator,
                WorkflowLifecycleManager,
                WorkflowCoordinator
            ]
            
            self.setup_injection_layer(container, service_types)
            
            logger = self.safe_get_service(container, ILogger)
            if logger:
                logger.debug(f"已设置工作流服务注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置工作流注入层失败: {e}", file=sys.stderr)


def _register_workflow_registry(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册工作流注册表
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 创建注册表工厂函数
    def workflow_registry_factory() -> 'WorkflowRegistry':
        from src.core.workflow.core.registry import WorkflowRegistry
        return WorkflowRegistry()
    
    # 注册注册表为单例
    container.register(
        IWorkflowRegistry,
        workflow_registry_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Workflow registry registered", file=sys.stdout)


def _register_workflow_builder(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册工作流构建器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 创建构建器工厂函数
    def workflow_builder_factory() -> IWorkflowBuilder:
        from src.core.workflow.core.builder import WorkflowBuilder
        return WorkflowBuilder()
    
    # 注册构建器为瞬态
    container.register(
        IWorkflowBuilder,
        workflow_builder_factory,
        environment=environment,
        lifetime=ServiceLifetime.TRANSIENT
    )
    
    print(f"[INFO] Workflow builder registered", file=sys.stdout)


def _register_workflow_executor(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册工作流执行器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 创建执行器工厂函数
    def workflow_executor_factory() -> IWorkflowExecutor:
        from src.core.workflow.execution.executor import WorkflowExecutor
        return WorkflowExecutor()
    
    # 注册执行器为单例
    container.register(
        IWorkflowExecutor,
        workflow_executor_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Workflow executor registered", file=sys.stdout)


def _register_workflow_validator(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册工作流验证器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 创建验证器工厂函数
    def workflow_validator_factory() -> IWorkflowValidator:
        from src.core.workflow.validation import WorkflowValidator
        return WorkflowValidator()
    
    # 注册验证器为单例
    container.register(
        IWorkflowValidator,
        workflow_validator_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Workflow validator registered", file=sys.stdout)


def _register_workflow_lifecycle_manager(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册工作流生命周期管理器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 创建生命周期管理器工厂函数
    def workflow_lifecycle_manager_factory() -> WorkflowLifecycleManager:
        from src.core.workflow.management.lifecycle import WorkflowLifecycleManager
        from src.core.workflow.graph_entities import GraphConfig
        
        # 创建默认配置
        default_config = GraphConfig(
            name="default_workflow",
            description="默认工作流配置"
        )
        
        return WorkflowLifecycleManager(default_config)
    
    # 注册生命周期管理器为作用域
    container.register(
        WorkflowLifecycleManager,
        workflow_lifecycle_manager_factory,
        environment=environment,
        lifetime=ServiceLifetime.SCOPED
    )
    
    print(f"[INFO] Workflow lifecycle manager registered", file=sys.stdout)


def _register_workflow_coordinator(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册工作流协调器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_workflow_builder(container, config, environment)
    _register_workflow_executor(container, config, environment)
    _register_workflow_validator(container, config, environment)
    _register_workflow_lifecycle_manager(container, config, environment)
    
    # 创建协调器工厂函数
    def workflow_coordinator_factory() -> WorkflowCoordinator:
        from src.core.workflow.coordinator import create_workflow_coordinator
        
        builder = container.get(IWorkflowBuilder)
        executor = container.get(IWorkflowExecutor)
        validator = container.get(IWorkflowValidator)
        lifecycle_manager = container.get(WorkflowLifecycleManager)
        
        return create_workflow_coordinator(
            builder=builder,
            executor=executor,
            validator=validator,
            lifecycle_manager=lifecycle_manager
        )
    
    # 注册协调器为瞬态
    container.register(
        WorkflowCoordinator,
        workflow_coordinator_factory,
        environment=environment,
        lifetime=ServiceLifetime.TRANSIENT
    )
    
    print(f"[INFO] Workflow coordinator registered", file=sys.stdout)


def _register_workflow_instances(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册具体工作流实例
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保注册表已注册
    _register_workflow_registry(container, config, environment)
    
    workflow_config = config.get("workflow", {})
    workflow_definitions = workflow_config.get("workflows", {})
    
    if not workflow_definitions:
        print(f"[INFO] No workflow definitions found in config", file=sys.stdout)
        return
    
    # 注册每个工作流实例
    for workflow_id, workflow_config in workflow_definitions.items():
        try:
            # 创建工作流工厂函数
            def workflow_factory(wc=workflow_config, wid=workflow_id) -> IWorkflow:
                from src.core.workflow.graph_entities import GraphConfig
                from src.core.workflow.workflow import Workflow
                
                # 创建图配置
                graph_config = GraphConfig(
                    name=wid,
                    description=wc.get("description", f"工作流 {wid}"),
                    nodes=wc.get("nodes", {}),
                    edges=wc.get("edges", []),
                    entry_point=wc.get("entry_point")
                )
                
                # 创建工作流实例
                workflow = Workflow(graph_config)
                
                # 注册到注册表
                registry = container.get(IWorkflowRegistry)
                registry.register_workflow(wid, workflow)
                
                return workflow
            
            # 注册工作流实例为单例
            container.register(
                f"workflow_{workflow_id}",
                workflow_factory,
                environment=environment,
                lifetime=ServiceLifetime.SINGLETON
            )
            
            print(f"[INFO] Workflow instance registered: {workflow_id}", file=sys.stdout)
            
        except Exception as e:
            print(f"[ERROR] Failed to register workflow {workflow_id}: {e}", file=sys.stderr)


def _load_workflow_configs_from_files(config: Dict[str, Any]) -> Dict[str, Any]:
    """从配置文件加载工作流定义
    
    Args:
        config: 配置字典
        
    Returns:
        Dict[str, Any]: 工作流定义字典
    """
    import os
    import yaml
    from pathlib import Path
    
    workflow_config = config.get("workflow", {})
    workflow_definitions = {}
    
    # 从配置目录加载工作流文件
    config_dirs = workflow_config.get("config_directories", ["configs/workflows"])
    
    for config_dir in config_dirs:
        if not os.path.exists(config_dir):
            continue
            
        for file_path in Path(config_dir).glob("*.yaml"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    
                if file_config and 'name' in file_config:
                    workflow_id = file_config['name']
                    workflow_definitions[workflow_id] = file_config
                    
            except Exception as e:
                print(f"[WARNING] Failed to load workflow config {file_path}: {e}", file=sys.stderr)
    
    return workflow_definitions


# 便捷函数
def create_workflow_service_bindings() -> WorkflowServiceBindings:
    """创建工作流服务绑定实例
    
    Returns:
        WorkflowServiceBindings: 服务绑定实例
    """
    return WorkflowServiceBindings()


# 导出实现
__all__ = [
    "WorkflowServiceBindings",
    "create_workflow_service_bindings",
]