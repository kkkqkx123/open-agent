"""工作流模块依赖注入配置测试

测试工作流模块的依赖注入配置功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, ANY
from typing import Type, Optional

from src.application.workflow.di_config import (
    WorkflowModule, configure_workflow_container,
    get_workflow_manager, get_workflow_factory,
    get_state_factory, get_state_serializer
)
from src.infrastructure.container import IDependencyContainer, ServiceLifetime
from src.infrastructure.config_loader import IConfigLoader
from src.infrastructure.graph.registry import NodeRegistry
from src.infrastructure.graph.states import StateFactory, StateSerializer
from src.application.workflow.interfaces import IWorkflowManager
from src.application.workflow.factory import IWorkflowFactory
from src.application.workflow.manager import WorkflowManager
from src.application.workflow.factory import WorkflowFactory
from src.application.workflow.builder_adapter import WorkflowBuilderAdapter


class TestWorkflowModule(unittest.TestCase):
    """测试工作流模块服务注册配置"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
    
    def test_register_services(self):
        """测试注册基础服务"""
        # 注册服务
        WorkflowModule.register_services(self.mock_container)
        
        # 验证注册调用
        expected_calls = [
            (StateFactory, StateFactory, ServiceLifetime.SINGLETON),
            (StateSerializer, StateSerializer, ServiceLifetime.SINGLETON),
            (WorkflowBuilderAdapter, WorkflowBuilderAdapter, ServiceLifetime.TRANSIENT),
            (IWorkflowFactory, WorkflowFactory, ServiceLifetime.SINGLETON),
            (IWorkflowManager, WorkflowManager, ServiceLifetime.SINGLETON)
        ]
        
        self.assertEqual(self.mock_container.register.call_count, len(expected_calls))
        
        for i, (service_type, implementation, lifetime) in enumerate(expected_calls):
            call_args = self.mock_container.register.call_args_list[i]
            self.assertEqual(call_args[0][0], service_type)
            self.assertEqual(call_args[0][1], implementation)
            self.assertEqual(call_args[1]['lifetime'], lifetime)
    
    def test_register_services_with_dependencies(self):
        """测试注册带依赖的服务"""
        # 创建模拟依赖
        mock_config_loader = Mock(spec=IConfigLoader)
        mock_node_registry = Mock(spec=NodeRegistry)
        
        # 注册服务
        WorkflowModule.register_services_with_dependencies(
            self.mock_container,
            mock_config_loader,
            mock_node_registry
        )
        
        # 验证has_service检查
        self.mock_container.has_service.assert_any_call(IConfigLoader)
        self.mock_container.has_service.assert_any_call(NodeRegistry)
        
        # 验证实例注册
        self.mock_container.register_instance.assert_any_call(IConfigLoader, mock_config_loader)
        self.mock_container.register_instance.assert_any_call(NodeRegistry, mock_node_registry)
        
        # 验证工厂注册
        self.assertEqual(self.mock_container.register_factory.call_count, 3)
        
        # 验证WorkflowBuilderAdapter工厂注册
        builder_adapter_call = self.mock_container.register_factory.call_args_list[0]
        self.assertEqual(builder_adapter_call[0][0], WorkflowBuilderAdapter)
        self.assertEqual(builder_adapter_call[1]['lifetime'], ServiceLifetime.TRANSIENT)
        
        # 验证WorkflowFactory工厂注册
        factory_call = self.mock_container.register_factory.call_args_list[1]
        self.assertEqual(factory_call[0][0], IWorkflowFactory)
        self.assertEqual(factory_call[1]['lifetime'], ServiceLifetime.SINGLETON)
        
        # 验证WorkflowManager工厂注册
        manager_call = self.mock_container.register_factory.call_args_list[2]
        self.assertEqual(manager_call[0][0], IWorkflowManager)
        self.assertEqual(manager_call[1]['lifetime'], ServiceLifetime.SINGLETON)
    
    def test_register_services_with_dependencies_already_registered(self):
        """测试注册带依赖的服务（依赖已注册）"""
        # 设置has_service返回True
        self.mock_container.has_service.return_value = True
        
        # 创建模拟依赖
        mock_config_loader = Mock(spec=IConfigLoader)
        mock_node_registry = Mock(spec=NodeRegistry)
        
        # 注册服务
        WorkflowModule.register_services_with_dependencies(
            self.mock_container,
            mock_config_loader,
            mock_node_registry
        )
        
        # 验证没有重复注册实例
        self.mock_container.register_instance.assert_not_called()
        
        # 验证仍然注册了工厂
        self.assertEqual(self.mock_container.register_factory.call_count, 3)
    
    def test_register_test_services(self):
        """测试注册测试环境专用服务"""
        # 注册测试服务
        WorkflowModule.register_test_services(self.mock_container)
        
        # 验证实例注册
        self.mock_container.register_instance.assert_any_call(IConfigLoader, ANY, "test")
        self.mock_container.register_instance.assert_any_call(NodeRegistry, ANY, "test")
        
        # 验证工作流管理器注册
        manager_call = self.mock_container.register.call_args_list[0]
        self.assertEqual(manager_call[0][0], IWorkflowManager)
        self.assertEqual(manager_call[0][1], WorkflowManager)
        self.assertEqual(manager_call[1]['environment'], "test")
        self.assertEqual(manager_call[1]['lifetime'], ServiceLifetime.TRANSIENT)
    
    def test_register_development_services(self):
        """测试注册开发环境专用服务"""
        # 注册开发服务
        WorkflowModule.register_development_services(self.mock_container)
        
        # 验证工厂注册
        self.assertEqual(self.mock_container.register_factory.call_count, 1)
        
        call_args = self.mock_container.register_factory.call_args_list[0]
        self.assertEqual(call_args[0][0], WorkflowBuilderAdapter)
        self.assertEqual(call_args[1]['environment'], "development")
        self.assertEqual(call_args[1]['lifetime'], ServiceLifetime.TRANSIENT)
    
    def test_register_production_services(self):
        """测试注册生产环境专用服务"""
        # 注册生产服务
        WorkflowModule.register_production_services(self.mock_container)
        
        # 验证工厂注册
        self.assertEqual(self.mock_container.register_factory.call_count, 1)
        
        call_args = self.mock_container.register_factory.call_args_list[0]
        self.assertEqual(call_args[0][0], WorkflowFactory)
        self.assertEqual(call_args[1]['environment'], "production")
        self.assertEqual(call_args[1]['lifetime'], ServiceLifetime.SINGLETON)


class TestConfigureWorkflowContainer(unittest.TestCase):
    """测试配置工作流容器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
        self.mock_config_loader = Mock(spec=IConfigLoader)
        self.mock_node_registry = Mock(spec=NodeRegistry)
    
    @patch('src.application.workflow.di_config.WorkflowModule')
    def test_configure_default_environment(self, mock_workflow_module):
        """测试配置默认环境"""
        # 配置容器
        configure_workflow_container(self.mock_container)
        
        # 验证环境设置
        self.mock_container.set_environment.assert_called_once_with("default")
        
        # 验证基础服务注册
        mock_workflow_module.register_services.assert_called_once_with(self.mock_container)
        
        # 验证没有注册环境特定服务
        mock_workflow_module.register_test_services.assert_not_called()
        mock_workflow_module.register_development_services.assert_not_called()
        mock_workflow_module.register_production_services.assert_not_called()
        
        # 验证没有注册带依赖的服务
        mock_workflow_module.register_services_with_dependencies.assert_not_called()
    
    @patch('src.application.workflow.di_config.WorkflowModule')
    def test_configure_test_environment(self, mock_workflow_module):
        """测试配置测试环境"""
        # 配置容器
        configure_workflow_container(self.mock_container, environment="test")
        
        # 验证环境设置
        self.mock_container.set_environment.assert_called_once_with("test")
        
        # 验证基础服务注册
        mock_workflow_module.register_services.assert_called_once_with(self.mock_container)
        
        # 验证测试服务注册
        mock_workflow_module.register_test_services.assert_called_once_with(self.mock_container)
        
        # 验证没有注册其他环境服务
        mock_workflow_module.register_development_services.assert_not_called()
        mock_workflow_module.register_production_services.assert_not_called()
    
    @patch('src.application.workflow.di_config.WorkflowModule')
    def test_configure_development_environment(self, mock_workflow_module):
        """测试配置开发环境"""
        # 配置容器
        configure_workflow_container(self.mock_container, environment="development")
        
        # 验证环境设置
        self.mock_container.set_environment.assert_called_once_with("development")
        
        # 验证基础服务注册
        mock_workflow_module.register_services.assert_called_once_with(self.mock_container)
        
        # 验证开发服务注册
        mock_workflow_module.register_development_services.assert_called_once_with(self.mock_container)
        
        # 验证没有注册其他环境服务
        mock_workflow_module.register_test_services.assert_not_called()
        mock_workflow_module.register_production_services.assert_not_called()
    
    @patch('src.application.workflow.di_config.WorkflowModule')
    def test_configure_production_environment(self, mock_workflow_module):
        """测试配置生产环境"""
        # 配置容器
        configure_workflow_container(self.mock_container, environment="production")
        
        # 验证环境设置
        self.mock_container.set_environment.assert_called_once_with("production")
        
        # 验证基础服务注册
        mock_workflow_module.register_services.assert_called_once_with(self.mock_container)
        
        # 验证生产服务注册
        mock_workflow_module.register_production_services.assert_called_once_with(self.mock_container)
        
        # 验证没有注册其他环境服务
        mock_workflow_module.register_test_services.assert_not_called()
        mock_workflow_module.register_development_services.assert_not_called()
    
    @patch('src.application.workflow.di_config.WorkflowModule')
    def test_configure_with_dependencies(self, mock_workflow_module):
        """测试配置带依赖的容器"""
        # 配置容器
        configure_workflow_container(
            self.mock_container,
            config_loader=self.mock_config_loader,
            node_registry=self.mock_node_registry
        )
        
        # 验证环境设置
        self.mock_container.set_environment.assert_called_once_with("default")
        
        # 验证基础服务注册
        mock_workflow_module.register_services.assert_called_once_with(self.mock_container)
        
        # 验证带依赖的服务注册
        mock_workflow_module.register_services_with_dependencies.assert_called_once_with(
            self.mock_container, self.mock_config_loader, self.mock_node_registry
        )


class TestGetterFunctions(unittest.TestCase):
    """测试获取器函数"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
    
    def test_get_workflow_manager(self):
        """测试获取工作流管理器"""
        # 设置模拟
        mock_manager = Mock(spec=IWorkflowManager)
        self.mock_container.get.return_value = mock_manager
        
        # 获取工作流管理器
        result = get_workflow_manager(self.mock_container)
        
        # 验证结果
        self.assertEqual(result, mock_manager)
        
        # 验证调用
        self.mock_container.get.assert_called_once_with(IWorkflowManager)
    
    def test_get_workflow_factory(self):
        """测试获取工作流工厂"""
        # 设置模拟
        mock_factory = Mock(spec=IWorkflowFactory)
        self.mock_container.get.return_value = mock_factory
        
        # 获取工作流工厂
        result = get_workflow_factory(self.mock_container)
        
        # 验证结果
        self.assertEqual(result, mock_factory)
        
        # 验证调用
        self.mock_container.get.assert_called_once_with(IWorkflowFactory)
    
    def test_get_state_factory(self):
        """测试获取状态工厂"""
        # 设置模拟
        mock_state_factory = Mock(spec=StateFactory)
        self.mock_container.get.return_value = mock_state_factory
        
        # 获取状态工厂
        result = get_state_factory(self.mock_container)
        
        # 验证结果
        self.assertEqual(result, mock_state_factory)
        
        # 验证调用
        self.mock_container.get.assert_called_once_with(StateFactory)
    
    def test_get_state_serializer(self):
        """测试获取状态序列化器"""
        # 设置模拟
        mock_state_serializer = Mock(spec=StateSerializer)
        self.mock_container.get.return_value = mock_state_serializer
        
        # 获取状态序列化器
        result = get_state_serializer(self.mock_container)
        
        # 验证结果
        self.assertEqual(result, mock_state_serializer)
        
        # 验证调用
        self.mock_container.get.assert_called_once_with(StateSerializer)


class TestWorkflowModuleIntegration(unittest.TestCase):
    """测试工作流模块集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
    
    @patch('src.application.workflow.di_config.WorkflowModule')
    def test_full_configuration_flow(self, mock_workflow_module):
        """测试完整配置流程"""
        # 创建模拟服务
        mock_config_loader = Mock(spec=IConfigLoader)
        mock_node_registry = Mock(spec=NodeRegistry)
        mock_manager = Mock(spec=IWorkflowManager)
        mock_factory = Mock(spec=IWorkflowFactory)
        mock_state_factory = Mock(spec=StateFactory)
        mock_state_serializer = Mock(spec=StateSerializer)
        
        # 设置容器get方法返回不同的服务
        def mock_get_side_effect(service_type):
            if service_type == IWorkflowManager:
                return mock_manager
            elif service_type == IWorkflowFactory:
                return mock_factory
            elif service_type == StateFactory:
                return mock_state_factory
            elif service_type == StateSerializer:
                return mock_state_serializer
            else:
                return Mock()
        
        self.mock_container.get.side_effect = mock_get_side_effect
        
        # 配置容器
        configure_workflow_container(
            self.mock_container,
            environment="test",
            config_loader=mock_config_loader,
            node_registry=mock_node_registry
        )
        
        # 验证配置调用
        mock_workflow_module.register_services.assert_called_once()
        mock_workflow_module.register_test_services.assert_called_once()
        mock_workflow_module.register_services_with_dependencies.assert_called_once()
        
        # 获取服务
        manager = get_workflow_manager(self.mock_container)
        factory = get_workflow_factory(self.mock_container)
        state_factory = get_state_factory(self.mock_container)
        state_serializer = get_state_serializer(self.mock_container)
        
        # 验证获取的服务
        self.assertEqual(manager, mock_manager)
        self.assertEqual(factory, mock_factory)
        self.assertEqual(state_factory, mock_state_factory)
        self.assertEqual(state_serializer, mock_state_serializer)


if __name__ == '__main__':
    unittest.main()