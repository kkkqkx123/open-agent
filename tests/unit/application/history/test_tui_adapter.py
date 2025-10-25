"""TUIHistoryAdapter单元测试"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.application.history.adapters.tui_adapter import TUIHistoryAdapter
from src.domain.history.models import MessageRecord, ToolCallRecord, MessageType
from src.domain.history.interfaces import IHistoryManager


class TestTUIHistoryAdapter:
    """TUIHistoryAdapter测试"""

    def test_init(self) -> None:
        """测试初始化"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        assert adapter.history_manager == mock_history_manager
        assert adapter.state_manager == mock_state_manager

    def test_on_user_message_with_session_id(self) -> None:
        """测试有会话ID时记录用户消息"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid"
            
            with patch('src.application.history.adapters.tui_adapter.datetime') as mock_datetime:
                mock_now = datetime(2023, 10, 25, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                
                adapter.on_user_message("你好")
                
                # 验证调用history_manager
                mock_history_manager.record_message.assert_called_once()
                call_args = mock_history_manager.record_message.call_args[0][0]
                
                assert isinstance(call_args, MessageRecord)
                assert call_args.record_id == "test-uuid"
                assert call_args.session_id == "test-session"
                assert call_args.timestamp == mock_now
                assert call_args.message_type == MessageType.USER
                assert call_args.content == "你好"

    def test_on_user_message_without_session_id(self) -> None:
        """测试无会话ID时不记录用户消息"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = None
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        adapter.on_user_message("你好")
        
        # 验证没有调用history_manager
        mock_history_manager.record_message.assert_not_called()

    def test_on_assistant_message_with_session_id(self) -> None:
        """测试有会话ID时记录助手消息"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid"
            
            with patch('src.application.history.adapters.tui_adapter.datetime') as mock_datetime:
                mock_now = datetime(2023, 10, 25, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                
                adapter.on_assistant_message("你好，我是助手")
                
                # 验证调用history_manager
                mock_history_manager.record_message.assert_called_once()
                call_args = mock_history_manager.record_message.call_args[0][0]
                
                assert isinstance(call_args, MessageRecord)
                assert call_args.record_id == "test-uuid"
                assert call_args.session_id == "test-session"
                assert call_args.timestamp == mock_now
                assert call_args.message_type == MessageType.ASSISTANT
                assert call_args.content == "你好，我是助手"

    def test_on_assistant_message_without_session_id(self) -> None:
        """测试无会话ID时不记录助手消息"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = ""
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        adapter.on_assistant_message("助手回复")
        
        # 验证没有调用history_manager
        mock_history_manager.record_message.assert_not_called()

    def test_on_tool_call_with_session_id(self) -> None:
        """测试有会话ID时记录工具调用"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        tool_input = {"param1": "value1", "param2": 123}
        tool_output = {"result": "success", "data": [1, 2, 3]}
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = "tool-uuid"
            
            with patch('src.application.history.adapters.tui_adapter.datetime') as mock_datetime:
                mock_now = datetime(2023, 10, 25, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                
                adapter.on_tool_call("test_tool", tool_input, tool_output)
                
                # 验证调用history_manager
                mock_history_manager.record_tool_call.assert_called_once()
                call_args = mock_history_manager.record_tool_call.call_args[0][0]
                
                assert isinstance(call_args, ToolCallRecord)
                assert call_args.record_id == "tool-uuid"
                assert call_args.session_id == "test-session"
                assert call_args.timestamp == mock_now
                assert call_args.tool_name == "test_tool"
                assert call_args.tool_input == tool_input
                assert call_args.tool_output == tool_output

    def test_on_tool_call_without_session_id(self) -> None:
        """测试无会话ID时不记录工具调用"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = None
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        adapter.on_tool_call("test_tool", {"param": "value"})
        
        # 验证没有调用history_manager
        mock_history_manager.record_tool_call.assert_not_called()

    def test_on_tool_call_without_output(self) -> None:
        """测试无输出的工具调用记录"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        tool_input = {"param": "value"}
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4'):
            with patch('src.application.history.adapters.tui_adapter.datetime'):
                adapter.on_tool_call("test_tool", tool_input)
                
                # 验证调用history_manager
                mock_history_manager.record_tool_call.assert_called_once()
                call_args = mock_history_manager.record_tool_call.call_args[0][0]
                
                assert isinstance(call_args, ToolCallRecord)
                assert call_args.tool_name == "test_tool"
                assert call_args.tool_input == tool_input
                assert call_args.tool_output is None

    def test_multiple_message_types(self) -> None:
        """测试记录多种类型的消息"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4'):
            with patch('src.application.history.adapters.tui_adapter.datetime'):
                # 记录用户消息
                adapter.on_user_message("用户输入")
                
                # 记录助手消息
                adapter.on_assistant_message("助手回复")
                
                # 记录工具调用
                adapter.on_tool_call("test_tool", {"param": "value"})
                
                # 验证调用次数
                assert mock_history_manager.record_message.call_count == 2
                assert mock_history_manager.record_tool_call.call_count == 1

    def test_empty_content_handling(self) -> None:
        """测试空内容处理"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4'):
            with patch('src.application.history.adapters.tui_adapter.datetime'):
                # 测试空用户消息
                adapter.on_user_message("")
                
                # 测试空助手消息
                adapter.on_assistant_message("")
                
                # 验证仍然记录
                assert mock_history_manager.record_message.call_count == 2
                
                # 验证内容为空字符串
                first_call = mock_history_manager.record_message.call_args_list[0][0][0]
                second_call = mock_history_manager.record_message.call_args_list[1][0][0]
                
                assert first_call.content == ""
                assert second_call.content == ""

    def test_special_characters_in_content(self) -> None:
        """测试内容中的特殊字符"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        special_content = "特殊字符测试: \n\t\"'\\emoji: 🚀"
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4'):
            with patch('src.application.history.adapters.tui_adapter.datetime'):
                adapter.on_user_message(special_content)
                
                # 验证特殊字符被正确保存
                mock_history_manager.record_message.assert_called_once()
                call_args = mock_history_manager.record_message.call_args[0][0]
                assert call_args.content == special_content

    def test_large_tool_input_output(self) -> None:
        """测试大型工具输入输出"""
        mock_history_manager = Mock(spec=IHistoryManager)
        mock_state_manager = Mock()
        mock_state_manager.session_id = "test-session"
        
        adapter = TUIHistoryAdapter(mock_history_manager, mock_state_manager)
        
        # 创建大型输入输出
        large_input = {"data": list(range(1000))}
        large_output = {"result": "success", "items": [{"id": i, "value": f"item-{i}"} for i in range(100)]}
        
        with patch('src.application.history.adapters.tui_adapter.uuid.uuid4'):
            with patch('src.application.history.adapters.tui_adapter.datetime'):
                adapter.on_tool_call("large_tool", large_input, large_output)
                
                # 验证大型数据被正确保存
                mock_history_manager.record_tool_call.assert_called_once()
                call_args = mock_history_manager.record_tool_call.call_args[0][0]
                assert call_args.tool_input == large_input
                assert call_args.tool_output == large_output