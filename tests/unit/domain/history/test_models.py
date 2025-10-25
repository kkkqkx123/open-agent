"""History模型单元测试"""

import pytest
from datetime import datetime
from src.domain.history.models import (
    MessageType,
    MessageRecord,
    ToolCallRecord,
    HistoryQuery,
    HistoryResult
)


class TestMessageType:
    """MessageType枚举测试"""

    def test_message_type_values(self) -> None:
        """测试消息类型枚举值"""
        assert MessageType.USER.value == "user"
        assert MessageType.ASSISTANT.value == "assistant"
        assert MessageType.SYSTEM.value == "system"


class TestMessageRecord:
    """MessageRecord模型测试"""

    def test_message_record_creation(self) -> None:
        """测试消息记录创建"""
        timestamp = datetime.now()
        record = MessageRecord(
            record_id="test-1",
            session_id="session-1",
            timestamp=timestamp,
            message_type=MessageType.USER,
            content="测试消息"
        )

        assert record.record_id == "test-1"
        assert record.session_id == "session-1"
        assert record.timestamp == timestamp
        assert record.record_type == "message"
        assert record.message_type == MessageType.USER
        assert record.content == "测试消息"
        assert record.metadata == {}

    def test_message_record_with_metadata(self) -> None:
        """测试带元数据的消息记录"""
        metadata = {"source": "test", "priority": "high"}
        record = MessageRecord(
            record_id="test-2",
            session_id="session-2",
            timestamp=datetime.now(),
            metadata=metadata
        )

        assert record.metadata == metadata

    def test_message_record_defaults(self) -> None:
        """测试消息记录默认值"""
        record = MessageRecord(
            record_id="test-3",
            session_id="session-3",
            timestamp=datetime.now()
        )

        assert record.record_type == "message"
        assert record.message_type == MessageType.USER
        assert record.content == ""
        assert record.metadata == {}


class TestToolCallRecord:
    """ToolCallRecord模型测试"""

    def test_tool_call_record_creation(self) -> None:
        """测试工具调用记录创建"""
        timestamp = datetime.now()
        tool_input = {"param1": "value1", "param2": 123}
        tool_output = {"result": "success"}
        record = ToolCallRecord(
            record_id="tool-1",
            session_id="session-1",
            timestamp=timestamp,
            tool_name="test_tool",
            tool_input=tool_input,
            tool_output=tool_output
        )

        assert record.record_id == "tool-1"
        assert record.session_id == "session-1"
        assert record.timestamp == timestamp
        assert record.record_type == "tool_call"
        assert record.tool_name == "test_tool"
        assert record.tool_input == tool_input
        assert record.tool_output == tool_output
        assert record.metadata == {}

    def test_tool_call_record_without_output(self) -> None:
        """测试无输出的工具调用记录"""
        record = ToolCallRecord(
            record_id="tool-2",
            session_id="session-2",
            timestamp=datetime.now(),
            tool_name="test_tool"
        )

        assert record.tool_output is None
        assert record.tool_input == {}
        assert record.metadata == {}

    def test_tool_call_record_with_metadata(self) -> None:
        """测试带元数据的工具调用记录"""
        metadata = {"execution_time": 1.5, "success": True}
        record = ToolCallRecord(
            record_id="tool-3",
            session_id="session-3",
            timestamp=datetime.now(),
            metadata=metadata
        )

        assert record.metadata == metadata


class TestHistoryQuery:
    """HistoryQuery模型测试"""

    def test_history_query_creation(self) -> None:
        """测试历史查询创建"""
        start_time = datetime(2023, 1, 1)
        end_time = datetime(2023, 12, 31)
        query = HistoryQuery(
            session_id="session-1",
            start_time=start_time,
            end_time=end_time,
            record_types=["message", "tool_call"],
            limit=100,
            offset=10
        )

        assert query.session_id == "session-1"
        assert query.start_time == start_time
        assert query.end_time == end_time
        assert query.record_types == ["message", "tool_call"]
        assert query.limit == 100
        assert query.offset == 10

    def test_history_query_defaults(self) -> None:
        """测试历史查询默认值"""
        query = HistoryQuery()

        assert query.session_id is None
        assert query.start_time is None
        assert query.end_time is None
        assert query.record_types is None
        assert query.limit is None
        assert query.offset is None


class TestHistoryResult:
    """HistoryResult模型测试"""

    def test_history_result_creation(self) -> None:
        """测试历史结果创建"""
        records = [
            MessageRecord(
                record_id="msg-1",
                session_id="session-1",
                timestamp=datetime.now(),
                content="消息1"
            ),
            ToolCallRecord(
                record_id="tool-1",
                session_id="session-1",
                timestamp=datetime.now(),
                tool_name="test_tool"
            )
        ]
        
        result = HistoryResult(records=records, total=50)

        assert result.records == records
        assert result.total == 50

    def test_history_result_defaults(self) -> None:
        """测试历史结果默认值"""
        result = HistoryResult(records=[])

        assert result.records == []
        assert result.total == 0