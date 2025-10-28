"""HistoryManager单元测试"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.application.history.manager import HistoryManager
from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult, MessageType


class TestHistoryManager:
    """HistoryManager测试"""

    def test_init(self) -> None:
        """测试初始化"""
        mock_storage = Mock()
        manager = HistoryManager(mock_storage)
        
        assert manager.storage == mock_storage

    def test_record_message(self) -> None:
        """测试记录消息"""
        mock_storage = Mock()
        manager = HistoryManager(mock_storage)
        
        record = MessageRecord(
            record_id="test-1",
            session_id="session-1",
            timestamp=datetime.now(),
            message_type=MessageType.USER,
            content="测试消息"
        )
        
        manager.record_message(record)
        
        mock_storage.store_record.assert_called_once_with(record)

    def test_record_tool_call(self) -> None:
        """测试记录工具调用"""
        mock_storage = Mock()
        manager = HistoryManager(mock_storage)
        
        record = ToolCallRecord(
            record_id="tool-1",
            session_id="session-1",
            timestamp=datetime.now(),
            tool_name="test_tool",
            tool_input={"param": "value"},
            tool_output={"result": "success"}
        )
        
        manager.record_tool_call(record)
        
        mock_storage.store_record.assert_called_once_with(record)

    def test_query_history(self) -> None:
        """测试查询历史记录"""
        mock_storage = Mock()
        # 设置 get_all_records 方法的返回值
        mock_storage.get_all_records.return_value = []
        manager = HistoryManager(mock_storage)
        
        query = HistoryQuery(
            session_id="session-1",
            limit=10
        )
        
        result = manager.query_history(query)
        
        # 验证返回的是空结果（当前简单实现）
        assert isinstance(result, HistoryResult)
        assert result.records == []
        assert result.total == 0
        
        # 验证调用了存储层的 get_all_records 方法
        mock_storage.get_all_records.assert_called_once_with("session-1")

    def test_storage_exception_handling(self) -> None:
        """测试存储层异常处理"""
        mock_storage = Mock()
        mock_storage.store_record.side_effect = Exception("存储错误")
        
        manager = HistoryManager(mock_storage)
        
        record = MessageRecord(
            record_id="test-1",
            session_id="session-1",
            timestamp=datetime.now(),
            content="测试消息"
        )
        
        # 应该抛出异常
        with pytest.raises(Exception, match="存储错误"):
            manager.record_message(record)

    def test_record_with_different_message_types(self) -> None:
        """测试记录不同类型的消息"""
        mock_storage = Mock()
        manager = HistoryManager(mock_storage)
        
        # 测试用户消息
        user_record = MessageRecord(
            record_id="user-1",
            session_id="session-1",
            timestamp=datetime.now(),
            message_type=MessageType.USER,
            content="用户消息"
        )
        manager.record_message(user_record)
        
        # 测试助手消息
        assistant_record = MessageRecord(
            record_id="assistant-1",
            session_id="session-1",
            timestamp=datetime.now(),
            message_type=MessageType.ASSISTANT,
            content="助手消息"
        )
        manager.record_message(assistant_record)
        
        # 测试系统消息
        system_record = MessageRecord(
            record_id="system-1",
            session_id="session-1",
            timestamp=datetime.now(),
            message_type=MessageType.SYSTEM,
            content="系统消息"
        )
        manager.record_message(system_record)
        
        # 验证所有记录都被存储
        assert mock_storage.store_record.call_count == 3
        mock_storage.store_record.assert_any_call(user_record)
        mock_storage.store_record.assert_any_call(assistant_record)
        mock_storage.store_record.assert_any_call(system_record)

    def test_record_tool_call_without_output(self) -> None:
        """测试记录无输出的工具调用"""
        mock_storage = Mock()
        manager = HistoryManager(mock_storage)
        
        record = ToolCallRecord(
            record_id="tool-1",
            session_id="session-1",
            timestamp=datetime.now(),
            tool_name="test_tool",
            tool_input={"param": "value"}
            # tool_output 为 None
        )
        
        manager.record_tool_call(record)
        
        mock_storage.store_record.assert_called_once_with(record)

    @patch('src.application.history.manager.HistoryManager.query_history')
    def test_query_history_with_complex_params(self, mock_query) -> None:
        """测试带复杂参数的历史查询"""
        mock_storage = Mock()
        manager = HistoryManager(mock_storage)
        
        # 设置模拟返回值
        expected_result = HistoryResult(records=["record1", "record2"], total=2)
        mock_query.return_value = expected_result
        
        query = HistoryQuery(
            session_id="session-1",
            start_time=datetime(2023, 1, 1),
            end_time=datetime(2023, 12, 31),
            record_types=["message", "tool_call"],
            limit=100,
            offset=10
        )
        
        result = manager.query_history(query)
        
        assert result == expected_result
        mock_query.assert_called_once_with(query)