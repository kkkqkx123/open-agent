"""测试重构后的插件系统

验证新的Hook系统和插件管理器是否正常工作。
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.core.workflow.plugins.manager import PluginManager
from src.core.workflow.plugins.interfaces import PluginType, PluginContext
from src.core.workflow.graph.nodes._node_plugin_system import NodeHookManager
from src.core.workflow.graph.nodes.start_node import StartNode
from src.core.workflow.graph.nodes.end_node import EndNode
from src.core.workflow.states import WorkflowState


class TestPluginSystemRefactor:
    """测试重构后的插件系统"""
    
    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        config = {
            "start_plugins": {
                "builtin": [
                    {"name": "context_summary", "enabled": True, "priority": 10, "config": {}},
                    {"name": "environment_check", "enabled": True, "priority": 20, "config": {}}
                ],
                "external": []
            },
            "end_plugins": {
                "builtin": [
                    {"name": "result_summary", "enabled": True, "priority": 10, "config": {}},
                    {"name": "execution_stats", "enabled": True, "priority": 20, "config": {}}
                ],
                "external": []
            },
            "hook_plugins": {
                "global": [
                    {"name": "performance_monitoring", "enabled": True, "priority": 10, "config": {}},
                    {"name": "logging", "enabled": True, "priority": 20, "config": {}}
                ],
                "node_specific": {
                    "start_node": [
                        {"name": "error_recovery", "enabled": True, "priority": 10, "config": {}}
                    ],
                    "end_node": [
                        {"name": "error_recovery", "enabled": True, "priority": 10, "config": {}}
                    ]
                },
                "external": []
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            yield f.name
        
        Path(f.name).unlink()
    
    def test_plugin_manager_initialization(self, temp_config_file):
        """测试插件管理器初始化"""
        manager = PluginManager(temp_config_file)
        
        # 测试初始化
        assert manager.initialize() is True
        assert manager._initialized is True
        
        # 测试获取插件
        start_plugins = manager.get_enabled_plugins(PluginType.START)
        assert len(start_plugins) > 0
        
        end_plugins = manager.get_enabled_plugins(PluginType.END)
        assert len(end_plugins) > 0
        
        # 清理
        manager.cleanup()
    
    def test_node_hook_manager_initialization(self, temp_config_file):
        """测试Node Hook管理器初始化"""
        hook_manager = NodeHookManager(temp_config_file)
        
        # 测试初始化
        assert hook_manager.initialize() is True
        assert hook_manager._initialized is True
        
        # 测试获取Hook插件
        start_hooks = hook_manager.get_hook_plugins("start_node")
        assert len(start_hooks) > 0
        
        end_hooks = hook_manager.get_hook_plugins("end_node")
        assert len(end_hooks) > 0
        
        # 清理
        hook_manager.cleanup()
    
    def test_start_node_with_hooks(self, temp_config_file):
        """测试START节点使用新的Hook系统"""
        start_node = StartNode(temp_config_file)
        
        # 创建测试状态
        state = WorkflowState()
        state.set_value('workflow_id', 'test_workflow')
        
        # 创建测试配置
        config = {
            'next_node': 'test_next_node',
            'context_metadata': {'test': True}
        }
        
        # 执行节点
        result = start_node.execute(state, config)
        
        # 验证结果
        assert result is not None
        assert result.state is not None
        assert result.next_node == 'test_next_node'
        
        # 检查元数据
        if hasattr(result.state, 'get_metadata'):
            start_metadata = result.state.get_metadata('start_metadata', {})
            assert 'execution_time' in start_metadata
            assert 'plugins_executed' in start_metadata
            assert start_metadata['success'] is True
        
        # 清理
        start_node.cleanup()
    
    def test_end_node_with_hooks(self, temp_config_file):
        """测试END节点使用新的Hook系统"""
        end_node = EndNode(temp_config_file)
        
        # 创建测试状态
        state = WorkflowState()
        state.set_value('workflow_id', 'test_workflow')
        state.set_value('start_metadata', {'timestamp': 1234567890})
        
        # 创建测试配置
        config = {
            'context_metadata': {'test': True}
        }
        
        # 执行节点
        result = end_node.execute(state, config)
        
        # 验证结果
        assert result is not None
        assert result.state is not None
        assert result.next_node is None  # END节点没有下一个节点
        
        # 检查工作流完成标记
        if hasattr(result.state, 'get'):
            assert result.state.get('workflow_completed') is True
        
        # 检查元数据
        if hasattr(result.state, 'get_metadata'):
            end_metadata = result.state.get_metadata('end_metadata', {})
            assert 'execution_time' in end_metadata
            assert 'plugins_executed' in end_metadata
            assert end_metadata['success'] is True
        
        # 清理
        end_node.cleanup()
    
    def test_plugin_manager_stats(self, temp_config_file):
        """测试插件管理器统计信息"""
        manager = PluginManager(temp_config_file)
        manager.initialize()
        
        # 获取统计信息
        stats = manager.get_manager_stats()
        
        # 验证统计信息
        assert stats['initialized'] is True
        assert stats['config_path'] == temp_config_file
        assert stats['loaded_plugins_count'] > 0
        assert stats['config_loaded'] is True
        
        # 清理
        manager.cleanup()
    
    def test_node_hook_manager_stats(self, temp_config_file):
        """测试Node Hook管理器统计信息"""
        hook_manager = NodeHookManager(temp_config_file)
        hook_manager.initialize()
        
        # 获取统计信息
        stats = hook_manager.get_manager_stats()
        
        # 验证统计信息
        assert stats['initialized'] is True
        assert stats['config_path'] == temp_config_file
        assert stats['config_loaded'] is True
        assert 'plugin_manager' in stats
        assert 'node_hook_manager' in stats
        
        # 清理
        hook_manager.cleanup()
    
    def test_hook_execution_service(self, temp_config_file):
        """测试Hook执行服务"""
        hook_manager = NodeHookManager(temp_config_file)
        hook_manager.initialize()
        
        # 获取Hook执行器
        hook_executor = hook_manager.hook_executor
        
        # 测试执行计数
        count = hook_executor.get_execution_count("test_node")
        assert count == 0
        
        # 增加执行计数
        new_count = hook_executor.increment_execution_count("test_node")
        assert new_count == 1
        
        # 测试性能统计
        hook_executor.update_performance_stats("test_node", 1.5, True)
        perf_stats = hook_executor.get_performance_stats()
        assert "test_node" in perf_stats
        assert perf_stats["test_node"]["total_executions"] == 1
        assert perf_stats["test_node"]["successful_executions"] == 1
        assert perf_stats["test_node"]["total_execution_time"] == 1.5
        
        # 清理
        hook_manager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])