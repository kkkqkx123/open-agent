"""触发器系统单元测试

测试触发器系统的功能，包括：
1. 触发器注册和管理
2. 事件处理和历史记录
3. 系统启动和停止
4. 工作流触发器系统
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import threading
import time

from src.infrastructure.graph.triggers.system import TriggerSystem, WorkflowTriggerSystem
from src.infrastructure.graph.triggers.base import (
    ITrigger, TriggerType, TriggerEvent, BaseTrigger
)
from src.domain.agent.state import AgentState, AgentStatus, AgentMessage


class MockTrigger(BaseTrigger):
    """模拟触发器用于测试"""
    
    def __init__(self, trigger_id: str, trigger_type: TriggerType = TriggerType.CUSTOM, enabled: bool = True):
        super().__init__(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            config={"test": "config"},
            enabled=enabled
        )
        self.evaluate_called = False
        self.execute_called = False
        self.execute_result = {"result": "success"}
        self.evaluate_result = True
        self.exception_in_evaluate = False
        self.exception_in_execute = False
    
    def evaluate(self, state: AgentState, context: dict) -> bool:
        self.evaluate_called = True
        if self.exception_in_evaluate:
            raise Exception("Evaluate error")
        return self.evaluate_result
    
    def execute(self, state: AgentState, context: dict) -> dict:
        self.execute_called = True
        if self.exception_in_execute:
            raise Exception("Execute error")
        return self.execute_result
    
    def update_trigger_info(self) -> None:
        super()._update_trigger_info()


class TestTriggerSystem(unittest.TestCase):
    """测试触发器系统"""

    def setUp(self):
        """测试前准备"""
        self.trigger_system = TriggerSystem(max_workers=2)

    def test_trigger_system_initialization(self):
        """测试触发器系统初始化"""
        self.assertFalse(self.trigger_system.is_running())
        self.assertEqual(self.trigger_system._executor._max_workers, 2)
        self.assertEqual(self.trigger_system._triggers, {})
        self.assertEqual(self.trigger_system._event_history, [])
        self.assertEqual(self.trigger_system._max_history_size, 1000)

    def test_trigger_system_register_trigger(self):
        """测试注册触发器"""
        trigger = MockTrigger("test-trigger-1")
        
        # 注册触发器
        result = self.trigger_system.register_trigger(trigger)
        self.assertTrue(result)
        self.assertIn("test-trigger-1", self.trigger_system._triggers)
        self.assertEqual(self.trigger_system._triggers["test-trigger-1"], trigger)
        
        # 尝试重复注册同一个触发器
        result = self.trigger_system.register_trigger(trigger)
        self.assertFalse(result)

    def test_trigger_system_unregister_trigger(self):
        """测试注销触发器"""
        trigger = MockTrigger("test-trigger-1")
        
        # 先注册触发器
        self.trigger_system.register_trigger(trigger)
        self.assertIn("test-trigger-1", self.trigger_system._triggers)
        
        # 注销触发器
        result = self.trigger_system.unregister_trigger("test-trigger-1")
        self.assertTrue(result)
        self.assertNotIn("test-trigger-1", self.trigger_system._triggers)
        
        # 尝试注销不存在的触发器
        result = self.trigger_system.unregister_trigger("nonexistent-trigger")
        self.assertFalse(result)

    def test_trigger_system_get_trigger(self):
        """测试获取触发器"""
        trigger = MockTrigger("test-trigger-1")
        
        # 注册触发器
        self.trigger_system.register_trigger(trigger)
        
        # 获取存在的触发器
        result = self.trigger_system.get_trigger("test-trigger-1")
        self.assertEqual(result, trigger)
        
        # 获取不存在的触发器
        result = self.trigger_system.get_trigger("nonexistent-trigger")
        self.assertIsNone(result)

    def test_trigger_system_list_triggers(self):
        """测试列出触发器"""
        # 注册几个触发器
        trigger1 = MockTrigger("trigger-1", TriggerType.STATE)
        trigger2 = MockTrigger("trigger-2", TriggerType.TIME, enabled=False)
        trigger3 = MockTrigger("trigger-3", TriggerType.EVENT)
        
        self.trigger_system.register_trigger(trigger1)
        self.trigger_system.register_trigger(trigger2)
        self.trigger_system.register_trigger(trigger3)
        
        # 禁用一个触发器
        trigger3.disable()
        
        # 获取触发器列表
        triggers = self.trigger_system.list_triggers()
        self.assertEqual(len(triggers), 3)
        
        # 检查触发器信息
        trigger_ids = [t["id"] for t in triggers]
        self.assertIn("trigger-1", trigger_ids)
        self.assertIn("trigger-2", trigger_ids)
        self.assertIn("trigger-3", trigger_ids)
        
        # 检查触发器类型和启用状态
        for trigger_info in triggers:
            if trigger_info["id"] == "trigger-1":
                self.assertEqual(trigger_info["type"], "state")
                self.assertTrue(trigger_info["enabled"])
            elif trigger_info["id"] == "trigger-2":
                self.assertEqual(trigger_info["type"], "time")
                self.assertFalse(trigger_info["enabled"])
            elif trigger_info["id"] == "trigger-3":
                self.assertEqual(trigger_info["type"], "event")
                self.assertFalse(trigger_info["enabled"])

    def test_trigger_system_enable_disable_trigger(self):
        """测试启用/禁用触发器"""
        trigger = MockTrigger("test-trigger-1", enabled=False)
        
        # 注册触发器
        self.trigger_system.register_trigger(trigger)
        self.assertFalse(trigger.is_enabled())
        
        # 启用触发器
        result = self.trigger_system.enable_trigger("test-trigger-1")
        self.assertTrue(result)
        self.assertTrue(trigger.is_enabled())
        
        # 禁用触发器
        result = self.trigger_system.disable_trigger("test-trigger-1")
        self.assertTrue(result)
        self.assertFalse(trigger.is_enabled())
        
        # 尝试启用/禁用不存在的触发器
        result = self.trigger_system.enable_trigger("nonexistent-trigger")
        self.assertFalse(result)
        
        result = self.trigger_system.disable_trigger("nonexistent-trigger")
        self.assertFalse(result)

    def test_trigger_system_evaluate_triggers(self):
        """测试评估触发器"""
        # 创建测试用的Agent状态
        state = AgentState(
            agent_id="test-agent",
            messages=[AgentMessage(content="test message", role="user")],
            status=AgentStatus.THINKING
        )
        context = {"test": "context"}
        
        # 注册几个触发器
        trigger1 = MockTrigger("trigger-1")
        trigger2 = MockTrigger("trigger-2")
        trigger2.evaluate_result = False  # 这个触发器不会触发
        trigger3 = MockTrigger("trigger-3")
        
        self.trigger_system.register_trigger(trigger1)
        self.trigger_system.register_trigger(trigger2)
        self.trigger_system.register_trigger(trigger3)
        
        # 评估触发器
        events = self.trigger_system.evaluate_triggers(state, context)
        
        # 检查结果
        self.assertEqual(len(events), 2)  # trigger1和trigger3应该触发
        self.assertTrue(trigger1.evaluate_called)
        self.assertTrue(trigger1.execute_called)
        self.assertTrue(trigger2.evaluate_called)
        self.assertFalse(trigger2.execute_called)  # 不应该执行
        self.assertTrue(trigger3.evaluate_called)
        self.assertTrue(trigger3.execute_called)
        
        # 检查事件
        event_trigger_ids = [event.trigger_id for event in events]
        self.assertIn("trigger-1", event_trigger_ids)
        self.assertIn("trigger-3", event_trigger_ids)
        
        # 检查触发信息是否更新
        self.assertIsNotNone(trigger1.get_last_triggered())
        self.assertEqual(trigger1.get_trigger_count(), 1)
        self.assertIsNotNone(trigger3.get_last_triggered())
        self.assertEqual(trigger3.get_trigger_count(), 1)

    def test_trigger_system_evaluate_triggers_with_exception(self):
        """测试评估触发器时出现异常"""
        state = AgentState(agent_id="test-agent")
        context = {"test": "context"}
        
        # 创建会抛出异常的触发器
        trigger1 = MockTrigger("trigger-1")
        trigger1.exception_in_evaluate = True
        
        trigger2 = MockTrigger("trigger-2")
        trigger2.exception_in_execute = True
        
        self.trigger_system.register_trigger(trigger1)
        self.trigger_system.register_trigger(trigger2)
        
        # 评估触发器
        events = self.trigger_system.evaluate_triggers(state, context)
        
        # 应该有两个错误事件
        self.assertEqual(len(events), 2)
        
        # 检查错误事件
        for event in events:
            self.assertIn("error", event.data)
            self.assertIn("error_type", event.metadata)

    def test_trigger_system_evaluate_disabled_triggers(self):
        """测试评估禁用的触发器"""
        state = AgentState(agent_id="test-agent")
        context = {"test": "context"}
        
        # 创建禁用的触发器
        trigger = MockTrigger("disabled-trigger", enabled=False)
        self.trigger_system.register_trigger(trigger)
        
        # 评估触发器
        events = self.trigger_system.evaluate_triggers(state, context)
        
        # 禁用的触发器不应该被评估
        self.assertEqual(len(events), 0)
        self.assertFalse(trigger.evaluate_called)
        self.assertFalse(trigger.execute_called)

    def test_trigger_system_start_stop(self):
        """测试系统启动和停止"""
        # 初始状态应该是停止的
        self.assertFalse(self.trigger_system.is_running())
        
        # 启动系统
        self.trigger_system.start()
        self.assertTrue(self.trigger_system.is_running())
        
        # 再次启动不应该有问题
        self.trigger_system.start()
        self.assertTrue(self.trigger_system.is_running())
        
        # 停止系统
        self.trigger_system.stop()
        self.assertFalse(self.trigger_system.is_running())
        
        # 再次停止不应该有问题
        self.trigger_system.stop()
        self.assertFalse(self.trigger_system.is_running())

    def test_trigger_system_register_unregister_event_handler(self):
        """测试注册/注销事件处理器"""
        def test_handler(event: TriggerEvent):
            pass
        
        # 注册事件处理器
        self.trigger_system.register_event_handler(TriggerType.STATE, test_handler)
        
        # 检查处理器是否注册成功
        handlers = self.trigger_system._handler.list_handlers()
        self.assertIn("state", handlers)
        self.assertEqual(handlers["state"], 1)
        
        # 注销事件处理器
        result = self.trigger_system.unregister_event_handler(TriggerType.STATE, test_handler)
        self.assertTrue(result)
        
        # 检查处理器是否注销成功
        handlers = self.trigger_system._handler.list_handlers()
        self.assertEqual(handlers.get("state", 0), 0)
        
        # 尝试注销不存在的处理器
        result = self.trigger_system.unregister_event_handler(TriggerType.STATE, test_handler)
        self.assertFalse(result)

    def test_trigger_system_event_history(self):
        """测试事件历史记录"""
        # 创建测试数据
        state = AgentState(agent_id="test-agent")
        context = {"test": "context"}
        
        # 注册触发器并触发事件
        trigger = MockTrigger("history-trigger")
        self.trigger_system.register_trigger(trigger)
        
        # 评估触发器产生事件
        events = self.trigger_system.evaluate_triggers(state, context)
        self.assertEqual(len(events), 1)
        
        # 检查事件历史
        history = self.trigger_system.get_event_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].trigger_id, "history-trigger")
        
        # 限制历史记录数量
        limited_history = self.trigger_system.get_event_history(limit=1)
        self.assertEqual(len(limited_history), 1)
        
        # 清除历史记录
        self.trigger_system.clear_event_history()
        history = self.trigger_system.get_event_history()
        self.assertEqual(len(history), 0)

    def test_trigger_system_event_history_size_limit(self):
        """测试事件历史记录大小限制"""
        # 创建测试数据
        state = AgentState(agent_id="test-agent")
        context = {"test": "context"}
        
        # 注册多个触发器并触发事件
        for i in range(1005):  # 超过默认的1000限制
            trigger = MockTrigger(f"trigger-{i}")
            self.trigger_system.register_trigger(trigger)
        
        # 评估所有触发器
        events = self.trigger_system.evaluate_triggers(state, context)
        self.assertEqual(len(events), 1005)
        
        # 检查历史记录大小限制
        history = self.trigger_system.get_event_history()
        self.assertEqual(len(history), 1000)  # 应该限制在1000条
        self.assertEqual(history[0].trigger_id, "trigger-5")  # 最旧的应该被移除

    def test_trigger_system_get_system_stats(self):
        """测试获取系统统计信息"""
        # 注册不同类型的触发器
        trigger1 = MockTrigger("trigger-1", TriggerType.STATE)
        trigger2 = MockTrigger("trigger-2", TriggerType.TIME, enabled=False)
        trigger3 = MockTrigger("trigger-3", TriggerType.EVENT)
        trigger4 = MockTrigger("trigger-4", TriggerType.CUSTOM)
        
        self.trigger_system.register_trigger(trigger1)
        self.trigger_system.register_trigger(trigger2)
        self.trigger_system.register_trigger(trigger3)
        self.trigger_system.register_trigger(trigger4)
        
        # 触发一些事件
        state = AgentState(agent_id="test-agent")
        context = {"test": "context"}
        events = self.trigger_system.evaluate_triggers(state, context)
        
        # 获取统计信息
        stats = self.trigger_system.get_system_stats()
        
        # 检查统计信息
        self.assertFalse(stats["system_running"])
        self.assertEqual(stats["total_triggers"], 4)
        self.assertEqual(stats["enabled_triggers"], 3)  # trigger2是禁用的
        self.assertEqual(stats["total_events"], 3)  # 3个触发器被触发
        
        # 检查触发器类型统计
        trigger_types = stats["trigger_types"]
        self.assertEqual(trigger_types["state"]["total"], 1)
        self.assertEqual(trigger_types["state"]["enabled"], 1)
        self.assertEqual(trigger_types["time"]["total"], 1)
        self.assertEqual(trigger_types["time"]["enabled"], 0)
        self.assertEqual(trigger_types["event"]["total"], 1)
        self.assertEqual(trigger_types["event"]["enabled"], 1)
        self.assertEqual(trigger_types["custom"]["total"], 1)
        self.assertEqual(trigger_types["custom"]["enabled"], 1)
        
        # 检查事件类型统计
        event_types = stats["event_types"]
        self.assertEqual(event_types["custom"], 3)  # 所有触发器都是CUSTOM类型
        
        # 检查处理器统计
        handlers = stats["handlers"]
        self.assertEqual(handlers, {})

    def test_trigger_system_context_manager(self):
        """测试上下文管理器"""
        # 使用上下文管理器
        with TriggerSystem() as system:
            self.assertTrue(system.is_running())
        
        # 退出上下文后应该停止
        self.assertFalse(system.is_running())

    def test_trigger_system_thread_safety(self):
        """测试线程安全性"""
        # 这个测试比较复杂，我们简单测试一下并发注册触发器
        def register_triggers(trigger_system, start_event, trigger_prefix, count):
            start_event.wait()  # 等待开始信号
            for i in range(count):
                trigger = MockTrigger(f"{trigger_prefix}-{i}")
                trigger_system.register_trigger(trigger)
        
        # 创建事件用于同步
        start_event = threading.Event()
        
        # 创建多个线程同时注册触发器
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=register_triggers,
                args=(self.trigger_system, start_event, f"thread-{i}", 10)
            )
            threads.append(thread)
            thread.start()
        
        # 启动所有线程
        start_event.set()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        self.assertEqual(len(self.trigger_system._triggers), 50)


class TestWorkflowTriggerSystem(unittest.TestCase):
    """测试工作流触发器系统"""

    def setUp(self):
        """测试前准备"""
        self.workflow_manager = Mock()
        self.workflow_trigger_system = WorkflowTriggerSystem(
            workflow_manager=self.workflow_manager,
            max_workers=2
        )

    def test_workflow_trigger_system_initialization(self):
        """测试工作流触发器系统初始化"""
        self.assertEqual(self.workflow_trigger_system.workflow_manager, self.workflow_manager)
        self.assertEqual(self.workflow_trigger_system._executor._max_workers, 2)

    def test_workflow_trigger_system_evaluate_workflow_triggers(self):
        """测试评估工作流触发器"""
        # 创建测试数据
        workflow_id = "test-workflow-1"
        state = AgentState(agent_id="test-agent")
        
        # 注册触发器
        trigger = MockTrigger("workflow-trigger-1")
        self.workflow_trigger_system.register_trigger(trigger)
        
        # 评估工作流触发器
        events = self.workflow_trigger_system.evaluate_workflow_triggers(workflow_id, state)
        
        # 检查结果
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].trigger_id, "workflow-trigger-1")
        
        # 检查上下文是否正确传递
        self.assertTrue(trigger.evaluate_called)
        self.assertTrue(trigger.execute_called)

    def test_workflow_trigger_system_register_workflow_trigger(self):
        """测试注册工作流触发器"""
        workflow_id = "test-workflow-1"
        trigger = MockTrigger("workflow-trigger-1")
        
        # 注册工作流触发器
        result = self.workflow_trigger_system.register_workflow_trigger(workflow_id, trigger)
        self.assertTrue(result)
        self.assertIn("workflow-trigger-1", self.workflow_trigger_system._triggers)
        
        # 检查配置是否更新
        config = trigger.get_config()
        self.assertEqual(config["workflow_id"], workflow_id)

    def test_workflow_trigger_system_unregister_workflow_trigger(self):
        """测试注销工作流触发器"""
        workflow_id = "test-workflow-1"
        trigger = MockTrigger("workflow-trigger-1")
        
        # 注册触发器
        self.workflow_trigger_system.register_trigger(trigger)
        
        # 为触发器添加工作流ID
        config = trigger.get_config()
        config["workflow_id"] = workflow_id
        
        # 注销工作流触发器
        result = self.workflow_trigger_system.unregister_workflow_trigger(workflow_id, "workflow-trigger-1")
        self.assertTrue(result)
        self.assertNotIn("workflow-trigger-1", self.workflow_trigger_system._triggers)
        
        # 尝试注销不匹配的工作流ID
        trigger2 = MockTrigger("workflow-trigger-2")
        self.workflow_trigger_system.register_trigger(trigger2)
        config2 = trigger2.get_config()
        config2["workflow_id"] = "different-workflow"
        
        result = self.workflow_trigger_system.unregister_workflow_trigger(workflow_id, "workflow-trigger-2")
        self.assertFalse(result)  # 应该失败，因为工作流ID不匹配

    def test_workflow_trigger_system_get_workflow_triggers(self):
        """测试获取工作流触发器"""
        workflow_id1 = "workflow-1"
        workflow_id2 = "workflow-2"
        
        # 注册不同工作流的触发器
        trigger1 = MockTrigger("trigger-1")
        trigger2 = MockTrigger("trigger-2")
        trigger3 = MockTrigger("trigger-3")
        
        self.workflow_trigger_system.register_trigger(trigger1)
        self.workflow_trigger_system.register_trigger(trigger2)
        self.workflow_trigger_system.register_trigger(trigger3)
        
        # 为触发器设置工作流ID
        trigger1.get_config()["workflow_id"] = workflow_id1
        trigger2.get_config()["workflow_id"] = workflow_id1
        trigger3.get_config()["workflow_id"] = workflow_id2
        
        # 获取特定工作流的触发器
        workflow1_triggers = self.workflow_trigger_system.get_workflow_triggers(workflow_id1)
        workflow2_triggers = self.workflow_trigger_system.get_workflow_triggers(workflow_id2)
        
        # 检查结果
        self.assertEqual(len(workflow1_triggers), 2)
        self.assertEqual(len(workflow2_triggers), 1)
        
        workflow1_ids = [t["id"] for t in workflow1_triggers]
        self.assertIn("trigger-1", workflow1_ids)
        self.assertIn("trigger-2", workflow1_ids)
        
        workflow2_ids = [t["id"] for t in workflow2_triggers]
        self.assertIn("trigger-3", workflow2_ids)


if __name__ == '__main__':
    unittest.main()