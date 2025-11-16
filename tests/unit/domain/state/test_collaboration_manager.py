"""协作管理器单元测试"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid
import zlib
import pickle

from src.domain.state.collaboration_manager import StateLifecycleManagerImpl
from src.infrastructure.state.interfaces import StateSnapshot


class TestStateLifecycleManagerImpl(unittest.TestCase):
    """StateLifecycleManagerImpl 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_snapshot_store = Mock()
        self.mock_crud_manager = Mock()
        self.collaboration_manager = StateLifecycleManagerImpl(
            crud_manager=self.mock_crud_manager,
            snapshot_store=self.mock_snapshot_store
        )
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.collaboration_manager.crud_manager, self.mock_crud_manager)
        self.assertEqual(self.collaboration_manager.snapshot_store, self.mock_snapshot_store)
        self.assertIsNotNone(self.collaboration_manager.history_manager)
        self.assertEqual(self.collaboration_manager._agent_snapshots, {})
        self.assertEqual(self.collaboration_manager._agent_history, {})
    
    def test_validate_domain_state_valid(self):
        """测试验证有效的域状态"""
        # 创建有效的域状态对象
        domain_state = Mock()
        domain_state.agent_id = "test_agent"
        domain_state.messages = []
        domain_state.iteration_count = 5
        domain_state.max_iterations = 10
        
        errors = self.collaboration_manager.validate_domain_state(domain_state)
        self.assertEqual(errors, [])
    
    def test_validate_domain_state_missing_agent_id(self):
        """测试验证缺少agent_id的域状态"""
        domain_state = Mock()
        domain_state.agent_id = ""
        domain_state.messages = []
        # 确保没有 iteration_count 和 max_iterations 属性，避免比较错误
        del domain_state.iteration_count
        del domain_state.max_iterations
        
        errors = self.collaboration_manager.validate_domain_state(domain_state)
        self.assertIn("缺少agent_id字段", errors)
    
    def test_validate_domain_state_missing_messages(self):
        """测试验证缺少messages的域状态"""
        domain_state = Mock()
        domain_state.agent_id = "test_agent"
        del domain_state.messages  # 删除messages属性
        # 确保没有 iteration_count 和 max_iterations 属性，避免比较错误
        del domain_state.iteration_count
        del domain_state.max_iterations
        
        errors = self.collaboration_manager.validate_domain_state(domain_state)
        self.assertIn("缺少messages字段", errors)
    
    def test_validate_domain_state_invalid_messages_type(self):
        """测试验证messages字段类型错误"""
        domain_state = Mock()
        domain_state.agent_id = "test_agent"
        domain_state.messages = "not a list"  # 字符串而不是列表
        # 确保没有 iteration_count 和 max_iterations 属性，避免比较错误
        del domain_state.iteration_count
        del domain_state.max_iterations
        
        errors = self.collaboration_manager.validate_domain_state(domain_state)
        self.assertIn("messages字段必须是列表类型", errors)
    
    def test_validate_domain_state_iteration_exceeded(self):
        """测试验证迭代次数超过限制"""
        domain_state = Mock()
        domain_state.agent_id = "test_agent"
        domain_state.messages = []
        domain_state.iteration_count = 15
        domain_state.max_iterations = 10
        
        errors = self.collaboration_manager.validate_domain_state(domain_state)
        self.assertIn("迭代计数超过最大限制", errors)
    
    def test_create_snapshot(self):
        """测试创建快照"""
        # 创建域状态对象
        domain_state = Mock()
        domain_state.agent_id = "test_agent"
        domain_state.to_dict.return_value = {"key": "value"}
        
        # 模拟snapshot_store.save_snapshot
        self.mock_snapshot_store.save_snapshot.return_value = True
        
        # 调用create_snapshot
        snapshot_id = self.collaboration_manager.create_snapshot(domain_state, "test snapshot")
        
        # 验证结果
        self.assertIsInstance(snapshot_id, str)
        
        # 验证save_snapshot被调用
        self.mock_snapshot_store.save_snapshot.assert_called_once()
        
        # 获取传递给save_snapshot的参数
        call_args = self.mock_snapshot_store.save_snapshot.call_args[0][0]
        self.assertIsInstance(call_args, StateSnapshot)
        self.assertEqual(call_args.agent_id, "test_agent")
        self.assertEqual(call_args.snapshot_name, "test snapshot")
        self.assertEqual(call_args.domain_state, {"key": "value"})
        self.assertIsInstance(call_args.timestamp, datetime)
        self.assertIsInstance(call_args.compressed_data, bytes)
        self.assertGreater(call_args.size_bytes, 0)
    
    def test_create_snapshot_without_to_dict(self):
        """测试创建快照时域状态没有to_dict方法"""
        # 创建没有to_dict方法的域状态对象
        domain_state = Mock()
        domain_state.agent_id = "test_agent"
        del domain_state.to_dict  # 删除to_dict方法
        domain_state.__dict__ = {"key": "value"}
        
        # 模拟snapshot_store.save_snapshot
        self.mock_snapshot_store.save_snapshot.return_value = True
        
        # 调用create_snapshot
        snapshot_id = self.collaboration_manager.create_snapshot(domain_state, "test snapshot")
        
        # 验证结果
        self.assertIsInstance(snapshot_id, str)
        
        # 验证save_snapshot被调用
        self.mock_snapshot_store.save_snapshot.assert_called_once()
        
        # 获取传递给save_snapshot的参数
        call_args = self.mock_snapshot_store.save_snapshot.call_args[0][0]
        self.assertEqual(call_args.domain_state, {"key": "value"})
    
    def test_restore_snapshot_exists(self):
        """测试恢复存在的快照"""
        # 创建模拟快照
        mock_snapshot = Mock()
        mock_snapshot.domain_state = {"key": "value"}
        
        # 模拟snapshot_store.load_snapshot
        self.mock_snapshot_store.load_snapshot.return_value = mock_snapshot
        
        # 调用restore_snapshot
        result = self.collaboration_manager.restore_snapshot("test_snapshot_id")
        
        # 验证结果
        self.assertEqual(result, {"key": "value"})
        self.mock_snapshot_store.load_snapshot.assert_called_once_with("test_snapshot_id")
    
    def test_restore_snapshot_not_exists(self):
        """测试恢复不存在的快照"""
        # 模拟snapshot_store.load_snapshot返回None
        self.mock_snapshot_store.load_snapshot.return_value = None
        
        # 调用restore_snapshot
        result = self.collaboration_manager.restore_snapshot("nonexistent_snapshot_id")
        
        # 验证结果
        self.assertIsNone(result)
        self.mock_snapshot_store.load_snapshot.assert_called_once_with("nonexistent_snapshot_id")
    
    def test_record_state_change(self):
        """测试记录状态变化"""
        # 调用record_state_change
        history_id = self.collaboration_manager.record_state_change(
            "test_agent", 
            "test_action", 
            {"old_key": "old_value"}, 
            {"new_key": "new_value"}
        )
        
        # 验证结果
        self.assertIsInstance(history_id, str)
        
        # 验证返回的是UUID格式的字符串
        try:
            uuid.UUID(history_id)
        except ValueError:
            self.fail("返回的history_id不是有效的UUID")


if __name__ == "__main__":
    unittest.main()