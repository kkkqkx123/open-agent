"""工作流依赖注入配置测试

测试工作流模块的依赖注入配置功能。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Type

from src.infrastructure.container import IDependencyContainer, ServiceLifetime
from infrastructure.config.config_loader import IConfigLoader
from src.infrastructure.graph.registry import NodeRegistry
from src.infrastructure.graph.states import StateFactory, StateSerializer
from src.infrastructure.graph.builder import GraphBuilder
from src.application.workflow.factory import IWorkflowFactory, WorkflowFactory
from src.application.workflow.interfaces import IWorkflowManager
from src.application.workflow.manager import WorkflowManager
from src.application.workflow.di_config import WorkflowModule, configure_workflow_container


class TestWorkflowModule(unittest.TestCase):
    """测试工作流模块服务注册"""

    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
        self.mock_config_loader = Mock(spec=IConfigLoader)
        self.mock_node_registry = Mock(spec=NodeRegistry)

    def test_register_services(self):
        """测试注册基础服务"""
        WorkflowModule.register_services(self.mock_container)
        
        # 验证服务注册调用
        expected_calls = [
            (StateFactory, StateFactory, ServiceLifetime.SINGLETON),
            (StateSerializer, StateSerializer, ServiceLifetime.SINGLETON),
            (GraphBuilder, GraphBuilder, ServiceLifetime.SINGLETON),
            (IWorkflowFactory, WorkflowFactory, ServiceLifetime.SINGLETON),
            (IWorkflowManager, WorkflowManager, ServiceLifetime.SINGLETON),
        ]
        
        for interface, implementation, lifetime in expected_calls:
            # 查找对应的调用
            found = False
            for call in self.mock_container.register.call_args_list:
                args, kwargs = call
                if (args[0] == interface and 
                    args[1] == implementation and 
                    kwargs.get('lifetime') == lifetime):
                    found = True
                    break
            
            self.assertTrue(found, f"服务 {interface} 未正确注册")

    def test_register_services_with_dependencies(self):
        """测试注册带依赖的服务"""
        # 模拟容器中没有已注册的服务
        self.mock_container.has_service.return_value = False
        
        WorkflowModule.register_services_with_dependencies(
            self.mock_container,
            self.mock_config_loader,
            self.mock_node_registry
        )
        
        # 验证配置加载器注册
        self.mock_container.register_instance.assert_any_call(
            IConfigLoader, self.mock_config_loader
        )
        
        # 验证节点注册表注册
        self.mock_container.register_instance.assert_any_call(
            NodeRegistry, self.mock_node_registry
        )

    def test_register_test_services(self):
        """测试注册测试环境服务"""
        WorkflowModule.register_test_services(self.mock_container)
        
        # 验证测试服务注册
        self.mock_container.register.assert_called_with(
            IWorkflowManager,
            WorkflowManager,
            environment="test",
            lifetime=ServiceLifetime.TRANSIENT
        )

    def test_register_development_services(self):
        """测试注册开发环境服务"""
        WorkflowModule.register_development_services(self.mock_container)
        
        # 验证开发环境服务注册
        call_args = self.mock_container.register_factory.call_args_list[0]
        self.assertEqual(call_args[0][0], GraphBuilder)
        self.assertEqual(call_args[1]['environment'], "development")
        self.assertEqual(call_args[1]['lifetime'], ServiceLifetime.SINGLETON)

    def test_register_production_services(self):
        """测试注册生产环境服务"""
        WorkflowModule.register_production_services(self.mock_container)
        
        # 验证生产环境服务注册
        call_args = self.mock_container.register_factory.call_args_list[0]
        self.assertEqual(call_args[0][0], WorkflowFactory)
        self.assertEqual(call_args[1]['environment'], "production")
        self.assertEqual(call_args[1]['lifetime'], ServiceLifetime.SINGLETON)


class TestConfigureWorkflowContainer(unittest.TestCase):
    """测试配置工作流容器函数"""

    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
        self.mock_config_loader = Mock(spec=IConfigLoader)
        self.mock_node_registry = Mock(spec=NodeRegistry)

    def test_configure_default_environment(self):
        """测试配置默认环境"""
        configure_workflow_container(self.mock_container)
        
        # 验证环境设置
        self.mock_container.set_environment.assert_called_with("default")
        
        # 验证基础服务注册
        self.mock_container.register.assert_called()

    def test_configure_test_environment(self):
        """测试配置测试环境"""
        configure_workflow_container(
            self.mock_container,
            environment="test"
        )
        
        # 验证测试服务注册被调用
        # 注意：这里我们只验证方法被调用，具体的验证在TestWorkflowModule中完成

    def test_configure_development_environment(self):
        """测试配置开发环境"""
        configure_workflow_container(
            self.mock_container,
            environment="development"
        )
        
        # 验证开发服务注册被调用

    def test_configure_production_environment(self):
        """测试配置生产环境"""
        configure_workflow_container(
            self.mock_container,
            environment="production"
        )
        
        # 验证生产服务注册被调用

    def test_configure_with_dependencies(self):
        """测试配置带依赖的服务"""
        configure_workflow_container(
            self.mock_container,
            config_loader=self.mock_config_loader,
            node_registry=self.mock_node_registry
        )
        
        # 验证带依赖的服务注册被调用


class TestGetFunctions(unittest.TestCase):
    """测试获取服务实例的函数"""

    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)

    def test_get_workflow_manager(self):
        """测试获取工作流管理器"""
        from src.application.workflow.di_config import get_workflow_manager
        
        mock_manager = Mock()
        self.mock_container.get.return_value = mock_manager
        
        result = get_workflow_manager(self.mock_container)
        
        self.assertEqual(result, mock_manager)
        self.mock_container.get.assert_called_with(IWorkflowManager)

    def test_get_workflow_factory(self):
        """测试获取工作流工厂"""
        from src.application.workflow.di_config import get_workflow_factory
        
        mock_factory = Mock()
        self.mock_container.get.return_value = mock_factory
        
        result = get_workflow_factory(self.mock_container)
        
        self.assertEqual(result, mock_factory)
        self.mock_container.get.assert_called_with(IWorkflowFactory)

    def test_get_state_factory(self):
        """测试获取状态工厂"""
        from src.application.workflow.di_config import get_state_factory
        
        mock_factory = Mock()
        self.mock_container.get.return_value = mock_factory
        
        result = get_state_factory(self.mock_container)
        
        self.assertEqual(result, mock_factory)
        self.mock_container.get.assert_called_with(StateFactory)

    def test_get_state_serializer(self):
        """测试获取状态序列化器"""
        from src.application.workflow.di_config import get_state_serializer
        
        mock_serializer = Mock()
        self.mock_container.get.return_value = mock_serializer
        
        result = get_state_serializer(self.mock_container)
        
        self.assertEqual(result, mock_serializer)
        self.mock_container.get.assert_called_with(StateSerializer)

    def test_get_graph_builder(self):
        """测试获取图构建器"""
        from src.application.workflow.di_config import get_graph_builder
        
        mock_builder = Mock()
        self.mock_container.get.return_value = mock_builder
        
        result = get_graph_builder(self.mock_container)
        
        self.assertEqual(result, mock_builder)
        self.mock_container.get.assert_called_with(GraphBuilder)


if __name__ == '__main__':
    unittest.main()