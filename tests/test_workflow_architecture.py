"""工作流架构测试

测试重构后的依赖注入架构。
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# 导入测试目标
from src.interfaces.workflow.registry import IWorkflowRegistry, IComponentRegistry, IFunctionRegistry
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.core import IWorkflow, IWorkflowValidator, IWorkflowBuilder, IWorkflowExecutor
from src.core.workflow.registry import WorkflowRegistry, ComponentRegistry, FunctionRegistry
from src.core.workflow.coordinator import WorkflowCoordinator, create_workflow_coordinator
from src.services.workflow import WorkflowServiceFactory, create_workflow_service_factory, WorkflowOrchestrator
from src.core.workflow.config.config import GraphConfig
from src.core.workflow.workflow import Workflow

logger = logging.getLogger(__name__)


class TestWorkflowRegistry:
    """测试工作流注册表"""
    
    def test_component_registry(self):
        """测试组件注册表"""
        registry = ComponentRegistry()
        
        # 测试注册节点
        mock_node_class = Mock()
        registry.register_node("test_node", mock_node_class)
        
        assert registry.get_node_class("test_node") == mock_node_class
        assert "test_node" in registry.list_node_types()
        
        # 测试注册边
        mock_edge_class = Mock()
        registry.register_edge("test_edge", mock_edge_class)
        
        assert registry.get_edge_class("test_edge") == mock_edge_class
        assert "test_edge" in registry.list_edge_types()
        
        # 测试清除
        registry.clear()
        assert registry.get_node_class("test_node") is None
        assert registry.get_edge_class("test_edge") is None
    
    def test_function_registry(self):
        """测试函数注册表"""
        registry = FunctionRegistry()
        
        # 测试注册节点函数
        mock_function = Mock()
        registry.register_node_function("test_function", mock_function)
        
        assert registry.get_node_function("test_function") == mock_function
        assert "test_function" in registry.list_node_functions()
        
        # 测试注册路由函数
        mock_route_function = Mock()
        registry.register_route_function("test_route", mock_route_function)
        
        assert registry.get_route_function("test_route") == mock_route_function
        assert "test_route" in registry.list_route_functions()
        
        # 测试清除
        registry.clear()
        assert registry.get_node_function("test_function") is None
        assert registry.get_route_function("test_route") is None
    
    def test_workflow_registry(self):
        """测试工作流注册表"""
        registry = WorkflowRegistry()
        
        # 测试属性
        assert isinstance(registry.component_registry, IComponentRegistry)
        assert isinstance(registry.function_registry, IFunctionRegistry)
        
        # 测试验证依赖
        errors = registry.validate_dependencies()
        assert isinstance(errors, list)
        
        # 测试统计信息
        stats = registry.get_registry_stats()
        assert "node_types" in stats
        assert "edge_types" in stats
        assert "node_functions" in stats
        assert "route_functions" in stats


class TestWorkflowCoordinator:
    """测试工作流协调器"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """创建模拟依赖"""
        mock_builder = Mock(spec=IWorkflowBuilder)
        mock_executor = Mock(spec=IWorkflowExecutor)
        mock_validator = Mock(spec=IWorkflowValidator)
        mock_lifecycle = Mock()
        mock_graph_service = Mock()
        
        # 设置模拟返回值
        mock_validator.validate.return_value = Mock(is_valid=True, errors=[])
        mock_builder.build_graph.return_value = Mock()
        mock_executor.execute.return_value = Mock()
        
        return {
            "builder": mock_builder,
            "executor": mock_executor,
            "validator": mock_validator,
            "lifecycle_manager": mock_lifecycle,
            "graph_service": mock_graph_service
        }
    
    def test_create_workflow_coordinator(self, mock_dependencies):
        """测试创建工作流协调器"""
        coordinator = create_workflow_coordinator(**mock_dependencies)
        
        assert isinstance(coordinator, IWorkflowCoordinator)
        assert coordinator._builder == mock_dependencies["builder"]
        assert coordinator._executor == mock_dependencies["executor"]
        assert coordinator._validator == mock_dependencies["validator"]
    
    def test_create_workflow(self, mock_dependencies):
        """测试创建工作流"""
        coordinator = create_workflow_coordinator(**mock_dependencies)
        
        # 创建测试配置
        config_dict = {
            "name": "test_workflow",
            "description": "测试工作流",
            "nodes": {
                "start": {
                    "type": "start_node",
                    "name": "开始"
                }
            },
            "edges": [],
            "entry_point": "start"
        }
        config = GraphConfig.from_dict(config_dict)
        
        # 创建工作流
        workflow = coordinator.create_workflow(config)
        
        assert isinstance(workflow, IWorkflow)
        assert workflow.name == "test_workflow"
        mock_validator.validate.assert_called_once()
        mock_builder.build_graph.assert_called_once()
    
    def test_execute_workflow(self, mock_dependencies):
        """测试执行工作流"""
        coordinator = create_workflow_coordinator(**mock_dependencies)
        
        # 创建模拟工作流和状态
        mock_workflow = Mock(spec=IWorkflow)
        mock_workflow.name = "test_workflow"
        mock_initial_state = Mock()
        mock_result_state = Mock()
        
        mock_executor.execute.return_value = mock_result_state
        
        # 执行工作流
        result = coordinator.execute_workflow(mock_workflow, mock_initial_state)
        
        assert result == mock_result_state
        mock_executor.execute.assert_called_once_with(mock_workflow, mock_initial_state, None)
    
    def test_validate_workflow_config(self, mock_dependencies):
        """测试验证工作流配置"""
        coordinator = create_workflow_coordinator(**mock_dependencies)
        
        # 创建测试配置
        config_dict = {
            "name": "test_workflow",
            "nodes": {},
            "edges": [],
            "entry_point": "start"
        }
        config = GraphConfig.from_dict(config_dict)
        
        # 验证配置
        errors = coordinator.validate_workflow_config(config)
        
        assert isinstance(errors, list)
        mock_validator.validate.assert_called_once()


class TestWorkflowServiceFactory:
    """测试工作流服务工厂"""
    
    @pytest.fixture
    def mock_container(self):
        """创建模拟容器"""
        container = Mock()
        container.has_service.return_value = True
        container.get.side_effect = lambda service_type: Mock()
        container.validate_configuration.return_value = Mock(is_valid=True, errors=[])
        container.get_registration_count.return_value = 10
        return container
    
    def test_create_workflow_service_factory(self, mock_container):
        """测试创建工作流服务工厂"""
        factory = create_workflow_service_factory(mock_container)
        
        assert isinstance(factory, WorkflowServiceFactory)
        assert factory._container == mock_container
    
    def test_register_workflow_services(self, mock_container):
        """测试注册工作流服务"""
        factory = create_workflow_service_factory(mock_container)
        
        # 注册服务
        factory.register_workflow_services(environment="test")
        
        # 验证注册调用
        assert mock_container.register.call_count > 0
    
    def test_validate_service_configuration(self, mock_container):
        """测试验证服务配置"""
        factory = create_workflow_service_factory(mock_container)
        
        # 验证配置
        errors = factory.validate_service_configuration()
        
        assert isinstance(errors, list)
        mock_container.validate_configuration.assert_called_once()


class TestWorkflowOrchestrator:
    """测试工作流编排器"""
    
    @pytest.fixture
    def mock_coordinator(self):
        """创建模拟协调器"""
        coordinator = Mock(spec=IWorkflowCoordinator)
        coordinator.create_workflow.return_value = Mock()
        coordinator.execute_workflow.return_value = Mock()
        coordinator.validate_workflow_config.return_value = []
        return coordinator
    
    def test_create_workflow_orchestrator(self, mock_coordinator):
        """测试创建工作流编排器"""
        orchestrator = create_workflow_orchestrator(mock_coordinator)
        
        assert orchestrator._workflow_coordinator == mock_coordinator
    
    def test_orchestrate_workflow_execution(self, mock_coordinator):
        """测试编排工作流执行"""
        orchestrator = create_workflow_orchestrator(mock_coordinator)
        
        # 测试数据
        workflow_config = {"name": "test"}
        business_context = {"user_id": "user123"}
        
        # 执行编排
        result = orchestrator.orchestrate_workflow_execution(workflow_config, business_context)
        
        # 验证调用
        mock_coordinator.create_workflow.assert_called_once()
        mock_coordinator.execute_workflow.assert_called_once()
        
        assert isinstance(result, dict)
        assert "success" in result
    
    def test_validate_workflow_with_business_rules(self, mock_coordinator):
        """测试验证工作流业务规则"""
        orchestrator = create_workflow_orchestrator(mock_coordinator)
        
        # 测试数据
        workflow_config = {"name": "test"}
        business_context = {"user_id": "user123"}
        
        # 验证
        errors = orchestrator.validate_workflow_with_business_rules(workflow_config, business_context)
        
        # 验证调用
        mock_coordinator.validate_workflow_config.assert_called_once()
        
        assert isinstance(errors, list)


class TestArchitectureIntegration:
    """架构集成测试"""
    
    def test_end_to_end_workflow_creation(self):
        """端到端工作流创建测试"""
        # 创建注册表
        registry = WorkflowRegistry()
        
        # 注册测试节点类型
        mock_node_class = Mock()
        registry.component_registry.register_node("test_node", mock_node_class)
        
        # 创建测试配置
        config_dict = {
            "name": "integration_test",
            "description": "集成测试工作流",
            "nodes": {
                "start": {
                    "type": "test_node",
                    "name": "开始"
                }
            },
            "edges": [],
            "entry_point": "start"
        }
        config = GraphConfig.from_dict(config_dict)
        
        # 验证配置可以创建
        assert config.name == "integration_test"
        assert "start" in config.nodes
        
        # 验证注册表包含节点类型
        assert "test_node" in registry.component_registry.list_node_types()
    
    def test_dependency_injection_flow(self):
        """依赖注入流程测试"""
        # 创建模拟依赖
        mock_builder = Mock(spec=IWorkflowBuilder)
        mock_executor = Mock(spec=IWorkflowExecutor)
        mock_validator = Mock(spec=IWorkflowValidator)
        mock_lifecycle = Mock()
        
        # 设置模拟返回值
        mock_validator.validate.return_value = Mock(is_valid=True, errors=[])
        mock_builder.build_graph.return_value = Mock()
        mock_executor.execute.return_value = Mock()
        
        # 创建协调器
        coordinator = create_workflow_coordinator(
            builder=mock_builder,
            executor=mock_executor,
            validator=mock_validator,
            lifecycle_manager=mock_lifecycle
        )
        
        # 验证依赖注入成功
        assert coordinator._builder == mock_builder
        assert coordinator._executor == mock_executor
        assert coordinator._validator == mock_validator
        assert coordinator._lifecycle_manager == mock_lifecycle


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])