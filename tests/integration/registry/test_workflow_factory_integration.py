"""工作流工厂集成测试"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.application.workflow.factory import WorkflowFactory
from src.infrastructure.registry.module_registry_manager import ModuleRegistryManager
from src.infrastructure.graph.config import WorkflowConfig


class TestWorkflowFactoryIntegration:
    """测试工作流工厂集成"""
    
    @pytest.fixture
    def mock_registry_manager(self):
        """创建模拟注册管理器"""
        manager = Mock(spec=ModuleRegistryManager)
        manager.initialized = True
        
        # 模拟工作流类型
        workflow_types = {
            "react": Mock(
                name="react",
                class_path="src.application.workflow.factory:ReActWorkflow",
                description="ReAct workflow",
                enabled=True,
                config_files=["react_workflow.yaml"]
            ),
            "plan_execute": Mock(
                name="plan_execute",
                class_path="src.application.workflow.factory:PlanExecuteWorkflow",
                description="Plan execute workflow",
                enabled=True,
                config_files=["plan_execute.yaml"]
            )
        }
        manager.get_workflow_types.return_value = workflow_types
        
        # 模拟工作流配置
        workflow_config = {
            "name": "react_workflow",
            "description": "ReAct workflow",
            "version": "1.0.0",
            "metadata": {
                "name": "react_workflow",
                "version": "1.0.0",
                "description": "ReAct workflow"
            },
            "config_type": "workflow",
            "workflow_name": "react_workflow",
            "max_iterations": 20,
            "timeout": 600
        }
        manager.get_workflow_config.return_value = workflow_config
        
        # 模拟注册表信息
        manager.get_registry_info.return_value = {
            "initialized": True,
            "workflow_types": 2,
            "tool_types": 0,
            "state_machine_configs": 0
        }
        
        return manager
    
    @pytest.fixture
    def mock_config_loader(self):
        """创建模拟配置加载器"""
        loader = Mock()
        return loader
    
    @pytest.fixture
    def mock_container(self):
        """创建模拟容器"""
        container = Mock()
        return container
    
    @patch('src.application.workflow.factory.DynamicImporter')
    def test_create_workflow_with_registry(self, mock_dynamic_importer, mock_registry_manager, mock_config_loader, mock_container):
        """测试使用注册管理器创建工作流"""
        # 模拟动态导入器
        mock_importer = Mock()
        mock_dynamic_importer.return_value = mock_importer
        
        # 模拟工作流类
        mock_react_class = Mock()
        mock_plan_execute_class = Mock()
        
        def mock_import_class(class_path):
            if "ReActWorkflow" in class_path:
                return mock_react_class
            elif "PlanExecuteWorkflow" in class_path:
                return mock_plan_execute_class
            else:
                raise ImportError(f"Cannot import {class_path}")
        
        mock_importer.import_class.side_effect = mock_import_class
        
        # 创建工厂
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=mock_registry_manager
        )
        
        # 验证工作流类型已注册
        assert "react" in factory.get_supported_types()
        assert "plan_execute" in factory.get_supported_types()
        
        # 创建工作流配置
        config = WorkflowConfig(
            name="test_workflow",
            description="Test workflow",
            additional_config={"workflow_type": "react"}
        )
        
        # 创建工作流实例
        workflow = factory.create_workflow(config)
        
        # 验证工作流创建
        assert workflow is not None
        mock_react_class.assert_called_once_with(config, mock_config_loader, mock_container)
    
    @patch('src.application.workflow.factory.DynamicImporter')
    def test_create_workflow_from_registry(self, mock_dynamic_importer, mock_registry_manager, mock_config_loader, mock_container):
        """测试从注册表创建工作流"""
        # 模拟动态导入器
        mock_importer = Mock()
        mock_dynamic_importer.return_value = mock_importer
        
        # 模拟工作流类
        mock_react_class = Mock()
        mock_importer.import_class.return_value = mock_react_class
        
        # 创建工厂
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=mock_registry_manager
        )
        
        # 从注册表创建工作流
        workflow = factory.create_workflow_from_registry("react_workflow")
        
        # 验证工作流创建
        assert workflow is not None
        mock_react_class.assert_called_once()
        
        # 验证配置获取
        mock_registry_manager.get_workflow_config.assert_called_once_with("react_workflow")
    
    def test_create_workflow_without_registry(self, mock_config_loader, mock_container):
        """测试不使用注册管理器创建工作流"""
        # 创建工厂（不使用注册管理器）
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=None
        )
        
        # 验证只有基础工作流类型
        supported_types = factory.get_supported_types()
        assert "base" in supported_types
        assert len(supported_types) == 1
        
        # 创建工作流配置
        config = WorkflowConfig(
            name="test_workflow",
            description="Test workflow",
            additional_config={"workflow_type": "base"}
        )
        
        # 创建工作流实例（应该使用基础工作流）
        # 直接替换_workflow_types中的base类
        original_base_class = factory._workflow_types["base"]
        mock_base_class = Mock()
        mock_instance = Mock()
        mock_base_class.return_value = mock_instance
        factory._workflow_types["base"] = mock_base_class
        
        try:
            workflow = factory.create_workflow(config)
            
            # 验证工作流创建
            assert workflow is not None
            mock_base_class.assert_called_once_with(config, mock_config_loader, mock_container)
        finally:
            # 恢复原始类
            factory._workflow_types["base"] = original_base_class
    
    @patch('src.application.workflow.factory.DynamicImporter')
    def test_reload_from_registry(self, mock_dynamic_importer, mock_registry_manager, mock_config_loader, mock_container):
        """测试从注册表重新加载"""
        # 模拟动态导入器
        mock_importer = Mock()
        mock_dynamic_importer.return_value = mock_importer
        
        # 模拟工作流类
        mock_react_class = Mock()
        mock_importer.import_class.return_value = mock_react_class
        
        # 创建工厂
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=mock_registry_manager
        )
        
        # 验证初始状态
        assert len(factory.get_supported_types()) == 2
        
        # 重新加载
        factory.reload_from_registry()
        
        # 验证重新加载后仍然有工作流类型
        assert len(factory.get_supported_types()) == 2
        
        # 验证注册管理器方法被调用
        mock_registry_manager.get_workflow_types.assert_called()
    
    def test_get_registry_info(self, mock_registry_manager, mock_config_loader, mock_container):
        """测试获取注册表信息"""
        # 创建工厂
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=mock_registry_manager
        )
        
        # 获取注册表信息
        info = factory.get_registry_info()
        
        # 验证信息
        assert info is not None
        assert info["initialized"] is True
        assert info["workflow_types"] == 2
        
        # 验证注册管理器方法被调用
        mock_registry_manager.get_registry_info.assert_called_once()
    
    def test_get_registry_info_without_registry(self, mock_config_loader, mock_container):
        """测试不使用注册管理器时获取注册表信息"""
        # 创建工厂（不使用注册管理器）
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=None
        )
        
        # 获取注册表信息
        info = factory.get_registry_info()
        
        # 验证信息为None
        assert info is None
    
    @patch('src.application.workflow.factory.DynamicImporter')
    @patch('src.application.workflow.factory.HotReloadManager')
    def test_hot_reload_setup(self, mock_hot_reload_manager, mock_dynamic_importer, mock_registry_manager, mock_config_loader, mock_container):
        """测试热重载设置"""
        # 模拟热重载管理器
        mock_manager = Mock()
        mock_hot_reload_manager.return_value = mock_manager
        
        # 模拟动态导入器
        mock_importer = Mock()
        mock_dynamic_importer.return_value = mock_importer
        
        # 模拟工作流类
        mock_react_class = Mock()
        mock_importer.import_class.return_value = mock_react_class
        
        # 创建工厂
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=mock_registry_manager
        )
        
        # 验证热重载管理器已创建
        assert factory.hot_reload_manager is mock_manager
        
        # 验证监听器已添加
        mock_manager.add_listener.assert_called_once()
        
        # 验证回调已添加
        mock_manager.add_callback.assert_called_once()
        
        # 验证热重载已启动
        mock_manager.start.assert_called_once()
    
    @patch('src.application.workflow.factory.DynamicImporter')
    @patch('src.application.workflow.factory.HotReloadManager')
    def test_hot_reload_event_handling(self, mock_hot_reload_manager, mock_dynamic_importer, mock_registry_manager, mock_config_loader, mock_container):
        """测试热重载事件处理"""
        # 模拟热重载管理器
        mock_manager = Mock()
        mock_hot_reload_manager.return_value = mock_manager
        
        # 模拟动态导入器
        mock_importer = Mock()
        mock_dynamic_importer.return_value = mock_importer
        
        # 模拟工作流类
        mock_react_class = Mock()
        mock_importer.import_class.return_value = mock_react_class
        
        # 创建工厂
        factory = WorkflowFactory(
            container=mock_container,
            config_loader=mock_config_loader,
            registry_manager=mock_registry_manager
        )
        
        # 模拟热重载事件
        mock_event = Mock()
        mock_event.file_path = "configs/workflows/__registry__.yaml"
        
        # 处理热重载事件
        factory._handle_hot_reload_event(mock_event)
        
        # 验证重新加载被调用
        mock_registry_manager.clear_cache.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])