"""工作流注册表测试

测试WorkflowRegistry的功能。
"""

import unittest
from unittest.mock import Mock
from datetime import datetime

from src.domain.workflow.registry import WorkflowRegistry, WorkflowDefinition


class TestWorkflowRegistry(unittest.TestCase):
    """测试工作流注册表"""
    
    def setUp(self):
        """设置测试环境"""
        self.registry = WorkflowRegistry()
        
        # 创建测试工作流定义
        self.test_workflow_def = {
            "name": "test_workflow",
            "description": "Test workflow",
            "version": "1.0.0",
            "config_id": "config_123",
            "config_path": "test_config.yaml"
        }
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(len(self.registry._workflows), 0)
        self.assertEqual(len(self.registry._name_index), 0)
        self.assertEqual(len(self.registry._tag_index), 0)
    
    def test_register_workflow(self):
        """测试注册工作流"""
        # 注册工作流
        workflow_id = self.registry.register_workflow(self.test_workflow_def)
        
        # 验证结果
        self.assertIsNotNone(workflow_id)
        self.assertIn(workflow_id, self.registry._workflows)
        self.assertIn("test_workflow", self.registry._name_index)
        self.assertEqual(self.registry._name_index["test_workflow"], workflow_id)
        
        # 验证工作流定义
        definition = self.registry._workflows[workflow_id]
        self.assertEqual(definition.name, "test_workflow")
        self.assertEqual(definition.description, "Test workflow")
        self.assertEqual(definition.version, "1.0.0")
        self.assertEqual(definition.config_id, "config_123")
        self.assertEqual(definition.config_path, "test_config.yaml")
    
    def test_register_workflow_with_id(self):
        """测试使用指定ID注册工作流"""
        # 注册工作流
        workflow_def = self.test_workflow_def.copy()
        workflow_def["workflow_id"] = "custom_id"
        workflow_id = self.registry.register_workflow(workflow_def)
        
        # 验证结果
        self.assertEqual(workflow_id, "custom_id")
        self.assertIn("custom_id", self.registry._workflows)
    
    def test_register_workflow_missing_fields(self):
        """测试注册缺少必要字段的工作流"""
        # 创建不完整的工作流定义
        incomplete_def = {
            "name": "test_workflow",
            "description": "Test workflow"
            # 缺少version, config_id, config_path
        }
        
        # 执行测试并验证异常
        with self.assertRaises(ValueError) as context:
            self.registry.register_workflow(incomplete_def)
        
        self.assertIn("缺少必要字段", str(context.exception))
    
    def test_get_workflow_definition(self):
        """测试获取工作流定义"""
        # 先注册工作流
        workflow_id = self.registry.register_workflow(self.test_workflow_def)
        
        # 获取工作流定义
        definition = self.registry.get_workflow_definition(workflow_id)
        
        # 验证结果
        self.assertIsNotNone(definition)
        self.assertEqual(definition["workflow_id"], workflow_id)
        self.assertEqual(definition["name"], "test_workflow")
        self.assertEqual(definition["description"], "Test workflow")
        self.assertEqual(definition["version"], "1.0.0")
        self.assertEqual(definition["config_id"], "config_123")
        self.assertEqual(definition["config_path"], "test_config.yaml")
        self.assertIn("created_at", definition)
        self.assertIn("updated_at", definition)
        
        # 获取不存在的工作流定义
        definition = self.registry.get_workflow_definition("nonexistent")
        self.assertIsNone(definition)
    
    def test_list_available_workflows(self):
        """测试列出可用工作流"""
        # 初始状态应该为空
        self.assertEqual(self.registry.list_available_workflows(), [])
        
        # 注册工作流
        workflow_id = self.registry.register_workflow(self.test_workflow_def)
        
        # 列出工作流
        workflows = self.registry.list_available_workflows()
        
        # 验证结果
        self.assertEqual(len(workflows), 1)
        self.assertEqual(workflows[0]["workflow_id"], workflow_id)
        self.assertEqual(workflows[0]["name"], "test_workflow")
        self.assertEqual(workflows[0]["description"], "Test workflow")
        self.assertEqual(workflows[0]["version"], "1.0.0")
        self.assertIn("tags", workflows[0])
        self.assertIn("created_at", workflows[0])
        self.assertIn("updated_at", workflows[0])
    
    def test_find_by_name(self):
        """测试根据名称查找工作流"""
        # 先注册工作流
        workflow_id = self.registry.register_workflow(self.test_workflow_def)
        
        # 根据名称查找
        found_id = self.registry.find_by_name("test_workflow")
        
        # 验证结果
        self.assertEqual(found_id, workflow_id)
        
        # 查找不存在的工作流
        found_id = self.registry.find_by_name("nonexistent")
        self.assertIsNone(found_id)
    
    def test_find_by_tag(self):
        """测试根据标签查找工作流"""
        # 注册带标签的工作流
        workflow_def = self.test_workflow_def.copy()
        workflow_def["metadata"] = {"tags": ["test", "example"]}
        workflow_id = self.registry.register_workflow(workflow_def)
        
        # 根据标签查找
        workflow_ids = self.registry.find_by_tag("test")
        
        # 验证结果
        self.assertEqual(len(workflow_ids), 1)
        self.assertEqual(workflow_ids[0], workflow_id)
        
        # 查找不存在的标签
        workflow_ids = self.registry.find_by_tag("nonexistent")
        self.assertEqual(workflow_ids, [])
    
    def test_update_workflow(self):
        """测试更新工作流"""
        # 先注册工作流
        workflow_id = self.registry.register_workflow(self.test_workflow_def)
        
        # 更新工作流
        updates = {
            "description": "Updated test workflow",
            "version": "2.0.0",
            "metadata": {"tags": ["updated", "test"]}
        }
        result = self.registry.update_workflow(workflow_id, updates)
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证更新
        definition = self.registry.get_workflow_definition(workflow_id)
        self.assertEqual(definition["description"], "Updated test workflow")
        self.assertEqual(definition["version"], "2.0.0")
        self.assertEqual(definition["metadata"]["tags"], ["updated", "test"])
    
    def test_update_workflow_name(self):
        """测试更新工作流名称"""
        # 先注册工作流
        workflow_id = self.registry.register_workflow(self.test_workflow_def)
        
        # 更新工作流名称
        updates = {"name": "updated_workflow"}
        result = self.registry.update_workflow(workflow_id, updates)
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证名称索引更新
        self.assertNotIn("test_workflow", self.registry._name_index)
        self.assertIn("updated_workflow", self.registry._name_index)
        self.assertEqual(self.registry._name_index["updated_workflow"], workflow_id)
    
    def test_update_workflow_not_exists(self):
        """测试更新不存在的工作流"""
        # 更新不存在的工作流
        updates = {"description": "Updated description"}
        result = self.registry.update_workflow("nonexistent", updates)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_unregister_workflow(self):
        """测试注销工作流"""
        # 先注册工作流
        workflow_id = self.registry.register_workflow(self.test_workflow_def)
        
        # 注销工作流
        result = self.registry.unregister_workflow(workflow_id)
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn(workflow_id, self.registry._workflows)
        self.assertNotIn("test_workflow", self.registry._name_index)
    
    def test_unregister_workflow_not_exists(self):
        """测试注销不存在的工作流"""
        # 注销不存在的工作流
        result = self.registry.unregister_workflow("nonexistent")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 注册多个工作流
        workflow_def1 = self.test_workflow_def.copy()
        workflow_def1["name"] = "workflow1"
        workflow_def1["metadata"] = {"tags": ["tag1", "common"]}
        
        workflow_def2 = self.test_workflow_def.copy()
        workflow_def2["name"] = "workflow2"
        workflow_def2["metadata"] = {"tags": ["tag2", "common"]}
        
        self.registry.register_workflow(workflow_def1)
        self.registry.register_workflow(workflow_def2)
        
        # 获取统计信息
        stats = self.registry.get_statistics()
        
        # 验证结果
        self.assertEqual(stats["total_workflows"], 2)
        self.assertEqual(stats["total_tags"], 3)  # tag1, tag2, common
        self.assertIn("tag_distribution", stats)
        self.assertIn("recent_workflows", stats)
        self.assertEqual(len(stats["recent_workflows"]), 2)
    
    def test_generate_workflow_id(self):
        """测试生成工作流ID"""
        workflow_id = self.registry._generate_workflow_id("test_workflow")
        
        # 验证ID格式
        self.assertTrue(workflow_id.startswith("test_workflow_"))
        self.assertIn("_", workflow_id)
        self.assertGreater(len(workflow_id), len("test_workflow_"))


if __name__ == '__main__':
    unittest.main()