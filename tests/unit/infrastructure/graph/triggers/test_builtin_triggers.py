"""内置触发器单元测试

测试各种内置触发器的功能，包括：
1. 时间触发器
2. 状态触发器
3. 事件触发器
4. 自定义触发器
5. 工具错误触发器
6. 迭代限制触发器
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import re

from src.infrastructure.graph.triggers.builtin_triggers import (
    TimeTrigger, StateTrigger, EventTrigger, CustomTrigger, 
    ToolErrorTrigger, IterationLimitTrigger
)
from src.infrastructure.graph.triggers.base import TriggerType
from src.domain.agent.state import AgentState, AgentStatus, AgentMessage
from src.domain.tools.interfaces import ToolResult


class TestTimeTrigger(unittest.TestCase):
    """测试时间触发器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "time-trigger-1"
        self.trigger_time = "14:30"  # 14:30
        self.config = {"rate_limit": 60.0}  # 1分钟速率限制
        self.time_trigger = TimeTrigger(
            trigger_id=self.trigger_id,
            trigger_time=self.trigger_time,
            config=self.config
        )

    def test_time_trigger_initialization(self):
        """测试时间触发器初始化"""
        self.assertEqual(self.time_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.time_trigger.trigger_type, TriggerType.TIME)
        self.assertEqual(self.time_trigger._trigger_time, self.trigger_time)
        self.assertIsNotNone(self.time_trigger._next_trigger)
        self.assertEqual(self.time_trigger.get_config()["rate_limit"], 60.0)

    def test_time_trigger_interval_initialization(self):
        """测试间隔时间触发器初始化"""
        interval_trigger = TimeTrigger(
            trigger_id="interval-trigger",
            trigger_time="300",  # 5分钟间隔
            config={}
        )
        
        self.assertEqual(interval_trigger.trigger_type, TriggerType.TIME)
        self.assertEqual(interval_trigger._trigger_time, "300")
        self.assertIsNotNone(interval_trigger._next_trigger)

    def test_time_trigger_evaluate_not_triggered(self):
        """测试时间触发器未触发情况"""
        state = AgentState()
        context = {}
        
        # 默认情况下不应该触发
        result = self.time_trigger.evaluate(state, context)
        self.assertFalse(result)

    def test_time_trigger_evaluate_triggered(self):
        """测试时间触发器触发情况"""
        state = AgentState()
        context = {}
        
        # 模拟时间已到触发时间
        with patch.object(self.time_trigger, '_next_trigger', datetime.now() - timedelta(minutes=1)):
            result = self.time_trigger.evaluate(state, context)
            self.assertTrue(result)

    def test_time_trigger_execute(self):
        """测试时间触发器执行"""
        state = AgentState()
        context = {}
        
        before_time = datetime.now()
        result = self.time_trigger.execute(state, context)
        after_time = datetime.now()
        
        # 检查执行结果
        self.assertEqual(result["trigger_time"], self.trigger_time)
        self.assertEqual(result["message"], f"时间触发器 {self.trigger_id} 执行")
        self.assertGreaterEqual(datetime.fromisoformat(result["executed_at"]), before_time)
        self.assertLessEqual(datetime.fromisoformat(result["executed_at"]), after_time)
        
        # 检查触发信息是否更新
        self.assertIsNotNone(self.time_trigger.get_last_triggered())
        self.assertEqual(self.time_trigger.get_trigger_count(), 1)

    def test_time_trigger_get_config(self):
        """测试时间触发器配置获取"""
        config = self.time_trigger.get_config()
        self.assertEqual(config["trigger_time"], self.trigger_time)
        self.assertIsNotNone(config["next_trigger"])

    def test_time_trigger_calculate_next_trigger_interval(self):
        """测试间隔时间触发器下次触发时间计算"""
        interval_trigger = TimeTrigger(
            trigger_id="interval-trigger",
            trigger_time="60",  # 1分钟间隔
            config={}
        )
        
        initial_next = interval_trigger._next_trigger
        self.assertIsNotNone(initial_next)
        
        # 执行一次触发器
        interval_trigger.execute(AgentState(), {})
        
        # 检查下次触发时间是否更新
        self.assertGreater(interval_trigger._next_trigger, initial_next)

    def test_time_trigger_calculate_next_trigger_time_format(self):
        """测试时间格式触发器下次触发时间计算"""
        time_trigger = TimeTrigger(
            trigger_id="time-format-trigger",
            trigger_time="23:59",  # 很晚的时间
            config={}
        )
        
        now = datetime.now()
        next_trigger = time_trigger._next_trigger
        
        # 检查下次触发时间是否在今天或明天
        self.assertGreaterEqual(next_trigger.date(), now.date())
        self.assertLessEqual(next_trigger.date(), now.date() + timedelta(days=1))


class TestStateTrigger(unittest.TestCase):
    """测试状态触发器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "state-trigger-1"
        self.condition = "len(state.messages) > 2"
        self.config = {"rate_limit": 10.0}
        self.state_trigger = StateTrigger(
            trigger_id=self.trigger_id,
            condition=self.condition,
            config=self.config
        )

    def test_state_trigger_initialization(self):
        """测试状态触发器初始化"""
        self.assertEqual(self.state_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.state_trigger.trigger_type, TriggerType.STATE)
        self.assertEqual(self.state_trigger._condition, self.condition)
        self.assertEqual(self.state_trigger.get_config()["rate_limit"], 10.0)

    def test_state_trigger_evaluate_true(self):
        """测试状态触发器评估为真"""
        state = AgentState(
            messages=[
                AgentMessage(content="msg1", role="user"),
                AgentMessage(content="msg2", role="assistant"),
                AgentMessage(content="msg3", role="user")
            ]
        )
        context = {}
        
        result = self.state_trigger.evaluate(state, context)
        self.assertTrue(result)

    def test_state_trigger_evaluate_false(self):
        """测试状态触发器评估为假"""
        state = AgentState(
            messages=[
                AgentMessage(content="msg1", role="user")
            ]
        )
        context = {}
        
        result = self.state_trigger.evaluate(state, context)
        self.assertFalse(result)

    def test_state_trigger_evaluate_with_context(self):
        """测试状态触发器使用上下文评估"""
        condition = "context.get('test_key') == 'test_value'"
        trigger = StateTrigger(
            trigger_id="context-trigger",
            condition=condition,
            config={}
        )
        
        state = AgentState()
        context = {"test_key": "test_value"}
        
        result = trigger.evaluate(state, context)
        self.assertTrue(result)

    def test_state_trigger_evaluate_exception(self):
        """测试状态触发器评估异常情况"""
        condition = "invalid_syntax["
        trigger = StateTrigger(
            trigger_id="error-trigger",
            condition=condition,
            config={}
        )
        
        state = AgentState()
        context = {}
        
        result = trigger.evaluate(state, context)
        self.assertFalse(result)  # 异常应该返回False

    def test_state_trigger_execute(self):
        """测试状态触发器执行"""
        state = AgentState(
            messages=[
                AgentMessage(content="msg1", role="user"),
                AgentMessage(content="msg2", role="assistant")
            ],
            tool_results=[
                ToolResult(success=True, output="result1"),
                ToolResult(success=False, error="error1")
            ],
            current_step="test_step",
            iteration_count=3
        )
        context = {}
        
        before_time = datetime.now()
        result = self.state_trigger.execute(state, context)
        after_time = datetime.now()
        
        # 检查执行结果
        self.assertEqual(result["condition"], self.condition)
        self.assertEqual(result["message"], f"状态触发器 {self.trigger_id} 执行")
        self.assertGreaterEqual(datetime.fromisoformat(result["executed_at"]), before_time)
        self.assertLessEqual(datetime.fromisoformat(result["executed_at"]), after_time)
        
        # 检查状态摘要
        state_summary = result["state_summary"]
        self.assertEqual(state_summary["messages_count"], 2)
        self.assertEqual(state_summary["tool_results_count"], 2)
        self.assertEqual(state_summary["current_step"], "test_step")
        self.assertEqual(state_summary["iteration_count"], 3)
        
        # 检查触发信息是否更新
        self.assertIsNotNone(self.state_trigger.get_last_triggered())
        self.assertEqual(self.state_trigger.get_trigger_count(), 1)

    def test_state_trigger_get_config(self):
        """测试状态触发器配置获取"""
        config = self.state_trigger.get_config()
        self.assertEqual(config["condition"], self.condition)


class TestEventTrigger(unittest.TestCase):
    """测试事件触发器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "event-trigger-1"
        self.event_type = "user_action"
        self.event_pattern = r"click.*button"
        self.config = {"rate_limit": 5.0}
        self.event_trigger = EventTrigger(
            trigger_id=self.trigger_id,
            event_type=self.event_type,
            event_pattern=self.event_pattern,
            config=self.config
        )

    def test_event_trigger_initialization(self):
        """测试事件触发器初始化"""
        self.assertEqual(self.event_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.event_trigger.trigger_type, TriggerType.EVENT)
        self.assertEqual(self.event_trigger._event_type, self.event_type)
        self.assertEqual(self.event_trigger._event_pattern, self.event_pattern)
        self.assertIsNotNone(self.event_trigger._compiled_pattern)
        self.assertEqual(self.event_trigger.get_config()["rate_limit"], 5.0)

    def test_event_trigger_without_pattern(self):
        """测试无模式的事件触发器"""
        trigger = EventTrigger(
            trigger_id="no-pattern-trigger",
            event_type="test_event",
            event_pattern=None,
            config={}
        )
        
        self.assertIsNone(trigger._event_pattern)
        self.assertIsNone(trigger._compiled_pattern)

    def test_event_trigger_evaluate_match_type(self):
        """测试事件触发器匹配事件类型"""
        state = AgentState()
        context = {
            "events": [
                {"type": "user_action", "data": "click save button"},
                {"type": "system_event", "data": "startup"}
            ]
        }
        
        # 创建无模式的触发器
        trigger = EventTrigger(
            trigger_id="type-match-trigger",
            event_type="user_action",
            event_pattern=None,
            config={}
        )
        
        result = trigger.evaluate(state, context)
        self.assertTrue(result)

    def test_event_trigger_evaluate_match_pattern(self):
        """测试事件触发器匹配事件模式"""
        state = AgentState()
        context = {
            "events": [
                {"type": "user_action", "data": "click save button"},
                {"type": "user_action", "data": "scroll down"}
            ]
        }
        
        result = self.event_trigger.evaluate(state, context)
        self.assertTrue(result)

    def test_event_trigger_evaluate_no_match(self):
        """测试事件触发器无匹配"""
        state = AgentState()
        context = {
            "events": [
                {"type": "system_event", "data": "startup"},
                {"type": "user_action", "data": "scroll down"}
            ]
        }
        
        result = self.event_trigger.evaluate(state, context)
        self.assertFalse(result)

    def test_event_trigger_evaluate_no_events(self):
        """测试事件触发器无事件情况"""
        state = AgentState()
        context = {}
        
        result = self.event_trigger.evaluate(state, context)
        self.assertFalse(result)

    def test_event_trigger_execute(self):
        """测试事件触发器执行"""
        state = AgentState()
        context = {
            "events": [
                {"type": "user_action", "data": "click save button"},
                {"type": "user_action", "data": "click delete button"},
                {"type": "system_event", "data": "startup"}
            ]
        }
        
        before_time = datetime.now()
        result = self.event_trigger.execute(state, context)
        after_time = datetime.now()
        
        # 检查执行结果
        self.assertEqual(result["event_type"], self.event_type)
        self.assertEqual(result["event_pattern"], self.event_pattern)
        self.assertEqual(result["message"], f"事件触发器 {self.trigger_id} 执行")
        self.assertGreaterEqual(datetime.fromisoformat(result["executed_at"]), before_time)
        self.assertLessEqual(datetime.fromisoformat(result["executed_at"]), after_time)
        
        # 检查匹配的事件
        matching_events = result["matching_events"]
        self.assertEqual(len(matching_events), 2)
        self.assertEqual(matching_events[0]["type"], "user_action")
        self.assertEqual(matching_events[0]["data"], "click save button")
        self.assertEqual(matching_events[1]["type"], "user_action")
        self.assertEqual(matching_events[1]["data"], "click delete button")
        
        # 检查触发信息是否更新
        self.assertIsNotNone(self.event_trigger.get_last_triggered())
        self.assertEqual(self.event_trigger.get_trigger_count(), 1)

    def test_event_trigger_get_config(self):
        """测试事件触发器配置获取"""
        config = self.event_trigger.get_config()
        self.assertEqual(config["event_type"], self.event_type)
        self.assertEqual(config["event_pattern"], self.event_pattern)


class TestCustomTrigger(unittest.TestCase):
    """测试自定义触发器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "custom-trigger-1"
        self.config = {"custom_field": "value"}
        
        # 定义评估和执行函数
        def evaluate_func(state: AgentState, context: dict) -> bool:
            return len(state.messages) > 0
        
        def execute_func(state: AgentState, context: dict) -> dict:
            return {
                "message": "Custom trigger executed",
                "message_count": len(state.messages)
            }
        
        self.evaluate_func = evaluate_func
        self.execute_func = execute_func
        
        self.custom_trigger = CustomTrigger(
            trigger_id=self.trigger_id,
            evaluate_func=self.evaluate_func,
            execute_func=self.execute_func,
            config=self.config
        )

    def test_custom_trigger_initialization(self):
        """测试自定义触发器初始化"""
        self.assertEqual(self.custom_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.custom_trigger.trigger_type, TriggerType.CUSTOM)
        self.assertEqual(self.custom_trigger._evaluate_func, self.evaluate_func)
        self.assertEqual(self.custom_trigger._execute_func, self.execute_func)
        self.assertEqual(self.custom_trigger.get_config()["custom_field"], "value")

    def test_custom_trigger_evaluate_true(self):
        """测试自定义触发器评估为真"""
        state = AgentState(
            messages=[AgentMessage(content="test", role="user")]
        )
        context = {}
        
        result = self.custom_trigger.evaluate(state, context)
        self.assertTrue(result)

    def test_custom_trigger_evaluate_false(self):
        """测试自定义触发器评估为假"""
        state = AgentState()
        context = {}
        
        result = self.custom_trigger.evaluate(state, context)
        self.assertFalse(result)

    def test_custom_trigger_evaluate_exception(self):
        """测试自定义触发器评估异常"""
        def error_evaluate_func(state: AgentState, context: dict) -> bool:
            raise Exception("Test error")
        
        trigger = CustomTrigger(
            trigger_id="error-trigger",
            evaluate_func=error_evaluate_func,
            execute_func=self.execute_func,
            config={}
        )
        
        state = AgentState()
        context = {}
        
        result = trigger.evaluate(state, context)
        self.assertFalse(result)

    def test_custom_trigger_execute(self):
        """测试自定义触发器执行"""
        state = AgentState(
            messages=[
                AgentMessage(content="msg1", role="user"),
                AgentMessage(content="msg2", role="assistant")
            ]
        )
        context = {}
        
        before_time = datetime.now()
        result = self.custom_trigger.execute(state, context)
        after_time = datetime.now()
        
        # 检查执行结果
        self.assertEqual(result["message"], "Custom trigger executed")
        self.assertEqual(result["message_count"], 2)
        self.assertEqual(result["trigger_id"], self.trigger_id)
        self.assertGreaterEqual(datetime.fromisoformat(result["executed_at"]), before_time)
        self.assertLessEqual(datetime.fromisoformat(result["executed_at"]), after_time)
        
        # 检查触发信息是否更新
        self.assertIsNotNone(self.custom_trigger.get_last_triggered())
        self.assertEqual(self.custom_trigger.get_trigger_count(), 1)

    def test_custom_trigger_execute_exception(self):
        """测试自定义触发器执行异常"""
        def error_execute_func(state: AgentState, context: dict) -> dict:
            raise Exception("Execution error")
        
        trigger = CustomTrigger(
            trigger_id="error-execute-trigger",
            evaluate_func=self.evaluate_func,
            execute_func=error_execute_func,
            config={}
        )
        
        state = AgentState()
        context = {}
        
        before_time = datetime.now()
        result = trigger.execute(state, context)
        after_time = datetime.now()
        
        # 检查错误处理结果
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Execution error")
        self.assertEqual(result["trigger_id"], "error-execute-trigger")
        self.assertIn("执行时出错", result["message"])
        self.assertGreaterEqual(datetime.fromisoformat(result["executed_at"]), before_time)
        self.assertLessEqual(datetime.fromisoformat(result["executed_at"]), after_time)


class TestToolErrorTrigger(unittest.TestCase):
    """测试工具错误触发器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "tool-error-trigger-1"
        self.error_threshold = 2
        self.config = {"rate_limit": 30.0}
        self.tool_error_trigger = ToolErrorTrigger(
            trigger_id=self.trigger_id,
            error_threshold=self.error_threshold,
            config=self.config
        )

    def test_tool_error_trigger_initialization(self):
        """测试工具错误触发器初始化"""
        self.assertEqual(self.tool_error_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.tool_error_trigger.trigger_type, TriggerType.CUSTOM)
        self.assertEqual(self.tool_error_trigger._error_threshold, self.error_threshold)
        self.assertEqual(self.tool_error_trigger.get_config()["rate_limit"], 30.0)

    def test_tool_error_trigger_evaluate_below_threshold(self):
        """测试工具错误触发器低于阈值"""
        state = AgentState(
            tool_results=[
                ToolResult(success=True, output="result1"),
                ToolResult(success=False, error="error1", tool_name="tool1"),
                ToolResult(success=True, output="result2")
            ]
        )
        context = {}
        
        result = self.tool_error_trigger.evaluate(state, context)
        self.assertFalse(result)  # 只有1个错误，低于阈值2

    def test_tool_error_trigger_evaluate_at_threshold(self):
        """测试工具错误触发器达到阈值"""
        state = AgentState(
            tool_results=[
                ToolResult(success=False, error="error1", tool_name="tool1"),
                ToolResult(success=False, error="error2", tool_name="tool2")
            ]
        )
        context = {}
        
        result = self.tool_error_trigger.evaluate(state, context)
        self.assertTrue(result)  # 2个错误，达到阈值

    def test_tool_error_trigger_evaluate_above_threshold(self):
        """测试工具错误触发器超过阈值"""
        state = AgentState(
            tool_results=[
                ToolResult(success=False, error="error1", tool_name="tool1"),
                ToolResult(success=False, error="error2", tool_name="tool1"),
                ToolResult(success=False, error="error3", tool_name="tool2")
            ]
        )
        context = {}
        
        result = self.tool_error_trigger.evaluate(state, context)
        self.assertTrue(result)  # 3个错误，超过阈值

    def test_tool_error_trigger_evaluate_no_errors(self):
        """测试工具错误触发器无错误"""
        state = AgentState(
            tool_results=[
                ToolResult(success=True, output="result1"),
                ToolResult(success=True, output="result2")
            ]
        )
        context = {}
        
        result = self.tool_error_trigger.evaluate(state, context)
        self.assertFalse(result)  # 无错误

    def test_tool_error_trigger_execute(self):
        """测试工具错误触发器执行"""
        state = AgentState(
            tool_results=[
                ToolResult(success=True, output="result1"),
                ToolResult(success=False, error="error1", tool_name="tool1"),
                ToolResult(success=False, error="error2", tool_name="tool1"),
                ToolResult(success=False, error="error3", tool_name="tool2")
            ]
        )
        context = {}
        
        before_time = datetime.now()
        result = self.tool_error_trigger.execute(state, context)
        after_time = datetime.now()
        
        # 检查执行结果
        self.assertEqual(result["error_threshold"], self.error_threshold)
        self.assertEqual(result["error_count"], 3)
        self.assertEqual(result["message"], f"工具错误触发器 {self.trigger_id} 执行")
        self.assertGreaterEqual(datetime.fromisoformat(result["executed_at"]), before_time)
        self.assertLessEqual(datetime.fromisoformat(result["executed_at"]), after_time)
        
        # 检查错误摘要
        error_summary = result["error_summary"]
        self.assertIn("tool1", error_summary)
        self.assertIn("tool2", error_summary)
        self.assertEqual(error_summary["tool1"]["count"], 2)
        self.assertEqual(len(error_summary["tool1"]["errors"]), 2)
        self.assertEqual(error_summary["tool2"]["count"], 1)
        self.assertEqual(len(error_summary["tool2"]["errors"]), 1)
        
        # 检查触发信息是否更新
        self.assertIsNotNone(self.tool_error_trigger.get_last_triggered())
        self.assertEqual(self.tool_error_trigger.get_trigger_count(), 1)

    def test_tool_error_trigger_get_config(self):
        """测试工具错误触发器配置获取"""
        config = self.tool_error_trigger.get_config()
        self.assertEqual(config["error_threshold"], self.error_threshold)


class TestIterationLimitTrigger(unittest.TestCase):
    """测试迭代限制触发器"""

    def setUp(self):
        """测试前准备"""
        self.trigger_id = "iteration-trigger-1"
        self.max_iterations = 5
        self.config = {"rate_limit": 15.0}
        self.iteration_trigger = IterationLimitTrigger(
            trigger_id=self.trigger_id,
            max_iterations=self.max_iterations,
            config=self.config
        )

    def test_iteration_trigger_initialization(self):
        """测试迭代限制触发器初始化"""
        self.assertEqual(self.iteration_trigger.trigger_id, self.trigger_id)
        self.assertEqual(self.iteration_trigger.trigger_type, TriggerType.CUSTOM)
        self.assertEqual(self.iteration_trigger._max_iterations, self.max_iterations)
        self.assertEqual(self.iteration_trigger.get_config()["rate_limit"], 15.0)

    def test_iteration_trigger_evaluate_below_limit(self):
        """测试迭代限制触发器低于限制"""
        state = AgentState(iteration_count=3)
        context = {}
        
        result = self.iteration_trigger.evaluate(state, context)
        self.assertFalse(result)  # 3次迭代，低于限制5次

    def test_iteration_trigger_evaluate_at_limit(self):
        """测试迭代限制触发器达到限制"""
        state = AgentState(iteration_count=5)
        context = {}
        
        result = self.iteration_trigger.evaluate(state, context)
        self.assertTrue(result)  # 5次迭代，达到限制

    def test_iteration_trigger_evaluate_above_limit(self):
        """测试迭代限制触发器超过限制"""
        state = AgentState(iteration_count=10)
        context = {}
        
        result = self.iteration_trigger.evaluate(state, context)
        self.assertTrue(result)  # 10次迭代，超过限制

    def test_iteration_trigger_evaluate_no_iteration_count(self):
        """测试迭代限制触发器无迭代计数"""
        state = AgentState()  # 没有设置iteration_count，默认为0
        context = {}
        
        result = self.iteration_trigger.evaluate(state, context)
        self.assertFalse(result)  # 0次迭代，低于限制

    def test_iteration_trigger_execute(self):
        """测试迭代限制触发器执行"""
        state = AgentState(iteration_count=7)
        context = {}
        
        before_time = datetime.now()
        result = self.iteration_trigger.execute(state, context)
        after_time = datetime.now()
        
        # 检查执行结果
        self.assertEqual(result["max_iterations"], self.max_iterations)
        self.assertEqual(result["current_iterations"], 7)
        self.assertEqual(result["message"], f"迭代限制触发器 {self.trigger_id} 执行")
        self.assertGreaterEqual(datetime.fromisoformat(result["executed_at"]), before_time)
        self.assertLessEqual(datetime.fromisoformat(result["executed_at"]), after_time)
        
        # 检查触发信息是否更新
        self.assertIsNotNone(self.iteration_trigger.get_last_triggered())
        self.assertEqual(self.iteration_trigger.get_trigger_count(), 1)

    def test_iteration_trigger_get_config(self):
        """测试迭代限制触发器配置获取"""
        config = self.iteration_trigger.get_config()
        self.assertEqual(config["max_iterations"], self.max_iterations)


if __name__ == '__main__':
    unittest.main()