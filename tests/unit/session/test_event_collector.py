"""事件收集器单元测试"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.session.event_collector import EventCollector, WorkflowEventCollector, IEventCollector, EventType


class TestEventCollector:
    """事件收集器测试类"""

    @pytest.fixture
    def event_collector(self):
        """创建事件收集器实例"""
        return EventCollector()

    def test_init(self, event_collector):
        """测试初始化"""
        assert event_collector._events == {}
        assert event_collector._handlers == {}

    def test_collect_event(self, event_collector):
        """测试收集事件"""
        event_type = EventType.WORKFLOW_START
        data = {"session_id": "test-session", "workflow_name": "test_workflow"}
        
        event_collector.collect_event(event_type, data)
        
        # 验证事件已存储
        assert "test-session" in event_collector._events
        assert len(event_collector._events["test-session"]) == 1
        
        event = event_collector._events["test-session"][0]
        assert event["type"] == event_type.value
        assert event["data"] == data
        assert "id" in event
        assert "timestamp" in event

    def test_collect_event_default_session(self, event_collector):
        """测试收集事件（默认会话ID）"""
        event_type = EventType.INFO
        data = {"message": "测试信息"}
        
        event_collector.collect_event(event_type, data)
        
        # 验证事件已存储到默认会话
        assert "default" in event_collector._events
        assert len(event_collector._events["default"]) == 1

    def test_collect_event_multiple_sessions(self, event_collector):
        """测试收集多个会话的事件"""
        # 收集第一个会话的事件
        event_collector.collect_event(
            EventType.WORKFLOW_START,
            {"session_id": "session1", "workflow_name": "workflow1"}
        )
        
        # 收集第二个会话的事件
        event_collector.collect_event(
            EventType.WORKFLOW_START,
            {"session_id": "session2", "workflow_name": "workflow2"}
        )
        
        # 验证两个会话都有事件
        assert "session1" in event_collector._events
        assert "session2" in event_collector._events
        assert len(event_collector._events["session1"]) == 1
        assert len(event_collector._events["session2"]) == 1

    def test_collect_event_with_handler(self, event_collector):
        """测试收集事件并调用处理器"""
        event_type = EventType.ERROR
        data = {"session_id": "test-session", "error_message": "测试错误"}
        
        # 创建模拟处理器
        handler = Mock()
        event_collector.register_handler(event_type, handler)
        
        event_collector.collect_event(event_type, data)
        
        # 验证处理器被调用
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args["type"] == event_type.value
        assert call_args["data"] == data

    def test_collect_event_with_handler_exception(self, event_collector):
        """测试处理器异常不影响事件收集"""
        event_type = EventType.INFO
        data = {"session_id": "test-session", "message": "测试信息"}
        
        # 创建会抛出异常的处理器
        def failing_handler(event):
            raise Exception("处理器错误")
        
        event_collector.register_handler(event_type, failing_handler)
        
        # 应该不会抛出异常
        event_collector.collect_event(event_type, data)
        
        # 验证事件仍然被收集
        assert "test-session" in event_collector._events
        assert len(event_collector._events["test-session"]) == 1

    def test_get_events(self, event_collector):
        """测试获取事件列表"""
        session_id = "test-session"
        
        # 收集一些事件
        event_collector.collect_event(
            EventType.WORKFLOW_START,
            {"session_id": session_id, "workflow_name": "test_workflow"}
        )
        event_collector.collect_event(
            EventType.NODE_START,
            {"session_id": session_id, "node_name": "test_node"}
        )
        
        events = event_collector.get_events(session_id)
        
        assert len(events) == 2
        assert events[0]["type"] == EventType.WORKFLOW_START.value
        assert events[1]["type"] == EventType.NODE_START.value

    def test_get_events_with_limit(self, event_collector):
        """测试获取限制数量的事件"""
        session_id = "test-session"
        
        # 收集多个事件
        for i in range(5):
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": f"消息 {i}"}
            )
        
        # 获取最后3个事件
        events = event_collector.get_events(session_id, limit=3)
        
        assert len(events) == 3
        assert events[0]["data"]["message"] == "消息 2"
        assert events[1]["data"]["message"] == "消息 3"
        assert events[2]["data"]["message"] == "消息 4"

    def test_get_events_not_exists(self, event_collector):
        """测试获取不存在会话的事件"""
        events = event_collector.get_events("non-existent-session")
        assert events == []

    def test_clear_events(self, event_collector):
        """测试清除事件"""
        session_id = "test-session"
        
        # 收集一些事件
        event_collector.collect_event(
            EventType.INFO,
            {"session_id": session_id, "message": "测试信息"}
        )
        
        # 验证事件存在
        assert len(event_collector.get_events(session_id)) == 1
        
        # 清除事件
        result = event_collector.clear_events(session_id)
        
        assert result is True
        assert len(event_collector.get_events(session_id)) == 0

    def test_clear_events_not_exists(self, event_collector):
        """测试清除不存在会话的事件"""
        result = event_collector.clear_events("non-existent-session")
        assert result is False

    def test_register_handler(self, event_collector):
        """测试注册事件处理器"""
        event_type = EventType.ERROR
        handler = Mock()
        
        event_collector.register_handler(event_type, handler)
        
        assert event_type in event_collector._handlers
        assert handler in event_collector._handlers[event_type]

    def test_register_multiple_handlers(self, event_collector):
        """测试注册多个事件处理器"""
        event_type = EventType.INFO
        handler1 = Mock()
        handler2 = Mock()
        
        event_collector.register_handler(event_type, handler1)
        event_collector.register_handler(event_type, handler2)
        
        assert len(event_collector._handlers[event_type]) == 2
        assert handler1 in event_collector._handlers[event_type]
        assert handler2 in event_collector._handlers[event_type]

    def test_get_events_by_type(self, event_collector):
        """测试按类型获取事件"""
        session_id = "test-session"
        
        # 收集不同类型的事件
        event_collector.collect_event(
            EventType.WORKFLOW_START,
            {"session_id": session_id, "workflow_name": "test_workflow"}
        )
        event_collector.collect_event(
            EventType.NODE_START,
            {"session_id": session_id, "node_name": "test_node"}
        )
        event_collector.collect_event(
            EventType.NODE_END,
            {"session_id": session_id, "node_name": "test_node"}
        )
        
        # 获取节点相关事件
        node_events = event_collector.get_events_by_type(session_id, EventType.NODE_START)
        
        assert len(node_events) == 1
        assert node_events[0]["type"] == EventType.NODE_START.value

    def test_get_events_by_time_range(self, event_collector):
        """测试按时间范围获取事件"""
        session_id = "test-session"
        base_time = datetime.now()
        
        with patch('src.session.event_collector.datetime') as mock_datetime:
            # 模拟不同时间点
            mock_datetime.now.side_effect = [
                base_time,
                base_time + timedelta(minutes=1),
                base_time + timedelta(minutes=2),
                base_time + timedelta(minutes=3)
            ]
            
            # 收集事件
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息1"}
            )
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息2"}
            )
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息3"}
            )
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息4"}
            )
        
        # 获取中间两个事件
        start_time = base_time + timedelta(seconds=30)
        end_time = base_time + timedelta(minutes=2, seconds=30)
        
        filtered_events = event_collector.get_events_by_time_range(
            session_id, start_time, end_time
        )
        
        assert len(filtered_events) == 2
        assert filtered_events[0]["data"]["message"] == "消息2"
        assert filtered_events[1]["data"]["message"] == "消息3"

    def test_get_events_by_time_range_start_only(self, event_collector):
        """测试按开始时间获取事件"""
        session_id = "test-session"
        base_time = datetime.now()
        
        with patch('src.session.event_collector.datetime') as mock_datetime:
            mock_datetime.now.side_effect = [
                base_time,
                base_time + timedelta(minutes=1),
                base_time + timedelta(minutes=2)
            ]
            
            # 收集事件
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息1"}
            )
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息2"}
            )
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息3"}
            )
        
        # 获取从第二个事件开始的所有事件
        start_time = base_time + timedelta(seconds=30)
        
        filtered_events = event_collector.get_events_by_time_range(
            session_id, start_time=start_time
        )
        
        assert len(filtered_events) == 2
        assert filtered_events[0]["data"]["message"] == "消息2"
        assert filtered_events[1]["data"]["message"] == "消息3"

    def test_get_events_by_time_range_end_only(self, event_collector):
        """测试按结束时间获取事件"""
        session_id = "test-session"
        base_time = datetime.now()
        
        with patch('src.session.event_collector.datetime') as mock_datetime:
            mock_datetime.now.side_effect = [
                base_time,
                base_time + timedelta(minutes=1),
                base_time + timedelta(minutes=2)
            ]
            
            # 收集事件
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息1"}
            )
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息2"}
            )
            event_collector.collect_event(
                EventType.INFO,
                {"session_id": session_id, "message": "消息3"}
            )
        
        # 获取到第二个事件为止的所有事件
        end_time = base_time + timedelta(minutes=1, seconds=30)
        
        filtered_events = event_collector.get_events_by_time_range(
            session_id, end_time=end_time
        )
        
        assert len(filtered_events) == 2
        assert filtered_events[0]["data"]["message"] == "消息1"
        assert filtered_events[1]["data"]["message"] == "消息2"

    def test_export_events_json(self, event_collector):
        """测试导出事件为JSON格式"""
        session_id = "test-session"
        
        # 收集一些事件
        event_collector.collect_event(
            EventType.WORKFLOW_START,
            {"session_id": session_id, "workflow_name": "test_workflow"}
        )
        
        json_output = event_collector.export_events(session_id, "json")
        
        # 验证JSON格式
        events = json.loads(json_output)
        assert len(events) == 1
        assert events[0]["type"] == EventType.WORKFLOW_START.value

    def test_export_events_csv(self, event_collector):
        """测试导出事件为CSV格式"""
        session_id = "test-session"
        
        # 收集一些事件
        event_collector.collect_event(
            EventType.WORKFLOW_START,
            {"session_id": session_id, "workflow_name": "test_workflow"}
        )
        
        csv_output = event_collector.export_events(session_id, "csv")
        
        # 验证CSV格式
        lines = csv_output.strip().split("\n")
        assert len(lines) == 2  # 标题行 + 数据行
        assert "ID,Type,Timestamp,Data" in lines[0]
        assert "workflow_start" in lines[1]

    def test_export_events_empty(self, event_collector):
        """测试导出空事件列表"""
        session_id = "empty-session"
        
        json_output = event_collector.export_events(session_id, "json")
        csv_output = event_collector.export_events(session_id, "csv")
        
        # 验证空输出
        assert json.loads(json_output) == []
        assert csv_output == ""

    def test_export_events_unsupported_format(self, event_collector):
        """测试导出不支持的格式"""
        session_id = "test-session"
        
        with pytest.raises(ValueError, match="不支持的导出格式"):
            event_collector.export_events(session_id, "xml")

    def test_generate_event_id(self, event_collector):
        """测试生成事件ID"""
        id1 = event_collector._generate_event_id()
        id2 = event_collector._generate_event_id()
        
        # 验证ID是UUID格式
        assert len(id1) == 36  # UUID长度
        assert len(id2) == 36
        assert id1 != id2  # 每次生成不同的ID


class TestWorkflowEventCollector:
    """工作流事件收集器测试类"""

    @pytest.fixture
    def mock_event_collector(self):
        """创建模拟事件收集器"""
        return Mock(spec=IEventCollector)

    @pytest.fixture
    def workflow_event_collector(self, mock_event_collector):
        """创建工作流事件收集器实例"""
        return WorkflowEventCollector(mock_event_collector, "test-session")

    def test_init(self, mock_event_collector):
        """测试初始化"""
        session_id = "test-session"
        collector = WorkflowEventCollector(mock_event_collector, session_id)
        
        assert collector.event_collector == mock_event_collector
        assert collector.session_id == session_id

    def test_collect_workflow_start(self, workflow_event_collector, mock_event_collector):
        """测试收集工作流开始事件"""
        workflow_name = "test_workflow"
        config = {"param1": "value1"}
        
        workflow_event_collector.collect_workflow_start(workflow_name, config)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.WORKFLOW_START,
            {
                "session_id": "test-session",
                "workflow_name": workflow_name,
                "config": config
            }
        )

    def test_collect_workflow_end(self, workflow_event_collector, mock_event_collector):
        """测试收集工作流结束事件"""
        workflow_name = "test_workflow"
        result = {"output": "test_result"}
        
        workflow_event_collector.collect_workflow_end(workflow_name, result)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.WORKFLOW_END,
            {
                "session_id": "test-session",
                "workflow_name": workflow_name,
                "result": result
            }
        )

    def test_collect_node_start(self, workflow_event_collector, mock_event_collector):
        """测试收集节点开始事件"""
        node_name = "test_node"
        node_type = "test_type"
        config = {"param1": "value1"}
        
        workflow_event_collector.collect_node_start(node_name, node_type, config)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.NODE_START,
            {
                "session_id": "test-session",
                "node_name": node_name,
                "node_type": node_type,
                "config": config
            }
        )

    def test_collect_node_end(self, workflow_event_collector, mock_event_collector):
        """测试收集节点结束事件"""
        node_name = "test_node"
        result = {"output": "node_result"}
        
        workflow_event_collector.collect_node_end(node_name, result)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.NODE_END,
            {
                "session_id": "test-session",
                "node_name": node_name,
                "result": result
            }
        )

    def test_collect_error(self, workflow_event_collector, mock_event_collector):
        """测试收集错误事件"""
        error = ValueError("测试错误")
        context = {"node": "test_node"}
        
        workflow_event_collector.collect_error(error, context)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.ERROR,
            {
                "session_id": "test-session",
                "error_type": "ValueError",
                "error_message": "测试错误",
                "context": context
            }
        )

    def test_collect_tool_call(self, workflow_event_collector, mock_event_collector):
        """测试收集工具调用事件"""
        tool_name = "calculator"
        arguments = {"expression": "1+1"}
        
        workflow_event_collector.collect_tool_call(tool_name, arguments)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.TOOL_CALL,
            {
                "session_id": "test-session",
                "tool_name": tool_name,
                "arguments": arguments
            }
        )

    def test_collect_tool_result(self, workflow_event_collector, mock_event_collector):
        """测试收集工具结果事件"""
        tool_name = "calculator"
        result = 2
        success = True
        
        workflow_event_collector.collect_tool_result(tool_name, result, success)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.TOOL_RESULT,
            {
                "session_id": "test-session",
                "tool_name": tool_name,
                "result": result,
                "success": success
            }
        )

    def test_collect_llm_call(self, workflow_event_collector, mock_event_collector):
        """测试收集LLM调用事件"""
        model = "gpt-4"
        messages = [{"role": "user", "content": "测试"}]
        parameters = {"temperature": 0.7}
        
        workflow_event_collector.collect_llm_call(model, messages, parameters)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.LLM_CALL,
            {
                "session_id": "test-session",
                "model": model,
                "messages": messages,
                "parameters": parameters
            }
        )

    def test_collect_llm_response(self, workflow_event_collector, mock_event_collector):
        """测试收集LLM响应事件"""
        model = "gpt-4"
        response = "测试响应"
        token_usage = {"prompt_tokens": 10, "completion_tokens": 20}
        
        workflow_event_collector.collect_llm_response(model, response, token_usage)
        
        mock_event_collector.collect_event.assert_called_once_with(
            EventType.LLM_RESPONSE,
            {
                "session_id": "test-session",
                "model": model,
                "response": response,
                "token_usage": token_usage
            }
        )


class TestIEventCollector:
    """事件收集器接口测试类"""

    def test_interface_methods(self):
        """测试接口方法定义"""
        # 验证接口定义了所有必需的方法
        assert hasattr(IEventCollector, 'collect_event')
        assert hasattr(IEventCollector, 'get_events')
        assert hasattr(IEventCollector, 'clear_events')
        assert hasattr(IEventCollector, 'register_handler')
        assert hasattr(IEventCollector, 'get_events_by_time_range')
        
        # 验证方法是抽象方法
        assert getattr(IEventCollector.collect_event, '__isabstractmethod__', False)
        assert getattr(IEventCollector.get_events, '__isabstractmethod__', False)
        assert getattr(IEventCollector.clear_events, '__isabstractmethod__', False)
        assert getattr(IEventCollector.register_handler, '__isabstractmethod__', False)
        assert getattr(IEventCollector.get_events_by_time_range, '__isabstractmethod__', False)

    def test_event_type_enum(self):
        """测试事件类型枚举"""
        # 验证所有事件类型都存在
        assert EventType.WORKFLOW_START.value == "workflow_start"
        assert EventType.WORKFLOW_END.value == "workflow_end"
        assert EventType.NODE_START.value == "node_start"
        assert EventType.NODE_END.value == "node_end"
        assert EventType.ERROR.value == "error"
        assert EventType.WARNING.value == "warning"
        assert EventType.INFO.value == "info"
        assert EventType.DEBUG.value == "debug"
        assert EventType.TOOL_CALL.value == "tool_call"
        assert EventType.TOOL_RESULT.value == "tool_result"
        assert EventType.LLM_CALL.value == "llm_call"
        assert EventType.LLM_RESPONSE.value == "llm_response"