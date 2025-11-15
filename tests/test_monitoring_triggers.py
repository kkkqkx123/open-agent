"""监控触发器测试

测试各种监控触发器的功能。
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.infrastructure.graph.triggers.timing import (
    ToolExecutionTimingTrigger,
    LLMResponseTimingTrigger,
    WorkflowStateTimingTrigger
)
from src.infrastructure.graph.triggers.state_monitoring import (
    WorkflowStateCaptureTrigger,
    WorkflowStateChangeTrigger,
    WorkflowErrorStateTrigger
)
from src.infrastructure.graph.triggers.pattern_matching import (
    UserInputPatternTrigger,
    LLMOutputPatternTrigger
)
from src.infrastructure.graph.triggers.system_monitoring import (
    MemoryMonitoringTrigger
)
from src.infrastructure.graph.triggers.factory import TriggerFactory
from src.infrastructure.graph.triggers.base import TriggerType


class TestToolExecutionTimingTrigger:
    """测试工具执行计时触发器"""
    
    def test_evaluate_with_timeout(self):
        """测试超时情况下的评估"""
        trigger = ToolExecutionTimingTrigger("test_tool_timing", {
            "timeout_threshold": 5.0,
            "warning_threshold": 2.0
        })
        
        state = {
            "tool_results": [
                {
                    "tool_name": "test_tool",
                    "execution_time": 6.0,
                    "success": True
                }
            ]
        }
        
        context = {}
        
        assert trigger.evaluate(state, context) == True
    
    def test_evaluate_without_timeout(self):
        """测试未超时情况下的评估"""
        trigger = ToolExecutionTimingTrigger("test_tool_timing", {
            "timeout_threshold": 5.0,
            "warning_threshold": 2.0
        })
        
        state = {
            "tool_results": [
                {
                    "tool_name": "test_tool",
                    "execution_time": 3.0,
                    "success": True
                }
            ]
        }
        
        context = {}
        
        assert trigger.evaluate(state, context) == False
    
    def test_execute(self):
        """测试执行功能"""
        trigger = ToolExecutionTimingTrigger("test_tool_timing", {
            "timeout_threshold": 5.0,
            "warning_threshold": 2.0
        })
        
        state = {
            "tool_results": [
                {
                    "tool_name": "test_tool",
                    "execution_time": 6.0,
                    "success": True
                }
            ]
        }
        
        context = {}
        
        result = trigger.execute(state, context)
        
        assert result["tool_name"] == "test_tool"
        assert result["execution_time"] == 6.0
        assert result["warning_level"] == "timeout"
        assert "executed_at" in result


class TestLLMResponseTimingTrigger:
    """测试LLM响应计时触发器"""
    
    def test_evaluate_with_timeout(self):
        """测试超时情况下的评估"""
        trigger = LLMResponseTimingTrigger("test_llm_timing", {
            "timeout_threshold": 30.0,
            "warning_threshold": 10.0
        })
        
        state = {
            "messages": [
                {
                    "role": "assistant",
                    "model": "gpt-4",
                    "content": "Test response",
                    "response_time": 35.0
                }
            ]
        }
        
        context = {}
        
        assert trigger.evaluate(state, context) == True
    
    def test_evaluate_without_timeout(self):
        """测试未超时情况下的评估"""
        trigger = LLMResponseTimingTrigger("test_llm_timing", {
            "timeout_threshold": 30.0,
            "warning_threshold": 10.0
        })
        
        state = {
            "messages": [
                {
                    "role": "assistant",
                    "model": "gpt-4",
                    "content": "Test response",
                    "response_time": 15.0
                }
            ]
        }
        
        context = {}
        
        assert trigger.evaluate(state, context) == False
    
    def test_execute(self):
        """测试执行功能"""
        trigger = LLMResponseTimingTrigger("test_llm_timing", {
            "timeout_threshold": 30.0,
            "warning_threshold": 10.0
        })
        
        state = {
            "messages": [
                {
                    "role": "assistant",
                    "model": "gpt-4",
                    "content": "Test response",
                    "response_time": 35.0
                }
            ]
        }
        
        context = {}
        
        result = trigger.execute(state, context)
        
        assert result["model"] == "gpt-4"
        assert result["response_time"] == 35.0
        assert result["warning_level"] == "timeout"
        assert "executed_at" in result


class TestWorkflowStateTimingTrigger:
    """测试工作流状态计时触发器"""
    
    def test_evaluate_with_stall(self):
        """测试停滞情况下的评估"""
        trigger = WorkflowStateTimingTrigger("test_state_timing", {
            "stall_threshold": 60.0,
            "warning_threshold": 30.0
        })
        
        # 模拟状态变更
        trigger.update_state("test_state", {})
        
        # 模拟时间流逝
        with patch('src.infrastructure.graph.triggers.monitoring_base.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now()
            trigger.update_state("test_state", {})
            
            # 模拟70秒后
            mock_datetime.now.return_value = datetime.now()
            with patch.object(trigger, 'get_time_since_last_state_change', return_value=70.0):
                state = {"current_step": "test_state"}
                context = {}
                
                assert trigger.evaluate(state, context) == True
    
    def test_execute(self):
        """测试执行功能"""
        trigger = WorkflowStateTimingTrigger("test_state_timing", {
            "stall_threshold": 60.0,
            "warning_threshold": 30.0
        })
        
        trigger.update_state("test_state", {})
        
        with patch.object(trigger, 'get_time_since_last_state_change', return_value=70.0):
            state = {"current_step": "test_state"}
            context = {}
            
            result = trigger.execute(state, context)
            
            assert result["current_state"] == "test_state"
            assert result["time_in_state"] == 70.0
            assert result["warning_level"] == "stall"
            assert "executed_at" in result


class TestUserInputPatternTrigger:
    """测试用户输入模式匹配触发器"""
    
    def test_evaluate_with_match(self):
        """测试匹配情况下的评估"""
        trigger = UserInputPatternTrigger("test_user_pattern", {
            "patterns": {
                "urgent": r"(?i)(urgent|asap)"
            }
        })
        
        state = {
            "messages": [
                {
                    "role": "user",
                    "content": "This is urgent!"
                }
            ]
        }
        
        context = {}
        
        assert trigger.evaluate(state, context) == True
    
    def test_evaluate_without_match(self):
        """测试不匹配情况下的评估"""
        trigger = UserInputPatternTrigger("test_user_pattern", {
            "patterns": {
                "urgent": r"(?i)(urgent|asap)"
            }
        })
        
        state = {
            "messages": [
                {
                    "role": "user",
                    "content": "This is normal."
                }
            ]
        }
        
        context = {}
        
        assert trigger.evaluate(state, context) == False
    
    def test_execute(self):
        """测试执行功能"""
        trigger = UserInputPatternTrigger("test_user_pattern", {
            "patterns": {
                "urgent": r"(?i)(urgent|asap)"
            }
        })
        
        state = {
            "messages": [
                {
                    "role": "user",
                    "content": "This is urgent!"
                }
            ]
        }
        
        context = {}
        
        result = trigger.execute(state, context)
        
        assert result["message_content"] == "This is urgent!"
        assert "urgent" in result["matched_patterns"]
        assert "executed_at" in result


class TestMemoryMonitoringTrigger:
    """测试内存监控触发器"""
    
    @patch('src.infrastructure.graph.triggers.system_monitoring.psutil')
    def test_evaluate_with_threshold_exceeded(self, mock_psutil):
        """测试超过阈值情况下的评估"""
        # 模拟psutil返回值
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 2 * 1024 * 1024 * 1024  # 2GB
        mock_process.memory_percent.return_value = 50.0
        mock_psutil.Process.return_value = mock_process
        
        mock_memory = Mock()
        mock_memory.used = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.percent = 95.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        trigger = MemoryMonitoringTrigger("test_memory", {
            "memory_threshold_mb": 1024,
            "system_memory_threshold_percent": 90
        })
        
        state = {}
        context = {}
        
        assert trigger.evaluate(state, context) == True
    
    @patch('src.infrastructure.graph.triggers.system_monitoring.psutil')
    def test_evaluate_without_threshold_exceeded(self, mock_psutil):
        """测试未超过阈值情况下的评估"""
        # 模拟psutil返回值
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 500 * 1024 * 1024  # 500MB
        mock_process.memory_percent.return_value = 25.0
        mock_psutil.Process.return_value = mock_process
        
        mock_memory = Mock()
        mock_memory.used = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        trigger = MemoryMonitoringTrigger("test_memory", {
            "memory_threshold_mb": 1024,
            "system_memory_threshold_percent": 90
        })
        
        state = {}
        context = {}
        
        assert trigger.evaluate(state, context) == False


class TestTriggerFactory:
    """测试触发器工厂"""
    
    def test_create_monitoring_trigger(self):
        """测试创建监控触发器"""
        factory = TriggerFactory()
        
        # 测试创建工具执行计时触发器
        trigger = factory.create_monitoring_trigger(
            "test_tool_timing",
            "ToolExecutionTimingTrigger",
            {"timeout_threshold": 30.0}
        )
        
        assert trigger.trigger_id == "test_tool_timing"
        assert trigger._config["timeout_threshold"] == 30.0
    
    def test_create_trigger_from_config(self):
        """测试从配置创建触发器"""
        factory = TriggerFactory()
        
        config = {
            "trigger_id": "test_trigger",
            "trigger_class": "ToolExecutionTimingTrigger",
            "config": {
                "timeout_threshold": 30.0
            }
        }
        
        trigger = factory._create_trigger_from_config(config)
        
        assert trigger.trigger_id == "test_trigger"
        assert trigger._config["timeout_threshold"] == 30.0
    
    def test_list_available_monitoring_triggers(self):
        """测试列出可用的监控触发器"""
        factory = TriggerFactory()
        
        triggers = factory.list_available_monitoring_triggers()
        
        assert "ToolExecutionTimingTrigger" in triggers
        assert "LLMResponseTimingTrigger" in triggers
        assert "MemoryMonitoringTrigger" in triggers
        assert len(triggers) > 0
    
    def test_validate_trigger_config(self):
        """测试验证触发器配置"""
        factory = TriggerFactory()
        
        # 测试有效配置
        valid_config = {
            "trigger_id": "test_trigger",
            "trigger_class": "ToolExecutionTimingTrigger",
            "config": {}
        }
        
        errors = factory.validate_trigger_config(valid_config)
        assert len(errors) == 0
        
        # 测试无效配置
        invalid_config = {
            "trigger_class": "InvalidTriggerClass"
        }
        
        errors = factory.validate_trigger_config(invalid_config)
        assert len(errors) > 0