"""触发器基类单元测试

测试触发器基类的功能，包括：
1. 触发器接口的实现
2. 基础触发器的功能
3. 触发器处理器的功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any
import uuid

from src.infrastructure.graph.triggers.base import (
    TriggerType, TriggerEvent, ITrigger, BaseTrigger, TriggerHandler
)
from src.domain.agent.state import AgentState, AgentStatus, AgentMessage
from src.domain.tools.interfaces import ToolResult


class TestTriggerType(unittest.TestCase):
    """测试触发器类型枚举"""

    def test_trigger_type_values(self):
        """测试触发器类型枚举值"""
        self.assertEqual(TriggerType.TIME.value, "time")
        self.assertEqual(TriggerType.STATE.value, "state")
        self.assertEqual(TriggerType.EVENT.value, "event")
        self.assertEqual(TriggerType.CUSTOM.value, "custom")


class TestTriggerEvent(unittest.TestCase):
    """测试触发器事件"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "test-trigger-1"
        self.trigger_type = TriggerType.STATE
        self.timestamp = datetime.now()
        self.data = {"key": "value"}
        self.metadata = {"source": "test"}

    def test_trigger_event_creation(self):
        """测试触发器事件创建"""
        event = TriggerEvent(
            id="",
            trigger_id=self.trigger_id,
            trigger_type=self.trigger_type,
            timestamp=self.timestamp,
            data=self.data,
            metadata=self.metadata
        )
        
        # 检查ID是否自动生成
        self.assertIsNotNone(event.id)
        self.assertIsInstance(uuid.UUID(event.id), uuid.UUID)
        
        # 检查其他属性
        self.assertEqual(event.trigger_id, self.trigger_id)
        self.assertEqual(event.trigger_type, self.trigger_type)
        self.assertEqual(event.timestamp, self.timestamp)
        self.assertEqual(event.data, self.data)
        self.assertEqual(event.metadata, self.metadata)

    def test_trigger_event_auto_id(self):
        """测试触发器事件自动生成ID"""
        event = TriggerEvent(
            id="",
            trigger_id=self.trigger_id,
            trigger_type=self.trigger_type,
            timestamp=self.timestamp,
            data=self.data,
            metadata=self.metadata
        )
        
        # 确保ID是有效的UUID
        self.assertTrue(uuid.UUID(event.id))


class MockTrigger(ITrigger):
    """模拟触发器实现用于测试接口"""
    
    def __init__(self, trigger_id: str = "mock-trigger", trigger_type: TriggerType = TriggerType.CUSTOM):
        self._trigger_id = trigger_id
        self._trigger_type = trigger_type
        self._enabled = True
        self._config = {"test": "config"}
        self.evaluate_called = False
        self.execute_called = False
        self.execute_result = {"result": "success"}
    
    @property
    def trigger_id(self) -> str:
        return self._trigger_id
    
    @property
    def trigger_type(self) -> TriggerType:
        return self._trigger_type
    
    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        self.evaluate_called = True
        return True
    
    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        self.execute_called = True
        return self.execute_result
    
    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False
    
    def create_event(self, data: Dict[str, Any], metadata: Dict[str, Any] = None) -> TriggerEvent:
        return TriggerEvent(
            id="",
            trigger_id=self._trigger_id,
            trigger_type=self._trigger_type,
            timestamp=datetime.now(),
            data=data,
            metadata=metadata or {}
        )
    
    def update_trigger_info(self) -> None:
        pass


class TestITriggerInterface(unittest.TestCase):
    """测试触发器接口"""

    def setUp(self):
        """测试前准备"""
        self.mock_trigger = MockTrigger()

    def test_interface_properties(self):
        """测试接口属性"""
        self.assertEqual(self.mock_trigger.trigger_id, "mock-trigger")
        self.assertEqual(self.mock_trigger.trigger_type, TriggerType.CUSTOM)

    def test_interface_methods(self):
        """测试接口方法"""
        # 创建测试数据
        state = AgentState(agent_id="test-agent")
        context = {"test": "context"}
        
        # 测试evaluate方法
        result = self.mock_trigger.evaluate(state, context)
        self.assertTrue(result)
        self.assertTrue(self.mock_trigger.evaluate_called)
        
        # 测试execute方法
        result = self.mock_trigger.execute(state, context)
        self.assertEqual(result, {"result": "success"})
        self.assertTrue(self.mock_trigger.execute_called)
        
        # 测试配置获取
        config = self.mock_trigger.get_config()
        self.assertEqual(config, {"test": "config"})
        
        # 测试启用状态
        self.assertTrue(self.mock_trigger.is_enabled())
        
        # 测试启用/禁用功能
        self.mock_trigger.disable()
        self.assertFalse(self.mock_trigger.is_enabled())
        
        self.mock_trigger.enable()
        self.assertTrue(self.mock_trigger.is_enabled())
        
        # 测试事件创建
        event = self.mock_trigger.create_event({"data": "test"})
        self.assertIsInstance(event, TriggerEvent)
        self.assertEqual(event.trigger_id, "mock-trigger")


class TestBaseTrigger(unittest.TestCase):
    """测试基础触发器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "test-base-trigger"
        self.trigger_type = TriggerType.STATE
        self.config = {
            "rate_limit": 1.0,
            "max_triggers": 5,
            "test_config": "value"
        }
        self.base_trigger = BaseTrigger(
            trigger_id=self.trigger_id,
            trigger_type=self.trigger_type,
            config=self.config
        )

    def test_base_trigger_initialization(self):
        """测试基础触发器初始化"""
        self.assertEqual(self.base_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.base_trigger.trigger_type, self.trigger_type)
        self.assertEqual(self.base_trigger.get_config(), self.config)
        self.assertTrue(self.base_trigger.is_enabled())
        self.assertIsNone(self.base_trigger.get_last_triggered())
        self.assertEqual(self.base_trigger.get_trigger_count(), 0)

    def test_base_trigger_enable_disable(self):
        """测试基础触发器启用/禁用功能"""
        # 默认应该是启用的
        self.assertTrue(self.base_trigger.is_enabled())
        
        # 禁用触发器
        self.base_trigger.disable()
        self.assertFalse(self.base_trigger.is_enabled())
        
        # 启用触发器
        self.base_trigger.enable()
        self.assertTrue(self.base_trigger.is_enabled())

    def test_base_trigger_config_copy(self):
        """测试配置复制功能"""
        config = self.base_trigger.get_config()
        # 修改返回的配置不应该影响原始配置
        config["new_key"] = "new_value"
        # 获取新的配置应该还是原始配置
        new_config = self.base_trigger.get_config()
        self.assertNotIn("new_key", new_config)
        self.assertEqual(new_config, self.config)

    def test_base_trigger_update_info(self):
        """测试触发器信息更新"""
        # 初始状态
        self.assertIsNone(self.base_trigger.get_last_triggered())
        self.assertEqual(self.base_trigger.get_trigger_count(), 0)
        
        # 更新信息
        before_time = datetime.now()
        self.base_trigger._update_trigger_info()
        after_time = datetime.now()
        
        # 检查更新结果
        last_triggered = self.base_trigger.get_last_triggered()
        self.assertIsNotNone(last_triggered)
        self.assertGreaterEqual(last_triggered, before_time)
        self.assertLessEqual(last_triggered, after_time)
        self.assertEqual(self.base_trigger.get_trigger_count(), 1)

    def test_base_trigger_rate_limit_check(self):
        """测试速率限制检查"""
        # 没有触发时间时应该通过
        self.assertTrue(self.base_trigger._check_rate_limit())
        
        # 设置触发时间
        self.base_trigger._last_triggered = datetime.now()
        
        # 由于时间间隔太短，应该不通过
        self.assertFalse(self.base_trigger._check_rate_limit())
        
        # 模拟时间过去足够久
        with patch('src.infrastructure.graph.triggers.base.datetime') as mock_datetime:
            # 设置当前时间为很久以后
            future_time = datetime.now().replace(year=2099)
            mock_datetime.now.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            self.assertTrue(self.base_trigger._check_rate_limit())

    def test_base_trigger_max_triggers_check(self):
        """测试最大触发次数检查"""
        # 没有触发次数限制时应该通过
        self.assertTrue(self.base_trigger._check_max_triggers())
        
        # 设置触发次数
        self.base_trigger._trigger_count = 3
        self.assertTrue(self.base_trigger._check_max_triggers())
        
        # 达到最大触发次数时应该不通过
        self.base_trigger._trigger_count = 5
        self.assertFalse(self.base_trigger._check_max_triggers())
        
        # 超过最大触发次数时应该不通过
        self.base_trigger._trigger_count = 10
        self.assertFalse(self.base_trigger._check_max_triggers())

    def test_base_trigger_can_trigger(self):
        """测试触发器是否可以触发"""
        # 默认情况下应该可以触发
        self.assertTrue(self.base_trigger.can_trigger())
        
        # 禁用触发器时不应该触发
        self.base_trigger.disable()
        self.assertFalse(self.base_trigger.can_trigger())
        
        # 重新启用
        self.base_trigger.enable()
        
        # 设置触发次数达到上限
        self.base_trigger._trigger_count = 5
        self.assertFalse(self.base_trigger.can_trigger())
        
        # 重置触发次数但设置速率限制
        self.base_trigger._trigger_count = 0
        self.base_trigger._last_triggered = datetime.now()
        self.assertFalse(self.base_trigger.can_trigger())

    def test_base_trigger_create_event(self):
        """测试创建触发器事件"""
        data = {"test": "data"}
        metadata = {"source": "test"}
        
        before_time = datetime.now()
        event = self.base_trigger.create_event(data, metadata)
        after_time = datetime.now()
        
        # 检查事件属性
        self.assertIsInstance(event, TriggerEvent)
        self.assertEqual(event.trigger_id, self.trigger_id)
        self.assertEqual(event.trigger_type, self.trigger_type)
        self.assertEqual(event.data, data)
        self.assertEqual(event.metadata, metadata)
        self.assertGreaterEqual(event.timestamp, before_time)
        self.assertLessEqual(event.timestamp, after_time)
        
        # 检查ID是否自动生成
        self.assertIsNotNone(event.id)
        self.assertIsInstance(uuid.UUID(event.id), uuid.UUID)

    def test_base_trigger_without_limits(self):
        """测试没有限制的触发器"""
        # 创建没有速率限制和最大触发次数的触发器
        config = {"test": "value"}
        trigger = BaseTrigger(
            trigger_id="no-limit-trigger",
            trigger_type=TriggerType.CUSTOM,
            config=config
        )
        
        # 应该可以触发
        self.assertTrue(trigger.can_trigger())
        
        # 检查速率限制（应该通过）
        self.assertTrue(trigger._check_rate_limit())
        
        # 检查最大触发次数（应该通过）
        self.assertTrue(trigger._check_max_triggers())


class TestTriggerHandler(unittest.TestCase):
    """测试触发器处理器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_handler = TriggerHandler()
        self.test_event = TriggerEvent(
            id="",
            trigger_id="test-trigger",
            trigger_type=TriggerType.STATE,
            timestamp=datetime.now(),
            data={"test": "data"},
            metadata={"source": "test"}
        )

    def test_trigger_handler_initialization(self):
        """测试触发器处理器初始化"""
        self.assertEqual(self.trigger_handler._handlers, {})

    def test_trigger_handler_register(self):
        """测试注册处理器"""
        def test_handler(event: TriggerEvent):
            pass
        
        # 注册处理器
        self.trigger_handler.register_handler("state", test_handler)
        
        # 检查是否注册成功
        self.assertIn("state", self.trigger_handler._handlers)
        self.assertIn(test_handler, self.trigger_handler._handlers["state"])
        
        # 注册同一个类型的另一个处理器
        def another_handler(event: TriggerEvent):
            pass
        
        self.trigger_handler.register_handler("state", another_handler)
        self.assertEqual(len(self.trigger_handler._handlers["state"]), 2)
        self.assertIn(another_handler, self.trigger_handler._handlers["state"])

    def test_trigger_handler_unregister(self):
        """测试注销处理器"""
        def test_handler(event: TriggerEvent):
            pass
        
        # 先注册处理器
        self.trigger_handler.register_handler("state", test_handler)
        self.assertIn("state", self.trigger_handler._handlers)
        self.assertIn(test_handler, self.trigger_handler._handlers["state"])
        
        # 注销处理器
        result = self.trigger_handler.unregister_handler("state", test_handler)
        self.assertTrue(result)
        self.assertNotIn(test_handler, self.trigger_handler._handlers["state"])
        
        # 尝试注销不存在的处理器
        result = self.trigger_handler.unregister_handler("state", test_handler)
        self.assertFalse(result)
        
        # 尝试注销不存在类型的处理器
        result = self.trigger_handler.unregister_handler("nonexistent", test_handler)
        self.assertFalse(result)

    def test_trigger_handler_handle_event(self):
        """测试处理事件"""
        # 创建模拟处理器
        handler1 = Mock()
        handler2 = Mock()
        
        # 注册处理器
        self.trigger_handler.register_handler("state", handler1)
        self.trigger_handler.register_handler("state", handler2)
        
        # 处理事件
        self.trigger_handler.handle_event(self.test_event)
        
        # 检查处理器是否被调用
        handler1.assert_called_once_with(self.test_event)
        handler2.assert_called_once_with(self.test_event)

    def test_trigger_handler_handle_event_with_exception(self):
        """测试处理事件时处理器抛出异常"""
        # 创建正常处理器和异常处理器
        normal_handler = Mock()
        exception_handler = Mock(side_effect=Exception("Test exception"))
        
        # 注册处理器
        self.trigger_handler.register_handler("state", exception_handler)
        self.trigger_handler.register_handler("state", normal_handler)
        
        # 处理事件，不应该因为一个处理器异常而影响其他处理器
        self.trigger_handler.handle_event(self.test_event)
        
        # 检查处理器是否被调用
        exception_handler.assert_called_once_with(self.test_event)
        normal_handler.assert_called_once_with(self.test_event)

    def test_trigger_handler_list_handlers(self):
        """测试列出处理器"""
        # 初始状态应该没有处理器
        handlers = self.trigger_handler.list_handlers()
        self.assertEqual(handlers, {})
        
        # 注册一些处理器
        def handler1(event: TriggerEvent):
            pass
        
        def handler2(event: TriggerEvent):
            pass
        
        def handler3(event: TriggerEvent):
            pass
        
        self.trigger_handler.register_handler("state", handler1)
        self.trigger_handler.register_handler("state", handler2)
        self.trigger_handler.register_handler("event", handler3)
        
        # 检查处理器列表
        handlers = self.trigger_handler.list_handlers()
        self.assertEqual(handlers, {"state": 2, "event": 1})


class TestBaseTriggerWithAgentState(unittest.TestCase):
    """测试基础触发器与Agent状态的交互"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "agent-state-trigger"
        self.trigger_type = TriggerType.STATE
        self.config = {"test": "config"}
        self.base_trigger = BaseTrigger(
            trigger_id=self.trigger_id,
            trigger_type=self.trigger_type,
            config=self.config
        )
        
        # 创建测试用的Agent状态
        self.agent_state = AgentState(
            agent_id="test-agent",
            agent_type="test-type",
            messages=[
                AgentMessage(content="Hello", role="user"),
                AgentMessage(content="Hi there", role="assistant")
            ],
            context={"task": "test-task"},
            current_task="Test task",
            status=AgentStatus.THINKING,
            max_iterations=5,
            iteration_count=2,
            custom_fields={"custom": "value"}
        )

    def test_create_event_with_agent_state(self):
        """测试使用Agent状态创建事件"""
        data = {
            "agent_id": self.agent_state.agent_id,
            "agent_status": self.agent_state.status.value,
            "iteration_count": self.agent_state.iteration_count
        }
        metadata = {
            "agent_type": self.agent_state.agent_type,
            "max_iterations": self.agent_state.max_iterations
        }
        
        event = self.base_trigger.create_event(data, metadata)
        
        # 检查事件数据
        self.assertEqual(event.data["agent_id"], "test-agent")
        self.assertEqual(event.data["agent_status"], "thinking")
        self.assertEqual(event.data["iteration_count"], 2)
        self.assertEqual(event.metadata["agent_type"], "test-type")
        self.assertEqual(event.metadata["max_iterations"], 5)


if __name__ == '__main__':
    unittest.main()