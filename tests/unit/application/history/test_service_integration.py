"""HistoryServiceIntegration单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.application.history.service_integration import HistoryServiceIntegration
from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, MessageType, ToolCallRecord, HistoryQuery, HistoryResult
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord


class TestHistoryServiceIntegration:
    """HistoryServiceIntegration测试"""

    def test_init(self) -> None:
        """测试初始化"""
        mock_history_manager = Mock(spec=IHistoryManager)
        
        service = HistoryServiceIntegration(mock_history_manager)
        
        assert service.history_manager == mock_history_manager

    def test_record_session_start(self) -> None:
        """测试记录会话开始"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context = Mock()
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            
            with patch.object(service, '_generate_id', return_value='test-id'):
                with patch('src.application.history.service_integration.datetime') as mock_datetime:
                    mock_now = datetime(2023, 10, 25, 12, 0, 0)
                    mock_datetime.now.return_value = mock_now
                    
                    service.record_session_start("session-1", "workflow-config", "agent-config")
                    
                    # 验证上下文管理器被调用
                    mock_context_manager.assert_called_once_with("session-1")
                    mock_context_manager.return_value.__enter__.assert_called_once()
                    mock_context_manager.return_value.__exit__.assert_called_once()
                    
                    # 验证history_manager.record_message被调用
                    mock_history_manager.record_message.assert_called_once()
                    call_args = mock_history_manager.record_message.call_args[0][0]
                    
                    assert isinstance(call_args, MessageRecord)
                    assert call_args.record_id == 'test-id'
                    assert call_args.session_id == "session-1"
                    assert call_args.timestamp == mock_now
                    assert call_args.message_type == MessageType.SYSTEM
                    assert "会话开始 - 工作流: workflow-config, 代理: agent-config" == call_args.content
                    assert call_args.metadata["workflow_config"] == "workflow-config"
                    assert call_args.metadata["agent_config"] == "agent-config"
                    assert call_args.metadata["event_type"] == "session_start"

    def test_record_session_start_without_agent_config(self) -> None:
        """测试记录会话开始（无代理配置）"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id', return_value='test-id'):
                with patch('src.application.history.service_integration.datetime') as mock_datetime:
                    mock_now = datetime(2023, 10, 25, 12, 0, 0)
                    mock_datetime.now.return_value = mock_now
                    
                    service.record_session_start("session-1", "workflow-config")
                    
                    # 验证history_manager.record_message被调用
                    mock_history_manager.record_message.assert_called_once()
                    call_args = mock_history_manager.record_message.call_args[0][0]
                    
                    assert "会话开始 - 工作流: workflow-config" == call_args.content
                    assert call_args.metadata["agent_config"] is None

    def test_record_session_end(self) -> None:
        """测试记录会话结束"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id', return_value='test-id'):
                with patch('src.application.history.service_integration.datetime') as mock_datetime:
                    mock_now = datetime(2023, 10, 25, 12, 0, 0)
                    mock_datetime.now.return_value = mock_now
                    
                    service.record_session_end("session-1", "user_cancel")
                    
                    # 验证history_manager.record_message被调用
                    mock_history_manager.record_message.assert_called_once()
                    call_args = mock_history_manager.record_message.call_args[0][0]
                    
                    assert isinstance(call_args, MessageRecord)
                    assert call_args.record_id == 'test-id'
                    assert call_args.session_id == "session-1"
                    assert call_args.timestamp == mock_now
                    assert call_args.message_type == MessageType.SYSTEM
                    assert "会话结束 - 原因: user_cancel" == call_args.content
                    assert call_args.metadata["reason"] == "user_cancel"
                    assert call_args.metadata["event_type"] == "session_end"

    def test_record_error(self) -> None:
        """测试记录错误"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        test_error = ValueError("测试错误")
        test_context = {"key": "value"}
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id', return_value='test-id'):
                with patch('src.application.history.service_integration.datetime') as mock_datetime:
                    mock_now = datetime(2023, 10, 25, 12, 0, 0)
                    mock_datetime.now.return_value = mock_now
                    
                    service.record_error("session-1", test_error, test_context)
                    
                    # 验证history_manager.record_message被调用
                    mock_history_manager.record_message.assert_called_once()
                    call_args = mock_history_manager.record_message.call_args[0][0]
                    
                    assert isinstance(call_args, MessageRecord)
                    assert call_args.record_id == 'test-id'
                    assert call_args.session_id == "session-1"
                    assert call_args.timestamp == mock_now
                    assert call_args.message_type == MessageType.SYSTEM
                    assert "错误: 测试错误" == call_args.content
                    assert call_args.metadata["error_type"] == "ValueError"
                    assert call_args.metadata["error_message"] == "测试错误"
                    assert call_args.metadata["context"] == test_context
                    assert call_args.metadata["event_type"] == "error"

    def test_record_error_without_context(self) -> None:
        """测试记录错误（无上下文）"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        test_error = RuntimeError("运行时错误")
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id'):
                with patch('src.application.history.service_integration.datetime'):
                    service.record_error("session-1", test_error)
                    
                    # 验证history_manager.record_message被调用
                    mock_history_manager.record_message.assert_called_once()
                    call_args = mock_history_manager.record_message.call_args[0][0]
                    
                    assert call_args.metadata["context"] == {}

    def test_record_message(self) -> None:
        """测试记录消息"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        test_metadata = {"source": "test"}
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id', return_value='test-id'):
                with patch('src.application.history.service_integration.datetime') as mock_datetime:
                    mock_now = datetime(2023, 10, 25, 12, 0, 0)
                    mock_datetime.now.return_value = mock_now
                    
                    service.record_message("session-1", MessageType.USER, "测试消息", test_metadata)
                    
                    # 验证history_manager.record_message被调用
                    mock_history_manager.record_message.assert_called_once()
                    call_args = mock_history_manager.record_message.call_args[0][0]
                    
                    assert isinstance(call_args, MessageRecord)
                    assert call_args.record_id == 'test-id'
                    assert call_args.session_id == "session-1"
                    assert call_args.timestamp == mock_now
                    assert call_args.message_type == MessageType.USER
                    assert call_args.content == "测试消息"
                    assert call_args.metadata == test_metadata

    def test_record_message_without_metadata(self) -> None:
        """测试记录消息（无元数据）"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id'):
                with patch('src.application.history.service_integration.datetime'):
                    service.record_message("session-1", MessageType.ASSISTANT, "助手回复")
                    
                    # 验证history_manager.record_message被调用
                    mock_history_manager.record_message.assert_called_once()
                    call_args = mock_history_manager.record_message.call_args[0][0]
                    
                    assert call_args.metadata == {}

    def test_record_tool_call(self) -> None:
        """测试记录工具调用"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        tool_input = {"param1": "value1"}
        tool_output = {"result": "success"}
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id', return_value='test-id'):
                with patch('src.application.history.service_integration.datetime') as mock_datetime:
                    mock_now = datetime(2023, 10, 25, 12, 0, 0)
                    mock_datetime.now.return_value = mock_now
                    
                    service.record_tool_call("session-1", "test_tool", tool_input, tool_output)
                    
                    # 验证history_manager.record_tool_call被调用
                    mock_history_manager.record_tool_call.assert_called_once()
                    call_args = mock_history_manager.record_tool_call.call_args[0][0]
                    
                    assert isinstance(call_args, ToolCallRecord)
                    assert call_args.record_id == 'test-id'
                    assert call_args.session_id == "session-1"
                    assert call_args.timestamp == mock_now
                    assert call_args.tool_name == "test_tool"
                    assert call_args.tool_input == tool_input
                    assert call_args.tool_output == tool_output

    def test_record_tool_call_without_output(self) -> None:
        """测试记录工具调用（无输出）"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        tool_input = {"param1": "value1"}
        
        with patch('src.application.history.service_integration.session_context') as mock_context_manager:
            mock_context_manager.return_value.__enter__.return_value = None
            mock_context_manager.return_value.__exit__.return_value = None
            with patch.object(service, '_generate_id'):
                with patch('src.application.history.service_integration.datetime'):
                    service.record_tool_call("session-1", "test_tool", tool_input)
                    
                    # 验证history_manager.record_tool_call被调用
                    mock_history_manager.record_tool_call.assert_called_once()
                    call_args = mock_history_manager.record_tool_call.call_args[0][0]
                    
                    assert call_args.tool_output is None

    def test_get_session_summary(self) -> None:
        """测试获取会话摘要"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        # 模拟查询结果
        mock_message1 = Mock()
        mock_message1.record_type = 'message'
        mock_message1.message_type = MessageType.USER
        
        mock_message2 = Mock()
        mock_message2.record_type = 'message'
        mock_message2.message_type = MessageType.ASSISTANT
        
        mock_tool_call = Mock()
        mock_tool_call.record_type = 'tool_call'
        
        mock_llm_request = Mock()
        mock_llm_request.record_type = 'llm_request'
        mock_llm_request.model = 'gpt-4'
        
        mock_llm_response = Mock()
        mock_llm_response.record_type = 'llm_response'
        
        mock_token_usage = Mock()
        mock_token_usage.record_type = 'token_usage'
        
        mock_cost = Mock()
        mock_cost.record_type = 'cost'
        mock_cost.currency = 'USD'
        
        mock_records = [
            mock_message1, mock_message2, mock_tool_call,
            mock_llm_request, mock_llm_response, mock_token_usage, mock_cost
        ]
        
        mock_result = HistoryResult(records=mock_records, total=7)
        mock_history_manager.query_history.return_value = mock_result
        
        # 模拟统计方法
        mock_history_manager.get_token_statistics.return_value = {
            "total_tokens": 100,
            "prompt_tokens": 60,
            "completion_tokens": 40
        }
        
        mock_history_manager.get_cost_statistics.return_value = {
            "total_cost": 0.01,
            "currency": "USD"
        }
        
        mock_history_manager.get_llm_statistics.return_value = {
            "models_used": ["gpt-4"]
        }
        
        # 设置时间戳
        start_time = datetime(2023, 10, 25, 10, 0, 0)
        end_time = datetime(2023, 10, 25, 11, 0, 0)
        
        for record in mock_records:
            record.timestamp = start_time if record == mock_records[0] else end_time
        
        summary = service.get_session_summary("session-1")
        
        # 验证查询被调用
        mock_history_manager.query_history.assert_called_once()
        query_arg = mock_history_manager.query_history.call_args[0][0]
        assert isinstance(query_arg, HistoryQuery)
        assert query_arg.session_id == "session-1"
        
        # 验证统计方法被调用
        mock_history_manager.get_token_statistics.assert_called_once_with("session-1")
        mock_history_manager.get_cost_statistics.assert_called_once_with("session-1")
        mock_history_manager.get_llm_statistics.assert_called_once_with("session-1")
        
        # 验证摘要内容
        assert summary["session_id"] == "session-1"
        assert summary["total_records"] == 7
        assert summary["message_count"] == 2
        assert summary["user_message_count"] == 1
        assert summary["assistant_message_count"] == 1
        assert summary["system_message_count"] == 0
        assert summary["tool_call_count"] == 1
        assert summary["llm_request_count"] == 1
        assert summary["llm_response_count"] == 1
        assert summary["token_usage_count"] == 1
        assert summary["cost_count"] == 1
        assert summary["start_time"] == start_time
        assert summary["end_time"] == end_time
        assert summary["duration"] == 3600.0  # 1小时

    def test_export_session_data(self) -> None:
        """测试导出会话数据"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        # 模拟get_session_summary返回值
        mock_summary = {
            "session_id": "session-1",
            "total_records": 2
        }
        
        # 模拟记录
        mock_record1 = Mock()
        mock_record1.__dict__ = {
            "record_id": "record-1",
            "session_id": "session-1",
            "content": "测试内容1",
            "message_type": MessageType.USER,
            "timestamp": datetime(2023, 10, 25, 12, 0, 0)
        }
        
        mock_record2 = Mock()
        mock_record2.__dict__ = {
            "record_id": "record-2",
            "session_id": "session-1",
            "tool_name": "test_tool",
            "timestamp": datetime(2023, 10, 25, 12, 1, 0)
        }
        
        mock_result = HistoryResult(records=[mock_record1, mock_record2], total=2)
        
        with patch.object(service, 'get_session_summary', return_value=mock_summary):
            mock_history_manager.query_history.return_value = mock_result
            
            with patch('src.application.history.service_integration.datetime') as mock_datetime:
                mock_now = datetime(2023, 10, 25, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                
                exported_data = service.export_session_data("session-1", "json")
                
                # 验证查询被调用
                mock_history_manager.query_history.assert_called_once()
                
                # 验证导出数据结构
                assert exported_data["summary"] == mock_summary
                assert len(exported_data["records"]) == 2
                assert exported_data["export_format"] == "json"
                assert exported_data["exported_at"] == mock_now.isoformat()
                
                # 验证记录序列化
                records = exported_data["records"]
                assert records[0]["record_id"] == "record-1"
                assert records[0]["message_type"] == MessageType.USER.value
                assert records[0]["timestamp"] == mock_record1.__dict__["timestamp"].isoformat()

    def test_generate_id(self) -> None:
        """测试生成ID"""
        mock_history_manager = Mock(spec=IHistoryManager)
        service = HistoryServiceIntegration(mock_history_manager)
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid"
            
            result = service._generate_id()
            
            assert result == "test-uuid"
            mock_uuid.assert_called_once()