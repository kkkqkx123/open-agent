"""工作流管理器测试

测试工作流管理器的功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
from datetime import datetime
import uuid

from src.application.workflow.manager import WorkflowManager
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import WorkflowState, StateFactory
from src.infrastructure.graph.registry import NodeRegistry
from src.infrastructure.config_loader import IConfigLoader
from src.application.workflow.interfaces import IEventCollector


class TestWorkflowManager(unittest.TestCase):
    """测试工作流管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_config_loader = Mock(spec=IConfigLoader)
        self.mock_node_registry = Mock(spec=NodeRegistry)
        self.mock_workflow_builder = Mock()
        
        self.manager = WorkflowManager(
            config_loader=self.mock_config_loader,
            node_registry=self.mock_node_registry,
            workflow_builder=self.mock_workflow_builder
        )
        
        # 创建模拟的工作流配置
        self.mock_workflow_config = Mock(spec=WorkflowConfig)
        self.mock_workflow_config.name = "test_workflow"
        self.mock_workflow_config.description = "Test workflow"
        self.mock_workflow_config.version = "1.0.0"
        self.mock_workflow_config.additional_config = {"max_iterations": 10}
        self.mock_workflow_config.nodes = {"node1": Mock()}
        self.mock_workflow_config.edges = [Mock()]
        self.mock_workflow_config.entry_point = "node1"
        self.mock_workflow_config.to_dict.return_value = {"name": "test_workflow"}
        
        # 创建模拟的工作流实例
        self.mock_workflow = Mock()
        self.mock_workflow.invoke.return_value = Mock(spec=WorkflowState)
        self.mock_workflow.ainvoke = Mock()
        self.mock_workflow.stream.return_value = [Mock(spec=WorkflowState)]
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.manager.config_loader, self.mock_config_loader)
        self.assertEqual(self.manager.node_registry, self.mock_node_registry)
        self.assertEqual(self.manager.workflow_builder, self.mock_workflow_builder)
        self.assertEqual(len(self.manager._workflows), 0)
        self.assertEqual(len(self.manager._workflow_configs), 0)
        self.assertEqual(len(self.manager._workflow_metadata), 0)
    
    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        manager = WorkflowManager()
        self.assertIsNone(manager.config_loader)
        self.assertIsNotNone(manager.node_registry)
        self.assertIsNotNone(manager.workflow_builder)
    
    def test_load_workflow(self):
        """测试加载工作流"""
        # 设置模拟
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        
        # 执行测试
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 验证结果
        self.assertIsNotNone(workflow_id)
        self.assertIn(workflow_id, self.manager._workflows)
        self.assertIn(workflow_id, self.manager._workflow_configs)
        self.assertIn(workflow_id, self.manager._workflow_metadata)
        
        # 验证调用
        self.mock_workflow_builder.load_workflow_config.assert_called_once_with("test_config.yaml")
        self.mock_workflow_builder.build_graph.assert_called_once_with(self.mock_workflow_config)
        
        # 验证元数据
        metadata = self.manager._workflow_metadata[workflow_id]
        self.assertEqual(metadata["name"], "test_workflow")
        self.assertEqual(metadata["description"], "Test workflow")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertEqual(metadata["config_path"], "test_config.yaml")
        self.assertIsNotNone(metadata["loaded_at"])
        self.assertIsNone(metadata["last_used"])
        self.assertEqual(metadata["usage_count"], 0)
    
    def test_create_workflow(self):
        """测试创建工作流实例"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 重置使用计数
        self.manager._workflow_metadata[workflow_id]["usage_count"] = 0
        
        # 创建工作流实例
        workflow = self.manager.create_workflow(workflow_id)
        
        # 验证结果
        self.assertEqual(workflow, self.mock_workflow)
        
        # 验证使用统计更新
        metadata = self.manager._workflow_metadata[workflow_id]
        self.assertIsNotNone(metadata["last_used"])
        self.assertEqual(metadata["usage_count"], 1)
    
    def test_create_workflow_not_found(self):
        """测试创建不存在的工作流"""
        with self.assertRaises(ValueError) as context:
            self.manager.create_workflow("nonexistent_workflow")
        
        self.assertIn("不存在", str(context.exception))
    
    def test_run_workflow(self):
        """测试运行工作流"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 创建模拟的事件收集器
        mock_event_collector = Mock(spec=IEventCollector)
        
        # 运行工作流
        result = self.manager.run_workflow(workflow_id, event_collector=mock_event_collector)
        
        # 验证结果
        self.assertIsNotNone(result)
        
        # 验证调用
        self.mock_workflow.invoke.assert_called_once()
        mock_event_collector.collect_workflow_start.assert_called_once()
        mock_event_collector.collect_workflow_end.assert_called_once()
    
    def test_run_workflow_with_initial_state(self):
        """测试使用初始状态运行工作流"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 创建初始状态
        initial_state = Mock(spec=WorkflowState)
        # 为initial_state添加字典接口支持
        type(initial_state).__setitem__ = Mock()
        type(initial_state).__getitem__ = Mock()
        
        # 运行工作流
        result = self.manager.run_workflow(workflow_id, initial_state=initial_state)
        
        # 验证结果
        self.assertIsNotNone(result)
        
        # 验证调用
        self.mock_workflow.invoke.assert_called_once()
        args, kwargs = self.mock_workflow.invoke.call_args
        self.assertEqual(args[0], initial_state)
    
    def test_run_workflow_error(self):
        """测试运行工作流时出错"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 设置工作流抛出异常
        test_error = Exception("Test error")
        self.mock_workflow.invoke.side_effect = test_error
        
        # 创建模拟的事件收集器
        mock_event_collector = Mock(spec=IEventCollector)
        
        # 运行工作流应该抛出异常
        with self.assertRaises(Exception) as context:
            self.manager.run_workflow(workflow_id, event_collector=mock_event_collector)
        
        self.assertEqual(str(context.exception), "Test error")
        
        # 验证错误收集
        mock_event_collector.collect_error.assert_called_once()
        
        # 验证错误记录
        metadata = self.manager._workflow_metadata[workflow_id]
        self.assertIn("errors", metadata)
        self.assertEqual(len(metadata["errors"]), 1)
        self.assertEqual(metadata["errors"][0]["error_type"], "Exception")
        self.assertEqual(metadata["errors"][0]["error_message"], "Test error")
    
    def test_run_workflow_async(self):
        """测试异步运行工作流"""
        import asyncio
        from unittest.mock import AsyncMock
        
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 设置异步返回值
        async_result = Mock(spec=WorkflowState)
        self.mock_workflow.ainvoke = AsyncMock(return_value=async_result)
        
        # 运行异步工作流
        async def run_test():
            return await self.manager.run_workflow_async(workflow_id)
        
        result = asyncio.run(run_test())
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result, async_result)
    
    def test_stream_workflow(self):
        """测试流式运行工作流"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 流式运行工作流
        results = list(self.manager.stream_workflow(workflow_id))
        
        # 验证结果
        self.assertEqual(len(results), 1)
        
        # 验证调用
        self.mock_workflow.stream.assert_called_once()
    
    def test_stream_workflow_without_stream_support(self):
        """测试工作流不支持流式运行"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 移除stream方法
        del self.mock_workflow.stream
        
        # 流式运行工作流
        results = list(self.manager.stream_workflow(workflow_id))
        
        # 验证结果
        self.assertEqual(len(results), 1)
        
        # 验证调用
        self.mock_workflow.invoke.assert_called_once()
    
    def test_list_workflows(self):
        """测试列出工作流"""
        # 初始状态应该为空
        self.assertEqual(self.manager.list_workflows(), [])
        
        # 加载工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id1 = self.manager.load_workflow("test_config1.yaml")
        workflow_id2 = self.manager.load_workflow("test_config2.yaml")
        
        # 列出工作流
        workflows = self.manager.list_workflows()
        
        # 验证结果
        self.assertEqual(len(workflows), 2)
        self.assertIn(workflow_id1, workflows)
        self.assertIn(workflow_id2, workflows)
    
    def test_get_workflow_config(self):
        """测试获取工作流配置"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 获取配置
        config = self.manager.get_workflow_config(workflow_id)
        
        # 验证结果
        self.assertEqual(config, self.mock_workflow_config)
        
        # 获取不存在的配置
        config = self.manager.get_workflow_config("nonexistent")
        self.assertIsNone(config)
    
    def test_unload_workflow(self):
        """测试卸载工作流"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 卸载工作流
        result = self.manager.unload_workflow(workflow_id)
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn(workflow_id, self.manager._workflows)
        self.assertNotIn(workflow_id, self.manager._workflow_configs)
        self.assertNotIn(workflow_id, self.manager._workflow_metadata)
        
        # 卸载不存在的工作流
        result = self.manager.unload_workflow("nonexistent")
        self.assertFalse(result)
    
    def test_get_workflow_visualization(self):
        """测试获取工作流可视化数据"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 获取可视化数据
        viz_data = self.manager.get_workflow_visualization(workflow_id)
        
        # 验证结果
        self.assertEqual(viz_data["workflow_id"], workflow_id)
        self.assertEqual(viz_data["name"], "test_workflow")
        self.assertEqual(viz_data["description"], "Test workflow")
        self.assertEqual(viz_data["version"], "1.0.0")
        self.assertIn("nodes", viz_data)
        self.assertIn("edges", viz_data)
        self.assertEqual(viz_data["entry_point"], "node1")
        
        # 获取不存在的工作流可视化
        viz_data = self.manager.get_workflow_visualization("nonexistent")
        self.assertEqual(viz_data, {})
    
    def test_get_workflow_summary(self):
        """测试获取工作流摘要"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 获取摘要
        summary = self.manager.get_workflow_summary(workflow_id)
        
        # 验证结果
        self.assertEqual(summary["workflow_id"], workflow_id)
        self.assertEqual(summary["name"], "test_workflow")
        self.assertEqual(summary["version"], "1.0.0")
        self.assertEqual(summary["description"], "Test workflow")
        self.assertEqual(summary["config_path"], "test_config.yaml")
        self.assertIn("checksum", summary)
        self.assertIn("loaded_at", summary)
        self.assertIn("last_used", summary)
        self.assertEqual(summary["usage_count"], 0)
        
        # 获取不存在的工作流摘要
        summary = self.manager.get_workflow_summary("nonexistent")
        self.assertEqual(summary, {})
    
    @patch('builtins.open', new_callable=mock_open, read_data=b"test content")
    @patch('pathlib.Path.exists')
    def test_get_workflow_summary_with_checksum(self, mock_exists, mock_file):
        """测试获取工作流摘要（包含校验和）"""
        # 设置文件存在
        mock_exists.return_value = True
        
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 获取摘要
        summary = self.manager.get_workflow_summary(workflow_id)
        
        # 验证校验和
        self.assertNotEqual(summary["checksum"], "")
        # 使用实际计算的MD5值而不是硬编码的值
        import hashlib
        expected_checksum = hashlib.md5(b"test content").hexdigest()
        self.assertEqual(summary["checksum"], expected_checksum)
    
    def test_get_workflow_metadata(self):
        """测试获取工作流元数据"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 获取元数据
        metadata = self.manager.get_workflow_metadata(workflow_id)
        
        # 验证结果
        self.assertIsNotNone(metadata)
        if metadata is not None:
            self.assertEqual(metadata["name"], "test_workflow")
        
        # 获取不存在的元数据
        metadata = self.manager.get_workflow_metadata("nonexistent")
        self.assertIsNone(metadata)
    
    @patch('pathlib.Path.exists')
    def test_reload_workflow(self, mock_path_exists):
        """测试重新加载工作流"""
        # 设置文件存在
        mock_path_exists.return_value = True
        
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 创建新的配置
        new_config = Mock(spec=WorkflowConfig)
        new_config.name = "test_workflow"
        new_config.version = "2.0.0"
        new_workflow = Mock()
        
        self.mock_workflow_builder.load_workflow_config.return_value = new_config
        self.mock_workflow_builder.build_graph.return_value = new_workflow
        
        # 重新加载工作流
        result = self.manager.reload_workflow(workflow_id)
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.manager._workflows[workflow_id], new_workflow)
        self.assertEqual(self.manager._workflow_configs[workflow_id], new_config)
        
        # 验证元数据更新
        metadata = self.manager._workflow_metadata[workflow_id]
        self.assertEqual(metadata["version"], "2.0.0")
        
        # 重新加载不存在的工作流
        result = self.manager.reload_workflow("nonexistent")
        self.assertFalse(result)
    
    def test_generate_workflow_id(self):
        """测试生成工作流ID"""
        workflow_id = self.manager._generate_workflow_id("test_workflow")
        
        # 验证ID格式
        self.assertTrue(workflow_id.startswith("test_workflow_"))
        self.assertIn("_", workflow_id)
        self.assertGreater(len(workflow_id), len("test_workflow_"))
    
    def test_log_workflow_error(self):
        """测试记录工作流错误"""
        # 先加载一个工作流
        self.mock_workflow_builder.load_workflow_config.return_value = self.mock_workflow_config
        self.mock_workflow_builder.build_graph.return_value = self.mock_workflow
        workflow_id = self.manager.load_workflow("test_config.yaml")
        
        # 记录错误
        test_error = Exception("Test error")
        self.manager._log_workflow_error(workflow_id, test_error)
        
        # 验证错误记录
        metadata = self.manager._workflow_metadata[workflow_id]
        self.assertIn("errors", metadata)
        self.assertEqual(len(metadata["errors"]), 1)
        self.assertEqual(metadata["errors"][0]["error_type"], "Exception")
        self.assertEqual(metadata["errors"][0]["error_message"], "Test error")
        self.assertIn("timestamp", metadata["errors"][0])


if __name__ == '__main__':
    unittest.main()