"""工作流模板注册表测试

测试工作流模板的注册、获取和管理功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Optional, Any

from src.application.workflow.templates.registry import (
    WorkflowTemplateRegistry, get_global_template_registry,
    _register_builtin_templates, register_template, get_template,
    list_templates, create_workflow_from_template
)
from src.application.workflow.interfaces import IWorkflowTemplate, IWorkflowTemplateRegistry
from src.infrastructure.graph.config import WorkflowConfig


class TestWorkflowTemplateRegistry(unittest.TestCase):
    """测试工作流模板注册表实现"""
    
    def setUp(self) -> None:
        """设置测试环境"""
        self.registry = WorkflowTemplateRegistry()
        
        # 创建模拟模板
        self.mock_template1 = Mock(spec=IWorkflowTemplate)
        self.mock_template1.name = "test_template1"
        self.mock_template1.description = "Test template 1"
        self.mock_template1.get_parameters.return_value = [
            {"name": "param1", "type": "string", "description": "Parameter 1"}
        ]
        self.mock_template1.create_template.return_value = Mock(spec=WorkflowConfig)
        self.mock_template1.validate_parameters.return_value = []
        
        self.mock_template2 = Mock(spec=IWorkflowTemplate)
        self.mock_template2.name = "test_template2"
        self.mock_template2.description = "Test template 2"
        self.mock_template2.get_parameters.return_value = [
            {"name": "param2", "type": "integer", "description": "Parameter 2"}
        ]
        self.mock_template2.create_template.return_value = Mock(spec=WorkflowConfig)
        self.mock_template2.validate_parameters.return_value = []
    
    @patch('src.application.workflow.templates.registry.logger')
    def test_init(self, mock_logger: Any) -> None:
        """测试初始化"""
        # 重新创建registry以确保日志被调用
        registry = WorkflowTemplateRegistry()
        
        # 验证初始状态
        self.assertEqual(len(registry._templates), 0)
        self.assertEqual(len(registry._template_metadata), 0)
        
        # 验证日志
        mock_logger.info.assert_called_once_with("WorkflowTemplateRegistry初始化完成")
    
    @patch('src.application.workflow.templates.registry.logger')
    def test_register_template(self, mock_logger: Any) -> None:
        """测试注册模板"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        
        # 验证注册结果
        self.assertIn("test_template1", self.registry._templates)
        self.assertEqual(self.registry._templates["test_template1"], self.mock_template1)
        
        # 验证元数据
        metadata = self.registry._template_metadata["test_template1"]
        self.assertEqual(metadata["name"], "test_template1")
        self.assertEqual(metadata["description"], "Test template 1")
        self.assertEqual(metadata["parameters"], self.mock_template1.get_parameters.return_value)
        
        # 验证日志
        mock_logger.info.assert_called_with("注册模板: test_template1")
    
    @patch('src.application.workflow.templates.registry.logger')
    def test_register_template_overwrite(self, mock_logger) -> None:
        """测试覆盖已存在的模板"""
        # 注册第一个模板
        self.registry.register_template(self.mock_template1)
        
        # 注册同名模板（覆盖）
        new_template = Mock(spec=IWorkflowTemplate)
        new_template.name = "test_template1"
        new_template.description = "New template"
        new_template.get_parameters.return_value = []
        
        self.registry.register_template(new_template)
        
        # 验证覆盖结果
        self.assertEqual(self.registry._templates["test_template1"], new_template)
        
        # 验证警告日志
        mock_logger.warning.assert_called_with("模板 'test_template1' 已存在，将被覆盖")
    
    def test_register_template_none(self) -> None:
        """测试注册None模板"""
        # 注册None模板应该抛出异常
        with self.assertRaises(ValueError) as context:
            self.registry.register_template(None)  # type: ignore
        
        self.assertIn("模板实例不能为None", str(context.exception))
    
    def test_get_template(self) -> None:
        """测试获取模板"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        
        # 获取存在的模板
        result = self.registry.get_template("test_template1")
        self.assertEqual(result, self.mock_template1)
        
        # 获取不存在的模板
        result = self.registry.get_template("nonexistent")
        self.assertIsNone(result)
    
    def test_list_templates(self):
        """测试列出所有模板"""
        # 初始状态应该为空
        self.assertEqual(self.registry.list_templates(), [])
        
        # 注册模板
        self.registry.register_template(self.mock_template1)
        self.registry.register_template(self.mock_template2)
        
        # 列出模板
        templates = self.registry.list_templates()
        
        # 验证结果
        self.assertEqual(len(templates), 2)
        self.assertIn("test_template1", templates)
        self.assertIn("test_template2", templates)
    
    @patch('src.application.workflow.templates.registry.logger')
    def test_unregister_template(self, mock_logger):
        """测试注销模板"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        
        # 注销模板
        result = self.registry.unregister_template("test_template1")
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn("test_template1", self.registry._templates)
        self.assertNotIn("test_template1", self.registry._template_metadata)
        
        # 验证日志
        mock_logger.info.assert_called_with("注销模板: test_template1")
        
        # 注销不存在的模板
        result = self.registry.unregister_template("nonexistent")
        self.assertFalse(result)
    
    def test_get_template_info(self) -> None:
        """测试获取模板信息"""
        # 注册模板
        self.registry.register_template(self.mock_template1)

        # 获取模板信息
        info = self.registry.get_template_info("test_template1")

        # 验证结果
        self.assertIsNotNone(info)
        assert info is not None
        self.assertEqual(info["name"], "test_template1")
        self.assertEqual(info["description"], "Test template 1")
        self.assertEqual(info["parameters"], self.mock_template1.get_parameters.return_value)
        self.assertIn("metadata", info)
        
        # 获取不存在模板的信息
        info = self.registry.get_template_info("nonexistent")
        self.assertIsNone(info)
    
    def test_list_templates_info(self):
        """测试列出所有模板信息"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        self.registry.register_template(self.mock_template2)
        
        # 列出模板信息
        infos = self.registry.list_templates_info()
        
        # 验证结果
        self.assertEqual(len(infos), 2)
        
        # 验证信息结构
        for info in infos:
            self.assertIn("name", info)
            self.assertIn("description", info)
            self.assertIn("parameters", info)
            self.assertIn("metadata", info)
    
    def test_validate_template_config(self):
        """测试验证模板配置"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        
        # 验证有效配置
        config = {"param1": "value"}
        errors = self.registry.validate_template_config("test_template1", config)
        self.assertEqual(errors, [])
        
        # 验证无效配置
        self.mock_template1.validate_parameters.return_value = ["error1", "error2"]
        errors = self.registry.validate_template_config("test_template1", config)
        self.assertEqual(errors, ["error1", "error2"])
        
        # 验证不存在的模板
        errors = self.registry.validate_template_config("nonexistent", config)
        self.assertEqual(len(errors), 1)
        self.assertIn("不存在", errors[0])
    
    def test_create_workflow_config(self):
        """测试使用模板创建工作流配置"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        
        # 创建配置
        config = {"param1": "value"}
        result = self.registry.create_workflow_config("test_template1", config)
        
        # 验证结果
        self.assertEqual(result, self.mock_template1.create_template.return_value)
        
        # 验证调用
        self.mock_template1.validate_parameters.assert_called_once_with(config)
        self.mock_template1.create_template.assert_called_once_with(config)
    
    def test_create_workflow_config_validation_error(self):
        """测试创建工作流配置（验证失败）"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        
        # 设置验证失败
        self.mock_template1.validate_parameters.return_value = ["error1"]
        
        # 创建配置应该抛出异常
        config = {"param1": "value"}
        with self.assertRaises(ValueError) as context:
            self.registry.create_workflow_config("test_template1", config)
        
        self.assertIn("参数验证失败", str(context.exception))
        self.assertIn("error1", str(context.exception))
    
    def test_create_workflow_config_template_not_found(self):
        """测试创建工作流配置（模板不存在）"""
        # 创建配置应该抛出异常
        config = {"param1": "value"}
        with self.assertRaises(ValueError) as context:
            self.registry.create_workflow_config("nonexistent", config)
        
        self.assertIn("模板不存在", str(context.exception))
    
    def test_search_templates(self):
        """测试搜索模板"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        self.registry.register_template(self.mock_template2)
        
        # 按名称搜索
        results = self.registry.search_templates("template1")
        self.assertEqual(results, ["test_template1"])
        
        # 按描述搜索
        results = self.registry.search_templates("Test template 2")
        self.assertEqual(results, ["test_template2"])
        
        # 按参数描述搜索
        results = self.registry.search_templates("Parameter 1")
        self.assertEqual(results, ["test_template1"])
        
        # 搜索不匹配的内容
        results = self.registry.search_templates("nonexistent")
        self.assertEqual(results, [])
    
    def test_get_templates_by_category(self):
        """测试根据类别获取模板"""
        # 创建不同类别的模板
        react_template = Mock(spec=IWorkflowTemplate)
        react_template.name = "react_workflow"
        react_template.description = "ReAct workflow template"
        
        plan_template = Mock(spec=IWorkflowTemplate)
        plan_template.name = "plan_execute"
        plan_template.description = "Plan execute workflow"
        
        collaborative_template = Mock(spec=IWorkflowTemplate)
        collaborative_template.name = "collaborative_agent"
        collaborative_template.description = "Collaborative agent workflow"
        
        # 注册模板
        self.registry.register_template(react_template)
        self.registry.register_template(plan_template)
        self.registry.register_template(collaborative_template)
        
        # 按类别获取
        react_templates = self.registry.get_templates_by_category("react")
        self.assertIn("react_workflow", react_templates)
        
        plan_templates = self.registry.get_templates_by_category("plan")
        self.assertIn("plan_execute", plan_templates)
        
        collaborative_templates = self.registry.get_templates_by_category("collaborative")
        self.assertIn("collaborative_agent", collaborative_templates)
    
    @patch('src.application.workflow.templates.registry.logger')
    def test_clear(self, mock_logger):
        """测试清除所有模板"""
        # 注册模板
        self.registry.register_template(self.mock_template1)
        self.registry.register_template(self.mock_template2)
        
        # 清除模板
        self.registry.clear()
        
        # 验证结果
        self.assertEqual(len(self.registry._templates), 0)
        self.assertEqual(len(self.registry._template_metadata), 0)
        
        # 验证日志
        mock_logger.info.assert_called_with("清除所有模板")
    
    def test_get_statistics(self):
        """测试获取注册表统计信息"""
        # 创建不同类别的模板
        react_template1 = Mock(spec=IWorkflowTemplate)
        react_template1.name = "react_template1"
        
        react_template2 = Mock(spec=IWorkflowTemplate)
        react_template2.name = "react_template2"
        
        plan_template = Mock(spec=IWorkflowTemplate)
        plan_template.name = "plan_template"
        
        other_template = Mock(spec=IWorkflowTemplate)
        other_template.name = "other_template"
        
        # 注册模板
        self.registry.register_template(react_template1)
        self.registry.register_template(react_template2)
        self.registry.register_template(plan_template)
        self.registry.register_template(other_template)
        
        # 获取统计信息
        stats = self.registry.get_statistics()
        
        # 验证统计信息
        self.assertEqual(stats["total_templates"], 4)
        self.assertEqual(stats["categories"]["react"], 2)
        self.assertEqual(stats["categories"]["plan_execute"], 1)
        self.assertEqual(stats["categories"]["other"], 1)
        self.assertIn("react_template1", stats["template_names"])
        self.assertIn("react_template2", stats["template_names"])
        self.assertIn("plan_template", stats["template_names"])
        self.assertIn("other_template", stats["template_names"])


class TestGlobalRegistryFunctions(unittest.TestCase):
    """测试全局注册表函数"""
    
    @patch('src.application.workflow.templates.registry.WorkflowTemplateRegistry')
    @patch('src.application.workflow.templates.registry._register_builtin_templates')
    def test_get_global_template_registry(self, mock_register_builtin, mock_registry_class):
        """测试获取全局模板注册表"""
        # 设置模拟
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        
        # 第一次获取
        registry1 = get_global_template_registry()
        
        # 验证创建
        mock_registry_class.assert_called_once()
        mock_register_builtin.assert_called_once_with(mock_registry)
        
        # 第二次获取应该返回同一个实例
        registry2 = get_global_template_registry()
        self.assertEqual(registry1, registry2)
        mock_registry_class.assert_called_once()  # 仍然只调用一次
    
    @patch('src.application.workflow.templates.registry.get_global_template_registry')
    def test_register_template(self, mock_get_global):
        """测试注册模板到全局注册表"""
        # 设置模拟
        mock_registry = Mock()
        mock_get_global.return_value = mock_registry
        
        mock_template = Mock(spec=IWorkflowTemplate)
        
        # 注册模板
        register_template(mock_template)
        
        # 验证调用
        mock_registry.register_template.assert_called_once_with(mock_template)
    
    @patch('src.application.workflow.templates.registry.get_global_template_registry')
    def test_get_template(self, mock_get_global):
        """测试从全局注册表获取模板"""
        # 设置模拟
        mock_registry = Mock()
        mock_template = Mock(spec=IWorkflowTemplate)
        mock_registry.get_template.return_value = mock_template
        mock_get_global.return_value = mock_registry
        
        # 获取模板
        result = get_template("test_template")
        
        # 验证结果
        self.assertEqual(result, mock_template)
        
        # 验证调用
        mock_registry.get_template.assert_called_once_with("test_template")
    
    @patch('src.application.workflow.templates.registry.get_global_template_registry')
    def test_list_templates(self, mock_get_global):
        """测试列出全局注册表中的所有模板"""
        # 设置模拟
        mock_registry = Mock()
        mock_registry.list_templates.return_value = ["template1", "template2"]
        mock_get_global.return_value = mock_registry
        
        # 列出模板
        result = list_templates()
        
        # 验证结果
        self.assertEqual(result, ["template1", "template2"])
        
        # 验证调用
        mock_registry.list_templates.assert_called_once()
    
    @patch('src.application.workflow.templates.registry.get_global_template_registry')
    def test_create_workflow_from_template(self, mock_get_global):
        """测试使用模板创建工作流配置"""
        # 设置模拟
        mock_registry = Mock()
        mock_config = Mock(spec=WorkflowConfig)
        mock_registry.create_workflow_config.return_value = mock_config
        mock_get_global.return_value = mock_registry
        
        config = {"param1": "value"}
        
        # 创建工作流配置
        result = create_workflow_from_template("test_template", config)
        
        # 验证结果
        self.assertEqual(result, mock_config)
        
        # 验证调用
        mock_registry.create_workflow_config.assert_called_once_with("test_template", config)


class TestRegisterBuiltinTemplates(unittest.TestCase):
    """测试注册内置模板"""
    
    @patch('src.application.workflow.templates.registry.logger')
    def test_register_builtin_templates_success(self, mock_logger):
        """测试成功注册内置模板"""
        # 创建模拟注册表
        mock_registry = Mock()
        
        # 创建模拟模板类
        mock_react_template = Mock()
        mock_enhanced_react_template = Mock()
        mock_plan_execute_template = Mock()
        mock_collaborative_template = Mock()
        
        # 模拟导入
        mock_react_module = Mock()
        mock_react_module.ReActWorkflowTemplate = Mock(return_value=mock_react_template)
        mock_react_module.EnhancedReActTemplate = Mock(return_value=mock_enhanced_react_template)
        
        mock_plan_module = Mock()
        mock_plan_module.PlanExecuteWorkflowTemplate = Mock(return_value=mock_plan_execute_template)
        mock_plan_module.CollaborativePlanExecuteTemplate = Mock(return_value=mock_collaborative_template)
        
        with patch.dict('sys.modules', {
            'src.application.workflow.templates.react_template': mock_react_module,
            'src.application.workflow.templates.plan_execute_template': mock_plan_module
        }):
            # 注册内置模板
            _register_builtin_templates(mock_registry)
        
        # 验证注册调用
        self.assertEqual(mock_registry.register_template.call_count, 4)
        mock_registry.register_template.assert_any_call(mock_react_template)
        mock_registry.register_template.assert_any_call(mock_enhanced_react_template)
        mock_registry.register_template.assert_any_call(mock_plan_execute_template)
        mock_registry.register_template.assert_any_call(mock_collaborative_template)
        
        # 验证日志
        mock_logger.info.assert_called_with("内置模板注册完成")
    
    @patch('src.application.workflow.templates.registry.logger')
    def test_register_builtin_templates_import_error(self, mock_logger):
        """测试注册内置模板时导入错误"""
        # 创建模拟注册表
        mock_registry = Mock()
        
        # 模拟导入错误
        with patch.dict('sys.modules', {}, clear=True):
            # 注册内置模板
            _register_builtin_templates(mock_registry)
        
        # 验证错误日志
        mock_logger.error.assert_called()
        error_args = [call.args[0] for call in mock_logger.error.call_args_list]
        self.assertTrue(any("注册内置模板失败" in arg for arg in error_args))


if __name__ == '__main__':
    unittest.main()