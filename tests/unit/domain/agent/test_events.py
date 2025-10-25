"""Agent事件系统单元测试"""

import pytest
from unittest.mock import Mock, call
from src.domain.agent.events import AgentEventManager, AgentEvent


class TestAgentEventManager:
    """AgentEventManager测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        self.event_manager = AgentEventManager()
    
    def test_subscribe_and_publish_event(self):
        """测试订阅和发布事件"""
        # 创建模拟处理器
        mock_handler = Mock()
        
        # 订阅事件
        self.event_manager.subscribe(AgentEvent.EXECUTION_STARTED, mock_handler)
        
        # 发布事件
        event_data = {"agent_id": "test_agent", "task": "calculate 2+2"}
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, event_data)
        
        # 验证处理器被调用
        mock_handler.assert_called_once_with(event_data)
    
    def test_subscribe_multiple_handlers_for_same_event(self):
        """测试为同一事件订阅多个处理器"""
        # 创建多个模拟处理器
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        
        # 订阅事件
        self.event_manager.subscribe(AgentEvent.EXECUTION_STARTED, mock_handler1)
        self.event_manager.subscribe(AgentEvent.EXECUTION_STARTED, mock_handler2)
        
        # 发布事件
        event_data = {"agent_id": "test_agent", "task": "calculate 2+2"}
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, event_data)
        
        # 验证所有处理器都被调用
        mock_handler1.assert_called_once_with(event_data)
        mock_handler2.assert_called_once_with(event_data)
    
    def test_subscribe_handlers_for_different_events(self):
        """测试为不同事件订阅处理器"""
        # 创建模拟处理器
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        
        # 订阅不同事件
        self.event_manager.subscribe(AgentEvent.EXECUTION_STARTED, mock_handler1)
        self.event_manager.subscribe(AgentEvent.EXECUTION_COMPLETED, mock_handler2)
        
        # 发布第一个事件
        event_data1 = {"agent_id": "test_agent", "task": "calculate 2+2"}
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, event_data1)
        
        # 发布第二个事件
        event_data2 = {"agent_id": "test_agent", "result": "4"}
        self.event_manager.publish(AgentEvent.EXECUTION_COMPLETED, event_data2)
        
        # 验证处理器被正确调用
        mock_handler1.assert_called_once_with(event_data1)
        mock_handler2.assert_called_once_with(event_data2)
    
    def test_publish_event_with_no_subscribers(self):
        """测试发布没有订阅者的事件"""
        # 发布事件（没有订阅者）
        event_data = {"agent_id": "test_agent", "task": "calculate 2+2"}
        
        # 应该不会抛出异常
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, event_data)
    
    def test_agent_event_enum_values(self):
        """测试AgentEvent枚举值"""
        assert AgentEvent.EXECUTION_STARTED.value == "execution_started"
        assert AgentEvent.TOOL_CALL_REQUESTED.value == "tool_call_requested"
        assert AgentEvent.DECISION_MADE.value == "decision_made"
        assert AgentEvent.EXECUTION_COMPLETED.value == "execution_completed"
        assert AgentEvent.ERROR_OCCURRED.value == "error_occurred"
    
    def test_clear_handlers(self):
        """测试清除事件处理器"""
        # 创建模拟处理器
        mock_handler = Mock()
        
        # 订阅事件
        self.event_manager.subscribe(AgentEvent.EXECUTION_STARTED, mock_handler)
        
        # 清除处理器
        self.event_manager.clear_handlers()
        
        # 发布事件
        event_data = {"agent_id": "test_agent", "task": "calculate 2+2"}
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, event_data)
        
        # 验证处理器没有被调用
        mock_handler.assert_not_called()