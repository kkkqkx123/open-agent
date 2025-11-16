"""状态管理器单元测试"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import pickle
import base64
from datetime import datetime

from src.domain.state.manager import StateManager
from src.infrastructure.graph.states import WorkflowState


class TestStateManager(unittest.TestCase):
    """StateManager 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.state_manager_json = StateManager(serialization_format="json")
        self.state_manager_pickle = StateManager(serialization_format="pickle")
    
    def test_init_json(self):
        """测试初始化为JSON格式"""
        manager = StateManager(serialization_format="json")
        self.assertEqual(manager.serialization_format, "json")
        self.assertEqual(manager._states, {})
    
    def test_init_pickle(self):
        """测试初始化为Pickle格式"""
        manager = StateManager(serialization_format="pickle")
        self.assertEqual(manager.serialization_format, "pickle")
        self.assertEqual(manager._states, {})
    
    def test_serialize_agent_state_json(self):
        """测试序列化WorkflowState为JSON格式"""
        # 创建WorkflowState
        workflow_state: WorkflowState = {
            "messages": [],
            "tool_results": [],
            "current_step": "start",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": datetime.now(),
            "errors": [],
            "input": "test input",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 序列化
        result = self.state_manager_json.serialize_agent_state(workflow_state)
        
        # 验证结果
        self.assertIsInstance(result, bytes)
        
        # 反序列化验证内容
        json_str = result.decode('utf-8')
        data = json.loads(json_str)
        self.assertEqual(data["workflow_name"], "test_workflow")
        self.assertEqual(data["input"], "test input")
    
    def test_serialize_agent_state_pickle(self):
        """测试序列化WorkflowState为Pickle格式"""
        # 创建WorkflowState
        workflow_state: WorkflowState = {
            "messages": [],
            "tool_results": [],
            "current_step": "start",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": datetime.now(),
            "errors": [],
            "input": "test input",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 序列化
        result = self.state_manager_pickle.serialize_agent_state(workflow_state)
        
        # 验证结果
        self.assertIsInstance(result, bytes)
        
        # 反序列化验证内容
        data = pickle.loads(result)
        self.assertEqual(data["workflow_name"], "test_workflow")
        self.assertEqual(data["input"], "test input")
    
    def test_serialize_agent_state_invalid_format(self):
        """测试序列化WorkflowState使用无效格式"""
        # 创建无效格式的管理器
        manager = StateManager(serialization_format="invalid")
        
        # 创建WorkflowState
        workflow_state: WorkflowState = {
            "messages": [],
            "tool_results": [],
            "current_step": "start",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": datetime.now(),
            "errors": [],
            "input": "test input",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 序列化，应该抛出异常
        with self.assertRaises(ValueError) as context:
            manager.serialize_agent_state(workflow_state)
        
        self.assertIn("不支持的序列化格式", str(context.exception))
    
    def test_deserialize_agent_state_json(self):
        """测试反序列化WorkflowState从JSON格式"""
        # 创建WorkflowState
        workflow_state: WorkflowState = {
            "messages": [],
            "tool_results": [],
            "current_step": "start",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": datetime.now(),
            "errors": [],
            "input": "test input",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 序列化
        serialized = self.state_manager_json.serialize_agent_state(workflow_state)
        
        # 反序列化
        result = self.state_manager_json.deserialize_agent_state(serialized)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result["workflow_name"], "test_workflow")
        self.assertEqual(result["input"], "test input")
        self.assertEqual(result["max_iterations"], 10)
    
    def test_deserialize_agent_state_pickle(self):
        """测试反序列化WorkflowState从Pickle格式"""
        # 创建WorkflowState
        workflow_state: WorkflowState = {
            "messages": [],
            "tool_results": [],
            "current_step": "start",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": datetime.now(),
            "errors": [],
            "input": "test input",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 序列化
        serialized = self.state_manager_pickle.serialize_agent_state(workflow_state)
        
        # 反序列化
        result = self.state_manager_pickle.deserialize_agent_state(serialized)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result["workflow_name"], "test_workflow")
        self.assertEqual(result["input"], "test input")
        self.assertEqual(result["max_iterations"], 10)
    
    def test_deserialize_agent_state_invalid_format(self):
        """测试反序列化WorkflowState使用无效格式"""
        # 创建无效格式的管理器
        manager = StateManager(serialization_format="invalid")
        
        # 反序列化，应该抛出异常
        with self.assertRaises(ValueError) as context:
            manager.deserialize_agent_state(b"some data")
        
        self.assertIn("不支持的序列化格式", str(context.exception))
    
    def test_serialize_state_json(self):
        """测试序列化状态字典为JSON格式"""
        state = {
            "key1": "value1",
            "key2": 123,
            "key3": datetime.now()
        }
        
        # 序列化
        result = self.state_manager_json.serialize_state(state)
        
        # 验证结果
        self.assertIsInstance(result, str)
        
        # 反序列化验证内容
        data = json.loads(result)
        self.assertEqual(data["key1"], "value1")
        self.assertEqual(data["key2"], 123)
    
    def test_serialize_state_pickle(self):
        """测试序列化状态字典为Pickle格式"""
        state = {
            "key1": "value1",
            "key2": 123,
            "key3": datetime.now()
        }
        
        # 序列化
        result = self.state_manager_pickle.serialize_state(state)
        
        # 验证结果
        self.assertIsInstance(result, str)
        
        # 解码并反序列化验证内容
        decoded_data = base64.b64decode(result.encode('utf-8'))
        data = pickle.loads(decoded_data)
        self.assertEqual(data["key1"], "value1")
        self.assertEqual(data["key2"], 123)
    
    def test_deserialize_state_json(self):
        """测试反序列化状态字典从JSON格式"""
        state = {
            "key1": "value1",
            "key2": 123
        }
        
        # 序列化
        serialized = self.state_manager_json.serialize_state(state)
        
        # 反序列化
        result = self.state_manager_json.deserialize_state(serialized)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"], 123)
    
    def test_deserialize_state_pickle(self):
        """测试反序列化状态字典从Pickle格式"""
        state = {
            "key1": "value1",
            "key2": 123
        }
        
        # 序列化
        serialized = self.state_manager_pickle.serialize_state(state)
        
        # 反序列化
        result = self.state_manager_pickle.deserialize_state(serialized)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"], 123)
    
    def test_validate_state_valid(self):
        """测试验证有效状态"""
        # 创建有效状态
        state: WorkflowState = {
            "messages": [],
            "tool_results": [],
            "current_step": "start",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": datetime.now(),
            "errors": [],
            "input": "test input",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 验证状态
        result = self.state_manager_json.validate_state(state)
        
        # 验证结果
        self.assertTrue(result)
    
    def test_validate_state_missing_fields(self):
        """测试验证缺少字段的状态"""
        # 创建缺少字段的状态
        state = {
            "messages": [],
            "tool_results": [],
            "current_step": "start"
            # 缺少 max_iterations 和 iteration_count
        }
        
        # 验证状态
        result = self.state_manager_json.validate_state(state)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_validate_state_invalid_types(self):
        """测试验证字段类型错误的状态"""
        # 创建字段类型错误的状态
        state: WorkflowState = {
            "messages": "not a list",  # 应该是列表
            "tool_results": [],
            "current_step": "start",
            "max_iterations": "not an int",  # 应该是整数
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": datetime.now(),
            "errors": [],
            "input": "test input",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 验证状态
        result = self.state_manager_json.validate_state(state)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_serialize_state_dict_json(self):
        """测试序列化状态字典为JSON格式（字节）"""
        state = {
            "key1": "value1",
            "key2": 123,
            "key3": datetime.now()
        }
        
        # 序列化
        result = self.state_manager_json.serialize_state_to_bytes(state)
        
        # 验证结果
        self.assertIsInstance(result, bytes)
        
        # 反序列化验证内容
        data = json.loads(result.decode('utf-8'))
        self.assertEqual(data["key1"], "value1")
        self.assertEqual(data["key2"], 123)
    
    def test_serialize_state_dict_pickle(self):
        """测试序列化状态字典为Pickle格式（字节）"""
        state = {
            "key1": "value1",
            "key2": 123,
            "key3": datetime.now()
        }
        
        # 序列化
        result = self.state_manager_pickle.serialize_state_to_bytes(state)
        
        # 验证结果
        self.assertIsInstance(result, bytes)
        
        # 反序列化验证内容
        data = pickle.loads(result)
        self.assertEqual(data["key1"], "value1")
        self.assertEqual(data["key2"], 123)
    
    def test_deserialize_state_dict_json(self):
        """测试反序列化状态字典从JSON格式（字节）"""
        state = {
            "key1": "value1",
            "key2": 123
        }
        
        # 序列化
        serialized = self.state_manager_json.serialize_state_to_bytes(state)
        
        # 反序列化
        result = self.state_manager_json.deserialize_state_from_bytes(serialized)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"], 123)
    
    def test_deserialize_state_dict_pickle(self):
        """测试反序列化状态字典从Pickle格式（字节）"""
        state = {
            "key1": "value1",
            "key2": 123
        }
        
        # 序列化
        serialized = self.state_manager_pickle.serialize_state_to_bytes(state)
        
        # 反序列化
        result = self.state_manager_pickle.deserialize_state_from_bytes(serialized)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"], 123)
    
    def test_create_state(self):
        """测试创建状态"""
        initial_state = {
            "key1": "value1",
            "key2": 123
        }
        
        # 创建状态
        result = self.state_manager_json.create_state("test_state", initial_state)
        
        # 验证结果
        self.assertEqual(result, initial_state)
        self.assertEqual(self.state_manager_json._states["test_state"], initial_state)
        
        # 验证返回的是副本
        result["key1"] = "modified"
        self.assertEqual(self.state_manager_json._states["test_state"]["key1"], "value1")
    
    def test_update_state(self):
        """测试更新状态"""
        current_state = {
            "key1": "value1",
            "key2": 123
        }
        updates = {
            "key2": 456,
            "key3": "new_value"
        }
        
        # 更新状态
        result = self.state_manager_json.update_state("test_state", current_state, updates)
        
        # 验证结果
        expected = {
            "key1": "value1",
            "key2": 456,
            "key3": "new_value"
        }
        self.assertEqual(result, expected)
        self.assertEqual(self.state_manager_json._states["test_state"], expected)
    
    def test_get_state_exists(self):
        """测试获取存在的状态"""
        state = {
            "key1": "value1",
            "key2": 123
        }
        
        # 设置状态
        self.state_manager_json._states["test_state"] = state
        
        # 获取状态
        result = self.state_manager_json.get_state("test_state")
        
        # 验证结果
        self.assertEqual(result, state)
    
    def test_get_state_not_exists(self):
        """测试获取不存在的状态"""
        # 获取不存在的状态
        result = self.state_manager_json.get_state("nonexistent_state")
        
        # 验证结果
        self.assertIsNone(result)
    
    def test_compare_states(self):
        """测试比较两个状态"""
        state1 = {
            "key1": "value1",
            "key2": 123,
            "key3": "common"
        }
        state2 = {
            "key2": 456,  # 修改
            "key3": "common",  # 不变
            "key4": "new_value"  # 新增
        }
        
        # 比较状态
        result = self.state_manager_json.compare_states(state1, state2)
        
        # 验证结果
        self.assertEqual(result["added"], {"key4": "new_value"})
        self.assertEqual(result["removed"], {"key1": "value1"})
        self.assertEqual(result["modified"]["key2"], {"old": 123, "new": 456})
        self.assertEqual(result["unchanged"], {"key3": "common"})
    
    def test_json_serializer_datetime(self):
        """测试JSON序列化器处理datetime"""
        dt = datetime.now()
        
        # 使用JSON序列化器
        result = self.state_manager_json._json_serializer(dt)
        
        # 验证结果
        self.assertEqual(result, dt.isoformat())
    
    def test_json_serializer_object_with_dict(self):
        """测试JSON序列化器处理有__dict__的对象"""
        class TestObject:
            def __init__(self):
                self.value = "test"
        
        obj = TestObject()
        
        # 使用JSON序列化器
        result = self.state_manager_json._json_serializer(obj)
        
        # 验证结果
        self.assertEqual(result, {"value": "test"})
    
    def test_json_serializer_fallback(self):
        """测试JSON序列化器回退到字符串"""
        obj = object()
        
        # 使用JSON序列化器
        result = self.state_manager_json._json_serializer(obj)
        
        # 验证结果
        self.assertEqual(result, str(obj))


if __name__ == "__main__":
    unittest.main()