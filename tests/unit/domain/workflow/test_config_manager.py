"""工作流配置管理器测试

测试WorkflowConfigManager的功能。
"""

import unittest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime

from src.domain.workflow.config_manager import WorkflowConfigManager
from src.infrastructure.graph.config import WorkflowConfig
from infrastructure.config.loader.yaml_loader import IConfigLoader


class TestWorkflowConfigManager(unittest.TestCase):
    """测试工作流配置管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_config_loader = Mock(spec=IConfigLoader)
        # 添加load_workflow_config方法到mock
        self.mock_config_loader.load_workflow_config = Mock()
        self.manager = WorkflowConfigManager(config_loader=self.mock_config_loader)
        
        # 创建模拟的工作流配置
        self.mock_workflow_config = Mock(spec=WorkflowConfig)
        self.mock_workflow_config.name = "test_workflow"
        self.mock_workflow_config.description = "Test workflow"
        self.mock_workflow_config.version = "1.0.0"
        self.mock_workflow_config.nodes = {"node1": Mock()}
        # 创建有效的边配置
        mock_edge = Mock()
        mock_edge.from_node = "node1"
        mock_edge.to_node = "node1"
        self.mock_workflow_config.edges = [mock_edge]
        self.mock_workflow_config.entry_point = "node1"
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.manager.config_loader, self.mock_config_loader)
        self.assertEqual(len(self.manager._configs), 0)
        self.assertEqual(len(self.manager._config_metadata), 0)
    
    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        manager = WorkflowConfigManager()
        self.assertIsNone(manager.config_loader)
    
    @patch('pathlib.Path.exists')
    def test_load_config(self, mock_path_exists):
        """测试加载配置"""
        # 设置文件存在
        mock_path_exists.return_value = True
        
        # 设置模拟
        self.mock_config_loader.load_workflow_config.return_value = self.mock_workflow_config
        
        # 执行测试
        config_id = self.manager.load_config("test_config.yaml")
        
        # 验证结果
        self.assertIsNotNone(config_id)
        self.assertIn(config_id, self.manager._configs)
        self.assertIn(config_id, self.manager._config_metadata)
        
        # 验证调用
        self.mock_config_loader.load_workflow_config.assert_called_once_with("test_config.yaml")
        
        # 验证元数据
        metadata = self.manager._config_metadata[config_id]
        self.assertEqual(metadata["config_id"], config_id)
        self.assertEqual(metadata["name"], "test_workflow")
        self.assertEqual(metadata["description"], "Test workflow")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertEqual(metadata["config_path"], "test_config.yaml")
        self.assertIsNotNone(metadata["loaded_at"])
        self.assertIsNotNone(metadata["checksum"])
    
    @patch('pathlib.Path.exists')
    def test_load_config_file_not_exists(self, mock_path_exists):
        """测试加载不存在的配置文件"""
        # 设置文件不存在
        mock_path_exists.return_value = False
        
        # 执行测试并验证异常
        with self.assertRaises(RuntimeError) as context:
            self.manager.load_config("nonexistent_config.yaml")
        
        self.assertIn("配置文件不存在", str(context.exception))
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b"test content")
    def test_get_config(self, mock_file, mock_path_exists):
        """测试获取配置"""
        # 设置文件存在
        mock_path_exists.return_value = True
        
        # 先加载配置
        self.mock_config_loader.load_workflow_config.return_value = self.mock_workflow_config
        config_id = self.manager.load_config("test_config.yaml")
        
        # 获取配置
        config = self.manager.get_config(config_id)
        
        # 验证结果
        self.assertEqual(config, self.mock_workflow_config)
        
        # 获取不存在的配置
        config = self.manager.get_config("nonexistent")
        self.assertIsNone(config)
    
    def test_validate_config_valid(self):
        """测试验证有效配置"""
        # 验证配置
        result = self.manager.validate_config(self.mock_workflow_config)
        
        # 验证结果
        self.assertTrue(result)
    
    def test_validate_config_missing_name(self):
        """测试验证缺少名称的配置"""
        # 设置无效配置
        self.mock_workflow_config.name = ""
        
        # 验证配置
        result = self.manager.validate_config(self.mock_workflow_config)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_validate_config_no_nodes(self):
        """测试验证没有节点的配置"""
        # 设置无效配置
        self.mock_workflow_config.nodes = {}
        
        # 验证配置
        result = self.manager.validate_config(self.mock_workflow_config)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_validate_config_no_entry_point(self):
        """测试验证没有入口点的配置"""
        # 设置无效配置
        self.mock_workflow_config.entry_point = ""
        
        # 验证配置
        result = self.manager.validate_config(self.mock_workflow_config)
        
        # 验证结果
        self.assertFalse(result)
    
    @patch('pathlib.Path.exists')
    def test_get_config_metadata(self, mock_path_exists):
        """测试获取配置元数据"""
        # 设置文件存在
        mock_path_exists.return_value = True
        
        # 先加载配置
        self.mock_config_loader.load_workflow_config.return_value = self.mock_workflow_config
        config_id = self.manager.load_config("test_config.yaml")
        
        # 获取元数据
        metadata = self.manager.get_config_metadata(config_id)
        
        # 验证结果
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["name"], "test_workflow")
        
        # 获取不存在的元数据
        metadata = self.manager.get_config_metadata("nonexistent")
        self.assertIsNone(metadata)
    
    @patch('pathlib.Path.exists')
    def test_list_configs(self, mock_path_exists):
        """测试列出配置"""
        # 设置文件存在
        mock_path_exists.return_value = True
        
        # 初始状态应该为空
        self.assertEqual(self.manager.list_configs(), [])
        
        # 加载配置
        self.mock_config_loader.load_workflow_config.return_value = self.mock_workflow_config
        config_id1 = self.manager.load_config("test_config1.yaml")
        config_id2 = self.manager.load_config("test_config2.yaml")
        
        # 列出配置
        configs = self.manager.list_configs()
        
        # 验证结果
        self.assertEqual(len(configs), 2)
        self.assertIn(config_id1, configs)
        self.assertIn(config_id2, configs)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b"test content")
    def test_reload_config(self, mock_file, mock_path_exists):
        """测试重新加载配置"""
        # 设置文件存在
        mock_path_exists.return_value = True
        
        # 先加载配置
        self.mock_config_loader.load_workflow_config.return_value = self.mock_workflow_config
        config_id = self.manager.load_config("test_config.yaml")
        
        # 重新加载配置
        result = self.manager.reload_config(config_id)
        
        # 验证结果
        self.assertTrue(result)
        
        # 重新加载不存在的配置
        result = self.manager.reload_config("nonexistent")
        self.assertFalse(result)
    
    @patch('pathlib.Path.exists')
    def test_reload_config_file_not_exists(self, mock_path_exists):
        """测试重新加载不存在的配置文件"""
        # 设置文件存在
        mock_path_exists.return_value = True
        
        # 先加载配置
        self.mock_config_loader.load_workflow_config.return_value = self.mock_workflow_config
        config_id = self.manager.load_config("test_config.yaml")
        
        # 设置文件不存在
        mock_path_exists.return_value = False
        
        # 重新加载配置
        result = self.manager.reload_config(config_id)
        
        # 验证结果
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()